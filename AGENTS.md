# Разработка SA

Этот репозиторий — исходник скилла `sa` для Claude Code и Codex. Здесь скилл разрабатывают и проверяют; аудит чужих проектов он выполняет после установки.

## Структура

- `SKILL.md` и `references/` — инструкции скилла. Ядро (`SKILL.md`, `audit`, `remediation`, `orchestration`, `artifacts`, `artifact-formats`, `checks`) не зависит от среды. Механизмы конкретной среды описаны только в `references/platform-claude-code.md` и `references/platform-codex.md`.
- `scripts/` — helper-скрипты на стандартной библиотеке Python 3.9+; `tests/` — их тесты.
- `agents/openai.yaml` — UI-метаданные Codex; в установку для Claude Code не попадает.
- `docs/` — планы, ревью и результаты проверки; в установку не попадает.

## Правила изменений

- Не упоминай в ядре название среды, имя её инструмента или параметр runtime: такие детали принадлежат адаптеру.
- Изменение инструкций проверяется реальными чистыми ролями на синтетическом проекте и наблюдаемыми side effects; поиск фраз в тексте не доказывает workflow. Изменение ядра проверяется в обеих средах. Результаты записываются в `docs/VALIDATION.md` с версией среды, включая неуспешные попытки.
- Временные синтетические проекты и тестовые установки создаются только внутри `.verification/`; каталог исключён из Git.
- Не запускай SA на этом репозитории как на проверяемом проекте.

## Проверки

```bash
python3 -B -m unittest discover -s tests -v
python3 scripts/fingerprint.py --help
python3 scripts/install.py --help
git diff --check
```

Установщик отказывается ставить скилл внутрь собственного исходника, поэтому тестовая установка идёт из копии пакета:

```bash
rsync -a --exclude .git --exclude .verification ./ .verification/pkg/
python3 .verification/pkg/scripts/install.py --platform claude --skills-dir .verification/skills
```

Глобальная установка в `~/.claude/skills` или `~/.agents/skills` выполняется только по явной просьбе пользователя.
