# SIPL Language Toolkit

Проєктна робота з дисципліни «Теорія програмування».

## Набір завдань (10.0 балів)

- `CORE-01` (0.5 б.) - формальна специфікація граматики SIPL та тестові приклади
- `CORE-02` (1.5 б.) - парсер та типізоване AST з позиціями у коді (`SourceSpan`)
- `CORE-03` (2.0 б.) - інтерпретатор SIPL зі станами та контролем нескінченних циклів
- `CORE-04` (1.0 б.) - подійний trace виконання
- `CORE-05` (1.0 б.) - CLI (`parse`, `check`, `run`, `trace`) з JSON-режимом
- `VIS-01` (1.5 б.) - візуалізація дерева синтаксичного виводу (`Text`, `JSON`, `DOT/SVG`)
- `SEM-01` (2.0 б.) - автоматична побудова семантичного терму програми
- `REL-01` (0.5 б.) - GitHub Actions CI

## Структура репозиторію

```text
tp-sipl-project/
|-- .github/workflows/ci.yml           # Автоматичний CI (pytest + покриття >= 80%)
|-- grammar/sipl.lark                  # Формальна LALR(1)-граматика мови SIPL
|-- examples/                          # Еталонні програми SIPL (gcd, power, div)
|-- src/sipl/
|   |-- ast.py                         # Типізоване AST із SourceSpan
|   |-- parser.py                      # CST -> AST трансформер та діагностика помилок
|   |-- cli.py                         # Консольний інтерфейс sipl
|   |-- interpreter/
|   |   |--evaluator.py                # Інтерпретатор із лімітом кроків (max_steps)
|   |   |-- trace.py                   # Запис подій трасування виконання
|   |-- visualization/
|   |   |-- tree_export.py             # Експорт дерева виводу у Text, JSON, DOT та SVG
|   |--semantics/
|       |--term_builder.py             # Побудова композиційного семантичного терму
|-- tests/                             # Модульні та інтеграційні тести
```

## Синтаксис і пріоритети операцій SIPL

Програма має вигляд `begin <stmt> end`. Пріоритет операцій (від найвищого до найнижчого):

1. Дужки `( ... )`
2. Множення `*` (лівоасоціативне)
3. Додавання `+`, віднімання `-` (лівоасоціативні)
4. Відношення порівняння `=`, `>`, `<`, `>=`, `<=`
5. Логічне заперечення `¬`, `!`, `not`
6. Логічна диз'юнкція `\/`, `|`, `or` (лівоасоціативна)
7. Присвоювання `:=`
8. Цикл `while <bexp> do <stmt>`
9. Умовний оператор `if <bexp> then <stmt> else <stmt>`
10. Послідовна композиція `;` (лівоасоціативна)

## Встановлення та запуск тестів

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
pytest --cov=sipl
```

## Приклади команд CLI

```bash
# Перевірка синтаксису та побудова AST
sipl check examples/gcd.sipl
sipl parse examples/gcd.sipl --json

# Виконання програми з початковим станом змінних
sipl run examples/gcd.sipl --var M=48 --var N=18

# Покрокове трасування виконання
sipl trace examples/power.sipl --var X=2 --var Y=5 --json

# Візуалізація дерева синтаксичного виводу
sipl tree examples/div.sipl --format text
sipl tree examples/div.sipl --format dot -o div.dot
sipl tree examples/div.sipl --format svg -o div.svg

# Побудова композиційного семантичного терму
sipl term examples/gcd.sipl
```
