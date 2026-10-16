# Проверка SA

Дата: 10–11 октября 2026. Среда: Windows, Python 3.13.7, codex-cli 0.144.3.

## Основные проверки helper-скриптов

```powershell
python -B -m unittest discover -s tests -v
```

Результат: **18 passed, 1 skipped**, exit 0. Symlink-тест пропущен: этот Windows-сеанс не разрешает создание symlink. Это не считается проверенным поведением на данном хосте.

Тесты проверяют порядок/состав зависимостей, изменение общего service-файла при неизменном handler-е, текущие незакоммиченные bytes, отсутствующие/секретные пути, отказ от существующего файла за границей переданного project root, новую установку, управляемое обновление, запрет перезаписи ручных изменений и неизвестных файлов. Отдельные regression tests подтверждают отказ **до записи** при обоих конфликтах структуры: файл → каталог и каталог → файл.

До реализации helper-скриптов тесты падали из-за их отсутствия. Независимое ревью затем воспроизвело дефект частичного обновления при смене структуры; оба regression tests упали на старой реализации и прошли после preflight-исправления. Ревьюер перепроверил исправление и закрыл замечание. Установщик не обеспечивает полную транзакционность при непредсказуемом I/O-сбое; этот предел отражен в README.

Команды `python scripts/fingerprint.py --help` и `python scripts/install.py --help` завершились с exit 0. CLI fingerprint проверен на локальном синтетическом проекте; он выдал JSON с SHA-256 обработчика и service-зависимости.

На этом ПК Python stdout/locale использует `cp1252`: вывод неэкранированного JSON с кириллическим именем файла падал. Новый CLI regression test сначала воспроизвел `UnicodeEncodeError`, затем прошел после перехода выходного JSON на Unicode escapes. Декодированный путь и алгоритм canonical digest сохранены; строгий ASCII stdout также поддерживается.

## Структура и загрузка скилла

- YAML frontmatter, UI metadata, длина short_description, `$SA` в default_prompt и ссылки SKILL/references проверены.
- Стандартный `skill-creator/scripts/quick_validate.py` на **реальном** SKILL.md завершился с exit 1: он требует lowercase и отклоняет имя `SA`. Это сознательное отклонение от правила имени по требованию точного вызова `$SA`; стандартный валидатор не объявляется прошедшим.
- Остальные правила того же валидатора проверены на временной копии с единственной заменой `name: SA` → `name: sa`; эта структурная проверка прошла. Рабочий скилл не переименован.
- После глобальной установки настоящий `codex app-server` через `skills/list` с forceReload вернул одну запись: `name=SA`, `scope=user`, `enabled=true`, путь `~/.agents/skills/SA/SKILL.md`, без ошибок загрузки. После обновления установки проверка повторилась с тем же результатом. Новая модельная сессия для этой проверки не запускалась.

Временные файлы проверки и synthetic audit artifacts находятся в `.verification/`, исключенной из Git. В глобальную установку не попадают README, docs, tests или fixtures.

## Независимая проверка workflow

На изолированном Python adapter-проекте с синтетическими данными проведен полный SA реальными сабагентами с `fork_turns="none"`. Исходный Endpoints.md намеренно имел пропуск и неверную ссылку. Свежий inventory agent обнаружил пропущенный `/health`, исправил ссылку на `/me` и подтвердил 3 endpoint.

Первый запуск: **3/3 audited и независимо accepted**, 36 строк покрытия категорий. Агенты приняли одну задачу IDOR уровня medium, 0 critical/high/low. Для каждого endpoint использованы разные новые аудиторы и ревьюеры. Аудитор и ревьюер самостоятельно воспроизвели cross-owner выдачу документа. Исходники приложения не изменены, задача сохранена отдельно. Проверка окончательного инвентаря, fingerprint, матриц и ревью завершилась с exit 0. Ошибки первоначальных вспомогательных discovery/Markdown-команд зафиксированы отдельно; после исправления проверок повторные сигналы прошли.

При оценке этого результата обнаружилась неоднозначность fixture: приватная политика была подразумеваема полем owner, но не записана явно. Воспроизведение доказывало выдачу чужого документа, а не само нарушение политики. Первую принятую задачу нельзя считать окончательно доказанной IDOR только на этом основании. Стандарт checks.md усилен: подтверждать нарушенный контракт доступа, а не выводить его из имени поля. Отдельные сценарии с явной приватной и общей политикой проверяют этот критерий.

Второй запуск при неизменных исходниках: **3/3 reused с новыми accepted ревью**. Снова выполнена свежая независимая проверка инвентаря. Между двумя запусками использованы 14 разных чистых агентов, включая inventory-фазы. Финальный signal подтвердил те же snapshots, 36 категорий, историю и отдельные audit/review IDs, exit 0. Вспомогательная Markdown-проверка сначала ошибочно требовала один вариант форматирования `reused`; после исправления проверки повтор прошел. Историческое ограничение access contract первой задачи сохранено.

Перед третьим запуском контролируемо изменены services.py и README: приватное owner-only правило теперь задано явно. App.py остался byte-identical; отдельный snapshot signal подтвердил изменение полной closure, exit 0. Результат третьего полного запуска: **3/3 audited/accepted, reused 0**, 36 категорий, **1 confirmed medium IDOR** по явному контракту и проверенной code-chain. Новые аудиторы и reviewer-ы независимо отказались от старой версии; финальный gate маршрутов, snapshots, категорий, трех ревью, задачи и ссылок прошел с exit 0. Старая история не переписана, новый архив проверен на точное соответствие.

Наблюдение прогона: некоторые агенты повторяли одинаковые успешные локальные вызовы десятки раз. Инструкции checks.md уточнены: использовать достаточный сигнал для конкретного риска, повторять только при обоснованном replay/race-сценарии или другом новом основании. Это ограничивает лишнюю работу, сохраняя все обязательные категории и независимость фаз.

Независимый package reviewer перепроверил Unicode fix, CLI regression и оба уточнения checks.md; существенных дефектов не обнаружил. Его отдельная проверка ASCII stdout и обратного чтения Unicode JSON прошла с exit 0.

Один первоначальный dispatch повторного package-review был отклонен из-за занятого слота. После явного резервирования слота с forward-координатором review состоялся. Первый dispatch не считается успешным; в endpoint workflow учитывались все активные родители и не более двух дочерних фаз одновременно.

Отдельный fixture с явно общими документами прошел полный запуск с нуля: свежая независимая инвентаризация, новый аудитор и отдельный новый reviewer. Результат: **1/1 audited/accepted**, 12 категорий, **0 задач**. Оба endpoint-агента независимо проверили сырой код и контракт, локально подтвердили разрешенное cross-author чтение (200) и запрет anonymous (401), exit 0. Финальная сверка маршрутов, snapshot, категорий и review прошла с exit 0. Owner marker не привел к ложной IDOR-задаче.

В новых сценариях также были исправлены вспомогательные ошибки: слишком широкий поиск AGENTS за пределами fixture дал exit 1 на недоступном чужом каталоге, а JS-обертки public gate и health review дали SyntaxError до выполнения соответствующих команд (числового exit code нет). Целевая проверка AGENTS и фактические команды после исправления завершились с exit 0; эти ошибки раскрыты в behavior/review artifacts и не выдаются за успешные первоначальные сигналы.

Также зафиксированы неуспешные диагностические чтения отсутствующего AGENTS/HEAD в unborn репозитории и отклоненные первые попытки записи артефактов. Отсутствие HEAD обозначено как условие, запись исправлена без потери данных; эти действия не объявляются passed validation. Всего четыре сценарных запуска использовали **24 разных чистых агента** (inventory, audit и review); primary и заключительные secondary signals прошли, все требуемые ревью приняты.

## Ограничения проверки

Двухчасовой таймер не проверялся двухчасовым ожиданием. Автономная доставка при закрытом приложении не заявляется: для нее нужен доступный thread-heartbeat. Goal принадлежал родительской задаче создания скилла; сценарные сабагенты не создавали и не закрывали его. Полный аудит реального приложения и production-проверки в этой задаче не выполняются.

Fingerprint детерминирован только для переданного списка и не определяет dependency closure. Релевантные внешние политики и настройки требуют отдельного доказательства актуальности. Статический анализ и независимое ревью не гарантируют обнаружение всех возможных уязвимостей.

## Модернизация audit / fix / full

Источник проверки — согласованный [план](SA-MODERNIZATION-PLAN.md), текущий пакет и отдельные синтетические проекты внутри `.verification/modernization/`. Исходники и данные реального приложения не проверяются. Старые результаты выше относятся к прежнему аудиторскому workflow и не подтверждают новую remediation-механику.

Первичный RED воспроизведён на двух приватных эндпоинтах с явным owner-only контрактом: обе проверки cross-owner ожидали 403, получили 200, `python -B -m unittest -v` завершился с exit 1. Чистый baseline-agent работал с сохранённым прежним пакетом: старый SA не имел режима исправления и запрещал patch приложения. Он выполнил только начальную инвентаризацию/checkpoint; независимость новых четырёх фаз этот baseline не доказывает. Оригинальные источники UTF-16 и JSON сохранились.

Технические проверки нового пакета:

- `python -B -m unittest discover -s tests -v`: 18 passed, 1 skipped, exit 0. Symlink остаётся непроверенным на этом хосте; scripts не менялись.
- Обе команды helper `--help` и `git diff --check`: exit 0.
- 28 локальных ссылок, строгий UTF-8 исходников, fences, frontmatter/UI metadata проверены; пакет содержит 10 файлов.
- Реальная новая установка и управляемое обновление прежнего пакета включили все новые references. Bytes пакетов совпали; README/docs/tests/fixtures не попали в установку. Все тестовые установки внутри проекта.
- Настоящий `codex app-server` / `skills/list` с forceReload обнаружил обновлённый `SA`, scope=repo, enabled=true, без ошибок. Старый глобальный SA отдельно присутствует как scope=user; новая repo-запись проверена по точному пути и новой description.
- Первые два вызова quick_validate без `-X utf8` упали на cp1252-декодировании кириллицы. Повтор с `-X utf8` на реальном пакете дал exit 1 по сознательно сохранённому uppercase имени SA. Та же структурная проверка на временной копии с единственной заменой имени на sa дала exit 0. Рабочий пакет не переименован.

Проверки чтения и сохранения форматов выполнены доступными bundled runtime, без новых зависимостей. Это roundtrip probes обработчиков, не дополнительные независимые security reviews; статусы/оценки в этих документах явно помечены PROBE ONLY:

| Источник | Фактический результат | Ограничение |
| --- | --- | --- |
| Неизвестное расширение, cp1251 и смешанные окончания строк | Строгое чтение и запись результата; исходный byte-префикс сохранён | Правильная кодировка дана контрактом fixture; произвольное угадывание encoding не проверено |
| ZIP с неизвестным расширением | Member обновлён; остальные bytes, список и archive comment сохранены; testzip успешен | Вложенные и зашифрованные контейнеры не проверены |
| PDF | Новый результат в том же PDF; прежний текст/metadata и pixels страницы совпали; обе страницы просмотрены | Poppler сообщил отсутствие display fonts Symbol/ArialUnicode; это диагностированный предел первого render signal, не безошибочный renderer check |
| Сканированный PDF без text layer | Полная страница прочитана визуально; probe-result добавлен в тот же PDF. Исходные image/content streams и rendered PNG byte-identical, metadata сохранены, saved readback и оба render проверены, exit 0 | Один synthetic scan; шумный OCR и запись результата в standalone raster-файл не проверены. Встроенный Arial дал render без stderr |
| XLSX | Export/import/edit/reopen; исходные значения, стили, annotation и SUM-формула сохранены, cached result=5; оба render просмотрены | Native Excel engine не проверен |
| DOCX | Native OOXML result block; остальные ZIP members byte-identical, прежний XML вне добавления совпадает, header/table сохранены | Визуальная проверка blocked: packaged render_docx требует отсутствующий soffice.exe; обычные пути LibreOffice также отсутствуют |
| Повреждённый PDF | Реальный PdfStreamError, исходник сохранён, статус blocked | Не выдаётся за no_recorded_findings |
| PDF с недоступным паролем | Реальный FileNotDecryptedError; полный read/write blocked, source bytes неизменны, score — | Пароль синтетически сгенерирован, не сохранён и не выводился; расшифровка не заявляется |

Первый XLSX scope check дал AssertionError из-за сравнения StyleProxy-обёрток: параметры стилей совпадали, но сравнение обёрток не сравнивало значения. Проверка исправлена на сравнение копий реальных style objects и повторно прошла с exit 0. Это исправление checker-а, не скрытая правка исходного workbook. Полнота чтения/записи всех возможных подтипов не заявляется: skill ищет применимый способ для каждого фактического файла без allowlist, а недостающий decoder/writer/пароль/QA оставляет конкретным blocker.

Первое создание защищённого fixture завершилось с exit 1: `pypdf.clone_document_from_reader` сохранил представление ReportLab ID, на котором native encrypt дал TypeError. Исходный защищённый файл ещё не был создан. Первая версия helper и failure сохранены; подготовка исправлена на новый PDF writer с добавлением страницы/синтетической metadata. Повторная проверка получила настоящий FileNotDecryptedError на чтении, сохранила blocked и неизменные bytes; checker завершился с exit 0. Этот ожидаемый read failure не объявляется успешным чтением документа.

Decision/evidence probes проверили 29 локальных случаев; 11/11 групп сверки сохранённых артефактов завершились с exit 0. Это действия отдельного чистого probe-агента на supplied synthetic artifacts, а не замена actual независимых ролей:

- Один сохранённый вопрос для bare `$SA`; отсутствие patch/навязанного режима. Explicit режимы, natural fix и resume не вызвали повторного вопроса.
- Реальная миграция schema1 array/object сохранила audit-поля, неизвестные nested fields и исходную копию. Unknown/corrupt/conflicting schema не перезаписана.
- Частичная синхронизация дописала task/State; второй проход сделал ноль записей, история не продублирована. Late attempt и неизвестный writer не получили полномочий.
- Изменения finding/плана/shared service сделали решение stale при unchanged handler. Доказанный собственный служебный append не инвалидировал план.
- Управляемые завершённые events сохранили counters через resume; три без продвижения потребовали переоценку, пять продуктивных не получили общего потолка. Самостоятельные planner/reviewer для переоценки здесь не запускались.
- Score7 дал eligibility при actual passed checks и явно supplied accepted input; score10 при фактической failed обязательной проверке — нет.
- Часовой trigger/resume проверены controlled time, без ожидания часа и automation. Арифметическая ETA-модель учитывала serial dependency; реальный ETA настоящих фаз не выдавался за измеренный.
- Полное чтение unknown-extension источника без findings, пустой реестр и повреждённый JSON дали разные сохранённые registry/results и четырёхколоночные таблицы.
- Реальные added/removed manifests вызвали helper только на существующей безопасной части; отсутствующие paths не передавались, stubs не создавались. Эксклюзивная Windows-блокировка файла дала actual PermissionError и blocker, а не absent. Сохранённый альтернативный маршрут продолжал нарушать контракт после удаления старого: issue остался confirmed/partial.

Initial integrity check дал exit 1 из-за одновременной документарной правки root статуса плана. Точный before/after diff и обе версии сохранены; обратная проверка delta восстановила начальный SHA, раздел 11 byte-identical. После явной актуализации input version повторная проверка дала exit 0; первоначальный failure сохранён. Преднамеренные failed migration/parse/locked-read сигналы также сохранены и не объявлены passed.

Эти probes не подтверждают live UI-вызов bare SA, реальный restart/late-result delivery, конкурентные писатели, независимую переоценку трёх попыток, четыре productive full waves, scheduler/heartbeat delivery либо production rollout. Чтение DOCX/PDF/XLSX и других форматов не даёт гарантий сохранения произвольного подтипа: standalone raster-сканы, старые DOC/XLS, защищённые документы и все возможные containers в этой задаче целиком не проверены.

### Реальный fix и независимое сценарное ревью

На двух приватных synthetic local adapter routes выполнен `$SA fix`: **2/2 источника, 1 canonical issue resolved, 0 остатка и blockers**. Для каждого источника последовательно запущены отдельные planner, plan reviewer, implementer и code reviewer. Независимый reviewer модернизации проверил восемь настоящих runtime spawn calls и соответствующих возвращённых ID: все различны, у каждого `fork_turns="none"`, model/effort override отсутствует. Это подтверждение фактического dispatch, а не восемь имитированных строк State.

Общий owner guard внесён один раз в `services.py`; первый исполнитель сохранил исходный regression oracle и добавил три существенных проверки. Второй исполнитель подтвердил применимость того же кода с нулевым дополнительным code/test diff. Оба code reviewers самостоятельно воспроизвели baseline RED (exit 1, security failures, 0 runtime errors), выполнили свои narrow GREEN и общий suite (exit 0, 2 tests / 14 outcomes), а также по восемь principal boundary checks (exit 0). Независимое ревью модернизации повторило baseline/current suites и через purpose-built thread API сверило реальные commandExecution обоих reviewers.

| Синтетический источник | Эндпоинт | Результат независимого code review | Оценка |
| --- | --- | --- | --- |
| documents.md, UTF-16 LE | GET /documents/{id} | shared-idor resolved локально, accepted; same-source запись verified | 9 |
| preview.json, UTF-8 | GET /preview/{id} | shared-idor resolved локально, accepted; тот же общий patch, own applicability review | 9 |

Исходные 494 bytes documents сохранены точным prefix, BOM FFFE и CRLF — без изменений. Для JSON удаление двух разрешённых вставок из сохранённого результата восстановило все 253 исходных bytes; поля, порядок и manual metadata сохранены. Нативные source writes, восемь фазовых артефактов, plan/prerequisite digests, конечная code closure, leases, Task, State, таблицы и четыре review links независимо проверены. Preterminal State ещё содержал canonical confirmed при двух completed accepted Code Reviews; task стал resolved только после координаторской синхронизации. Все итоговые проверки — exit 0. Stage 1 независимого сценарного ревью: **accepted**, blocking findings нет; на stage 1 full ещё не был принят.

Настоящая часовая сводка отправлена при 3704.4 active seconds с сохранением marker; порог 3600 задержался на генерацию terminal helper. Это одиночная observed delivery в активном сеансе, не проверка длительной cadence/фонового heartbeat. Надёжная ETA для остатка финализации отсутствовала.

Первоначальные failures сохранены: неверные discovery/reference paths, metadata/preflight exit 1, cp1252 stdout UnicodeEncodeError, truncated-output JSON parse, Windows launch OSError 206 и неудачный compile check extracted runner. Короткий исправленный launcher выполнил writer с exit 0; приложение при этих tooling failures не переписывалось. Временный fixture finalizer преждевременно поставил State complete до Summary: прежний checkpoint сохранён, running восстановлен. Первые Summary/report имели неверную базу relative review links; отдельный check дал exit 1, прежние документы сохранены, ссылки исправлены и повторная проверка дала exit 0. Окончательный complete записан после сохранения и проверки обеих сводок. Независимый reviewer подтвердил эти recoveries; действующие source-инструкции уже требовали согласованную связку и Summary, нового пробела контракта на этом trigger не обнаружено. Его начальные вспомогательные checks дали exit 1 из-за cp1252 stdout и ошибочных предположений о non-null snapshot agent_id, заполненных preterminal local_results, raw hash без newline и plaintext runtime message. Фактическая ранняя запись имеет null с причиной, State/attempt и raw dispatch связывают её с агентом; исходная строка включает newline, message зашифровано. После чтения реальных shapes проверки связей прошли с exit 0 без изменения fixtures/source.

Сценарий ограничен synthetic trusted-principal adapter. Реальный HTTP/session/production rollout, миграция, остальные форматы, независимый no-progress reassessment и live restart/late delivery этим fix не проверены. Git и глобальная установленная копия не менялись сценарными агентами. Полные локальные evidence сохранены внутри игнорируемой `.verification/modernization/`; приватные runtime logs в пакет и Git не включены.

### Реальный full: аудит и исправление

Отдельный synthetic local adapter содержит один приватный `GET /documents/{id}`. Новый inventory-agent принял полный инвентарь 1/1; новые auditor и audit reviewer самостоятельно воспроизвели baseline RED и приняли 12 категорий: 5 checked, 7 not_applicable, 0 blocked, одна confirmed medium shared-idor. Контракт owner-only явно задан README. Исторические source/Task сохранились; принятый текущий аудит добавлен в исходный UTF-16 документ append-only, без подмены seed новой confirmed записью до независимого подтверждения.

Затем отдельно запущены четыре свежие remediation-роли. План и его независимое ревью приняты на точных версиях. Исполнитель изменил только services.py и test_access.py: 59-byte generic owner guard в слое причины и девять differentiated policy checks. На одном и том же новом suite до патча получены exit 1 / 4 security failures, после — exit 0 / 2 test methods / 9 outcomes. Fresh code reviewer независимо повторил baseline RED и current GREEN, принял локальный resolved с оценкой 9. Влияющая closure изменилась с a664b8ecd291a98240b7a454726a8cc6e462473d1024c2d829b44462d664853c на a625a248e8d13cbd4285c9a1515621667688913fcc53fb08adcc4c8791ffb15f; README/app bytes сохранились.

Code reviewer нативно записал verdict/status/score/history в тот же documents.md. Полный прежний 2140-byte prefix, включая исходные 494 bytes, сохранён; добавлены только 4446 bytes результата. UTF-16 LE, один BOM FFFE и CRLF сохранены, native candidate и saved-file readback verified. Старый audit после патча стал stale, его профиль и доказательства сохранены в истории.

Завершающий auditor и отдельный завершающий reviewer запущены заново на конечной closure. Auditor сам получил current GREEN, проверил все 12 категорий и не нашёл текущих замечаний. Final reviewer принял полный raw code/access/sink chain, самостоятельно сверил AST/bytes/manifests и актуальность свидетельств; свой повторный runtime suite он не запускал. Эти роли не переиспользовали начальные решения. Итог full: **1/1 current audit accepted, 1 canonical issue resolved, 0 остатка и blockers**, оценка исправления 9 от независимого code reviewer.

После принятого финального review координатор добавил в тот же UTF-16 источник результат итогового аудита: прежние 6586 bytes сохранены точно, добавлены 3910 bytes; итог 10496 bytes, один FFFE BOM и 43 CRLF. Saved readback, история, Task, Endpoints, обе Summary и State согласованы. Итоговая сверка 50 accepted inputs, 13 snapshots и 49 ссылок завершилась exit 0; все девять leases released, State complete записан после проверенных итоговых сводок и отчёта.

Фактический runtime dispatch содержит **9 различных свежих ролей**, у всех `fork_turns="none"`, без model/effort override; API отдельно подтвердил девять started и девять completed событий. Вместе с fix это 17 actual fresh roles. Отфильтрованная metadata, snapshots и полный full-run-report сохранены в игнорируемой `.verification/modernization/`, без raw сообщений/reasoning из runtime logs. Итоговое независимое сценарное ревью модернизации (stage 2): **accepted, blocking findings 0**. Локальный отчёт: `.verification/modernization/final-scenario-review.md`; reviewer разрешил эту замену pending на фактический verdict без повторного review, при сохранении границ и ограничений проверки.

| Синтетический источник | Эндпоинт | Замечание и текущий результат | Оценка |
| --- | --- | --- | --- |
| documents.md, UTF-16 LE | GET /documents/{id} | shared-idor resolved локально; code review accepted; fresh final audit/review accepted | 9 |

Время full включает ожидание доступных agent slots. Часовые markers сохранены при 3613.309 и 7396.849 active seconds; второй trigger задержан на 183.540 seconds. Root независимо отправил пользователю вторую сводку примерно в 10:41:59 UTC, а marker координатора записан в 10:43:43.316916 UTC: более ранняя доставка координатора не заявляется. Это observed active-session delivery с раскрытой задержкой, не доказательство точного расписания либо фонового heartbeat.

Неуспешные tooling checks сохранены: неверные scoped relative reads, cp1252 stdout, диагностические Python/JS parse errors, artifact writer до создания его owned directory, UTF-8 чтение UTF-16, literal_eval на AST Name, ошибочное ожидание четырёх entries в общем snapshot, пропущенный baseline locator и слишком длинный Windows command (OSError 206 до запуска). Исправленные проверки дали exit 0; PowerShell aggregate exit 0 не выдан за успешное ошибочное чтение. App/test не переписывались при failed artifact writes. Эти ошибки не смешаны с намеренным security RED.

Full проверен на одном synthetic trusted-principal adapter с явно заданной private policy. Настоящие HTTP/session identity/auth provider/DB/gateway/network/deployment не проверены. Независимая no-progress переоценка, несколько productive waves, restart/late-result delivery и конкурентные writers здесь не запускались. Отдельные bounded probes выше не превращаются в полное live покрытие всех сценариев плана; code acceptance и local resolved не утверждают production rollout.

### Обновление глобальной копии

После принятого независимого ревью и публикации исходного пакета пользователь отдельно разрешил обновить `C:\Users\georg\.agents\skills\SA`. Команда `python -B -X utf8 scripts/install.py --skills-dir 'C:\Users\georg\.agents\skills' --update` завершилась exit 0. Штатная проверка managed installation сохранила защиту от перезаписи ручных изменений; force не применялся.

Read-only сверка подтвердила byte equality всех 10 установленных файлов с принятым исходным пакетом, совпадение `.sa-install.json` и отсутствие посторонних файлов, exit 0. Настоящий `codex app-server --stdio` / `skills/list` с forceReload для текущего проекта обнаружил ровно нужный `C:\Users\georg\.agents\skills\SA\SKILL.md`, scope=user, enabled=true, новую description, errors=[]; check exit 0. Локальные результаты: `.verification/modernization/global-package-results.json` и `global-discovery-results.json`. Это проверка установленного пакета и discovery metadata; новый security workflow после установки не запускался. Исходный пакет остался неизменным, поэтому принятые сценарные сигналы сохраняют применимость.

## Адаптация для Claude Code: технические проверки

Дата: 15 октября 2026. Среда: macOS (APFS, без различения регистра), Python 3.9.6 (`/usr/bin/python3`; команды `python` нет), Claude Code 2.1.295 из desktop-приложения. Основание изменений — [план адаптации](CLAUDE-CODE-ADAPTATION-PLAN.md).

До изменений: `python3 -B -m unittest discover -s tests -v` — 19 passed, 0 skipped, exit 0. Symlink-тест, пропущенный на Windows, на этом хосте выполнен и прошёл.

После изменений:

- Тесты: 24 passed, 1 skipped, exit 0. Пропущен новый тест дублей `SA`/`sa`: на APFS такие каталоги создать нельзя, поведение на файловой системе с различением регистра не проверено. Новые тесты: `agents/` только для Codex, отказ обновлять установку другой платформы, миграция управляемой `SA` без поля `platform` в `sa` с обновлением файлов, отказ для неизвестной платформы.
- `install.py --help` и запуск без `--platform` (argparse, exit 2) проверены; `git diff --check` — exit 0.
- 44 локальные ссылки в `SKILL.md`, README, `AGENTS.md` и references существуют; все Markdown-файлы пакета строго декодируются как UTF-8. Frontmatter: `name`, `description`, `argument-hint`, `disable-model-invocation: true` (D6). Что Codex принимает `argument-hint` и `disable-model-invocation` без ошибок загрузки, не проверено. Frontmatter разобран настоящим YAML-парсером (Ruby Psych 2.6): `disable-model-invocation` — boolean `true`. Первая редакция description с фразой «Запуск: /sa» содержала двоеточие с пробелом; контрольная строка такого вида даёт `Psych::SyntaxError`, а Claude Code при ошибке разбора загружает скилл с пустыми метаданными. Фраза переписана без двоеточия до проверки.
- Установка из копии пакета в `.verification/`: для `claude` — 11 файлов без `agents/`, для `codex` — 12 файлов с `agents/openai.yaml`; повторный `--update` — exit 0; `--update` с `--platform claude` поверх Codex-установки — exit 1 без изменений. Первая попытка установить прямо из репозитория в `.verification/` получила штатный отказ «Source and installed skill must not overlap»: установщик не ставит скилл внутрь собственного исходника. Рецепт в `AGENTS.md` исправлен на установку из копии.
- `claude plugin validate --strict` по каталогу `.claude/skills` с установленным `sa` вернул success с пустым `contents`. Контрольный скилл с повреждённым YAML дал тот же результат, поэтому эта проверка обнаружение и разбор скилла не подтверждает и не засчитывается.

Не проверено: обнаружение `/sa` в реальной сессии Claude Code, любой запуск ролей, часовые сводки, продолжение после компакции и рестарта, регрессия Codex-стороны после изменения ядра (discovery и один audit). Глобальная установка в `~/.claude/skills` не выполнялась.

## Адаптация для Claude Code: этап 7, проверка в среде

Дата: 15 октября 2026. Среда: macOS 27.0.1 (APFS), Claude desktop 2.37337.1, Code tab (`CLAUDE_CODE_ENTRYPOINT=claude-desktop`, Agent SDK 0.3.295), встроенный Claude Code 2.1.295, Python 3.9.6 (`python3`), Codex CLI 0.162.0-alpha.17.2 из `ChatGPT.app`. Пакет — незакоммиченное рабочее дерево. Прогоны 0, A, B и C шли на установленной версии с исправленными дефектами 1–4; правки 6–7 внесены в исходник позже; 16 октября они установлены во все копии вместе с правками 8–11. Основание — этап 7 [плана адаптации](CLAUDE-CODE-ADAPTATION-PLAN.md).

Выполнены прогоны 0, A (audit, затем по просьбе пользователя fix и повторный audit), B, C, E, F, проба 2 и модельный аудит в Codex. В прогоне D на вопрос bare `/sa` пользователь выбрал `full`, поэтому D стал вторым прогоном full; отказ в запросе разрешения и `/compact` в нём не выполнялись. Прогоны 0–C, включая fix в A, шли на Claude Code 2.1.295; ночью приложение обновило его до 2.1.299, на нём шли продолжение повторного аудита A, проба 2, E и F. Прогоны запускаются из сессии проверки (см. «Прогоны в фикстурах»); шаги для ручного запуска — `.verification/claude-code/STEPS.md`.

### Подготовка

- Шесть фикстур в `.verification/claude-code/fixtures/`, каждая — отдельный git-репозиторий с синтетическими данными и тестами `python3 -B -m unittest discover -s tests` (exit 0): `fx-audit` (три эндпоинта, явный owner-only контракт в README, общий IDOR в `services.load_document` на двух из них, третий исправен), `fx-fix` (те же маршруты; ручные Endpoint Reviews в UTF-16 LE с BOM и CRLF, windows-1251 и UTF-8 со смешанными CRLF/LF; два описывают общий дефект, третий — отдельный дефект в `notes.py`; `CLAUDE.md` и `AGENTS.md` с правилом, видимым только из `AGENTS.md`), `fx-full`, `fx-restart`, `fx-probe` (один эндпоинт), `fx-config` (`.claude/agents/general-purpose.md` и PreToolUse-hook в `.claude/settings.json`, который логирует только метаданные вызова). Генератор: `.verification/claude-code/tools/make_fixtures.py`; исходные bytes и SHA-256 — `baseline.json` и `baseline-sources/`.
- Установка в каждую фикстуру — `install.py --platform claude --skills-dir <fixture>/.claude/skills` из копии пакета: 11 файлов пакета и manifest. Независимая проверка доступа до прогонов (`tools/check_fix_effect.py`): в `fx-fix` чужой документ, превью и заметка отдаются с 200; в `fx-audit` документ и превью — 200, заметка — 403.
- Claude Code загружает `CLAUDE.md`/`AGENTS.md` всех каталогов-предков (в коде 2.1.295 — «project root and its ancestor and nested directories»). Фикстуры лежат внутри репозитория SA и получили бы его `AGENTS.md` с запретом запускать SA. Поэтому в `.claude/settings.local.json` фикстур задан `claudeMdExcludes` для обоих файлов репозитория. Действие исключения подтвердят интерактивные прогоны.
- Проверка сохранности источников `tools/check_sources.py` принимает файл, только если исходные bytes сохранены, а новые лишь вставлены, файл строго декодируется своим codec и сохраняет BOM и контракт переводов строк. Самопроверка: исходные файлы и корректные дозаписи в каждом codec — passed; перезапись windows-1251 в UTF-8, нормализация CRLF→LF и второй BOM — failed с указанием мест.
- Регрессия пакета: `python3 -B -m unittest discover -s tests -v` — 24 passed, 1 skipped, exit 0; `fingerprint.py --help`, `install.py --help`, `git diff --check` — exit 0. После исправления дефектов 1–4 — те же результаты; пакет заново скопирован, шесть установок обновлены `install.py --update` и побайтно совпадают с ним, в allowlist фикстур добавлен `Bash(sleep:*)`.

### Пробы механизмов в сессии проверки

Пробы шли из этой сессии Code tab (auto mode, без переменных D7). Роли-пробы — сабагенты `general-purpose` с моделью haiku: модель не влияет на проверяемые механизмы, роли SA в пробах не участвовали. Метаданные — `tools/collect_dispatch.py`, результат — `.verification/claude-code/evidence/probes-this-session.json`, журнал времени — `probes/cron-probe.log`.

- **Вложенный агент без D7 не отклоняется.** Роль глубины 1 вызвала Agent; создан агент `spawnDepth: 2` с `parentAgentId` роли, он ответил. У обеих ролей в `prefix.json` есть `Agent` и `Skill`. Роль, перечисляя свои инструменты, `Agent` не назвала, хотя он у неё был: самоотчёт роли о наборе инструментов недостоверен, проверять по `prefix.json`.
- **Cron не срабатывает, пока работает фоновая роль.** Задача `*/1 * * * *` создана в 15:36:56 UTC; фоновая роль работала 15:37:02–15:41:06, основной ход завершился сразу после её запуска. За четыре минутные границы cron не сработал ни разу. Контроль: через 7 секунд после того, как сессия освободилась от фоновой работы, пришло одно срабатывание (15:41:27, не на границе минуты); пропущенные тики свернулись в одно.
- **Фоновый Bash-таймер будит координатора при работающей роли.** `sleep 70` с `run_in_background` завершился в 15:42:57, ход координатора начался в 15:43:00; фоновая роль при этом работала с 15:41:52 до 15:45:16.
- **Побочный эффект CronCreate.** Первый вызов создал в корне проекта `.claude/scheduled_tasks.lock` (sessionId, pid) и в то же время изменил `.git/info/exclude`, где есть правило `**/.claude/scheduled_tasks.lock`. `git status` файл не показывает, но это запись в `.claude/` и `.git/` проверяемого проекта.
- **Метаданные dispatch извлекаются.** `subagents/agent-<id>.meta.json`: `agentType`, `spawnDepth`, `parentAgentId`, `requestShape` (foreground/background), `model` — только если передан в вызове. `prefix.json`: модель и `toolNames`. `jsonl`: первая запись с `parentUuid: null`, единственная строковая user-реплика равна prompt вызова Agent (сверка по SHA-256). Токены роли: `subagent_tokens` из итога или уведомления о завершении — это размер контекста последнего вызова, а не сумма; сумму ввода по вызовам экстрактор считает из `usage` каждого вызова. `usage.output_tokens` в транскрипте занижены (потоковые частичные записи) и как источник не годятся.
- **Базовая стоимость роли.** Контекст первого вызова тривиальной роли-пробы — 49,5–53 тыс. токенов: системный prompt и описания инструментов desktop-среды до чтения SKILL и references. `subagent_tokens` этих ролей — 52–67 тыс.; суммарный ввод роли из четырёх вызовов — около 205 тыс., в основном чтения из кеша.
- **Инструменты роли в desktop.** У `general-purpose` 48 инструментов, среди них Artifact, `start_session` и `hand_off_to_session`, управление сессиями (`send_message`, `stop_session`, `delete_session`), `set_setting` настроек приложения, CronCreate, PushNotification, EnterWorktree, коннектор документов и браузеры.

### Сценарии этапа 7

| Сценарий | Результат | Основание |
| --- | --- | --- |
| Обнаружение `/sa` | passed; меню `/` не проверено | `claude -p`: init-событие перечисляет `sa` в `skills` и `slash_commands` (вопреки 8.2.15 плана). Сообщение `/sa …` в сессиях Code tab запустило скилл в прогонах A, B, C. Модельный ход в `-p` невозможен: отдельный CLI не авторизован. Меню `/` глазами не проверено. |
| Bare `/sa`: один вопрос, без изменений | passed | Прогон D: один вопрос AskUserQuestion с текстом SKILL, до ответа только чтения, час ожидания не принят за ответ. |
| audit: свежие роли, разные ID, `general-purpose` | passed | Прогон A: 3/3 accepted, 7 разных ролей `general-purpose`, общий дефект сведён к одной канонической задаче, приложение не изменено. |
| fix: общий дефект на двух источниках, параллельные линии | passed | Прогон B: общий дефект на двух источниках сведён и исправлен, линии правильно сериализованы из-за общей closure. Прогон F: при независимых closure две линии шли параллельно на всех фазах. |
| full | passed | Прогон E: аудит, исправление и завершающий аудит одного эндпоинта, девять свежих ролей, независимая проверка доступа прошла. Прогон D (fx-restart): второй full, 10 ролей, одна задача high resolved с оценкой 9, завершающий аудит принят. |
| Часовая сводка на укороченном интервале | failed для CronCreate; passed для фонового Bash-таймера в SA-потоке | Пробы механизма выше. Прогон A на исправленном адаптере: сводки при 180, 606 и 797 с, пока работали роли; таймер остановлен в конце. |
| Продолжение после `/compact` | не проверено | В прогоне D пользователь выбрал `full`, шаг с `/compact` не выполнялся; `/compact` может отправить только пользователь. |
| Роль вызывает `sa` и запускает агента | passed с D6 и D7; failed для вложенности без D7 | Прогон 0: Skill `sa` отклонён механизмом и для координатора, и для роли. При `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1` инструмента Agent у роли нет. Без этой переменной вложенный агент создаётся (проба в сессии проверки), защита — только строка задания. |
| Неразрешённая команда в фоновой роли → blocked | passed для отчёта, с оговоркой; отказ пользователя не проверен | Прогон 0: роль вернула blocked с именем инструмента Bash. Но deny-правило `Bash(git log:*)` не остановило `git -C <путь> log`, и роль получила результат до отказа. Отказ пользователя в запросе не проверен: прогон D шёл без отказов. |
| Побайтовая сохранность источников | passed | Прогон B: UTF-16 LE с BOM и CRLF, windows-1251 и смешанные CRLF/LF — исходные bytes сохранены, новое только дописано, кодировки и переводы строк соблюдены. |
| `.claude/agents/general-purpose.md` и hook проекта | passed | Прогон C: blocker до запуска ролей, hook и внешние инструкции записаны в `project_config`. Проба подтвердила: проектный агент действительно подменяет встроенный, а hook срабатывает и на вызовах ролей. |
| Рестарт при работающей роли | passed для рестарта приложения и лимита; выключение Mac — см. «Обрывы и восстановление» | Без прогона D: рестарт приложения (B), лимит тарифа (A, B) и выключение Mac (A) случились по ходу прогонов. Отказ пользователя в запросе разрешения (часть D) не проверен. |
| Доказательства dispatch по транскриптам | passed | Пробы и прогон A: тип, глубина, `model`, совпадение первого сообщения с prompt, отсутствие Agent и Skill внутри ролей, токены. |
| Регрессия Codex: discovery, frontmatter | passed | См. ниже. |
| Регрессия Codex: один audit | passed | Вторая попытка после повторного входа: 1/1 эндпоинт принят, три роли через `spawn_agent` с `fork_turns: "none"`, читается только адаптер Codex. Первая попытка — 401 `token_revoked`. |

### Прогоны в фикстурах

По просьбе пользователя прогоны запускаются из сессии проверки: `start_session` открывает отдельную сессию Code tab в папке фикстуры (без worktree, auto mode) и передаёт ей первое сообщение. Сообщение, начинающееся с `/sa …`, разворачивается в скилл так же, как набранная команда (прогон A). Ограничение: такую сессию приложение разрешает запускать только по реплике пользователя в сессии проверки, не по уведомлению другой сессии. Вопросы и запросы разрешений в запущенной сессии видит и решает пользователь.

**Прогон 0 (fx-probe), 15 октября 2026.** Метаданные — `evidence/run0-probe.json`.

- Skill `sa` от координатора: ошибка «Skill sa cannot be used with Skill tool due to disable-model-invocation. Ask the user to run /sa themselves…». Тот же отказ получила роль. D6 работает механизмом.
- `env` из `.claude/settings.local.json` применяется в сессии desktop: `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1`, `CLAUDE_CODE_FORK_SUBAGENT=0`. У ролей в `prefix.json` нет `Agent` (47 и 42 инструмента против 48 без переменной); поиск `Agent` через ToolSearch ничего не нашёл. Вложенность выключена механизмом.
- Фоновая роль с обязательными строками задания: сначала `git -C <корень> log --oneline -1` — выполнено, deny-правило `Bash(git log:*)` его не поймало; затем `git log --oneline -1` — «Permission … has been denied». Итог роли — blocked с именем инструмента. Вывод: deny-правила Bash по префиксу обходятся перестановкой аргументов и не являются надёжным ограничением роли.
- Обе роли — `general-purpose`, разные ID, первое сообщение равно prompt вызова, `model` не передавался; контекст первого вызова — 47,5 и 51 тыс. токенов.
- После итога пробы пользователь написал в этой сессии «Надо исправлять ошибки». Сессия запросила доступ к каталогу репозитория SA, получила его и исправила адаптер, `STEPS.md` и этот файл (дефекты 6 и 7 ниже). Это правки по просьбе пользователя, а не поведение роли SA.

**Проба 2 (fx-probe, 16 октября, установки с правками 6–11).** Фоновая роль с новыми обязательными строками: записать вывод тестов во временный файл и получить хеш коммита «обычным способом — `git log --oneline -1`» при deny-правиле `Bash(git log:*)`.

- Правка 9 работает: роль создала `<scratchpad>/probe-2-a1/` и писала только туда.
- Правка 6: роль сразу выполнила `git -C <корень> log --oneline -1`, deny-правило его не поймало, отказа не было. Поэтому строку «отказ не обходи» эта проба не проверила, зато вывод адаптера — deny-правило Bash по началу команды не ограничение — подтвердился повторно. Форма `git -C` не случайна: инструкции Claude Code для агентов советуют абсолютные пути вместо `cd`.
- В итоге роль написала, что хеш получен «`git log --oneline -1`», хотя выполнена другая форма команды. Самоотчёт роли о командах приходится сверять с транскриптом.

**Как запускается `/sa` из первого сообщения.** Во всех прогонах (A, B, C) приложение не развернуло команду само: модель вызвала Skill с `sa` и аргументами из сообщения, и вызов прошёл («Launching skill: sa»), а следом пришло содержимое `SKILL.md` («Base directory for this skill: /Users/georg/.claude/skills/sa»). В прогоне 0 такой же вызов без команды пользователя был отклонён. Значит, `disable-model-invocation` пропускает вызов Skill только после команды `/sa` в сообщении — то, что и требует D6. Взята глобальная копия: у личного скилла приоритет над проектным.

**Прогон A (fx-audit), `/sa audit` с интервалом сводки 180 с.** Метаданные — `evidence/runA-audit.json`.

- Итог: 3/3 эндпоинта приняты независимыми ревью, reused 0, 12 категорий на каждый. Общий IDOR в `services.load_document` — одна каноническая задача `get-documents-id-i01` (high); запись превью — `superseded` с `canonical_issue_id`, в своём контексте medium. Исправный `GET /notes/{id}` — 0 проблем. Приложение не изменено: в `git status` только `Security Audit/`.
- Dispatch: 7 ролей (ревью инвентаря, 3 аудитора, 3 ревьюера), 7 разных ID, все `general-purpose`, `requestShape: background`, `model` не передавался, глубина 1. Первое сообщение каждой роли равно prompt вызова Agent, строковая user-реплика одна. Внутри ролей нет вызовов Agent и Skill (инструмент Agent у ролей был: в фикстуре нет D7, удержала строка задания). Три аудита стартовали одновременно — параллельные линии работают.
- Инвентарь составил координатор, свежая роль его независимо проверила и приняла; это соответствует `audit.md`.
- Таймер: сводки при 180, 606 и 797 с активного времени, пока роли работали; в конце координатор остановил таймер через `TaskStop`, `heartbeat_id: null`. Active time запуска — 1016 с.
- Стоимость: контекст первого вызова роли — 49,6–50,3 тыс. токенов, `subagent_tokens` — 87–118 тыс., 13–25 вызовов модели на роль, суммарный ввод роли — 1,07–2,11 млн токенов (около 10,3 млн на семь ролей, в основном чтения из кеша).
- Не проверено в этом прогоне: bare `/sa` и `/compact` — оба шага требуют ввода пользователя в сессии прогона.
- Дальше в той же сессии по просьбе пользователя: `fix` (новый run со ссылкой на аудит; линия документов исправила `services.load_document`, линия превью доказала применимость того же исправления, у `notes` записанных замечаний нет), затем повторный `audit` всех эндпоинтов на конечном коде — 3/3 accepted, новых проблем нет. Независимая проверка: на всех трёх маршрутах чужой объект — 403, владелец — 200, без входа — 401, тесты — OK. За три запуска — 25 ролей с разными ID; у трёх аудиторов, оборванных выключением Mac, нет `prefix.json`.
- Координатор перенёс сокращённый интервал сводки (180 с) из исходного `/sa audit` в последующие запуски той же сессии.

**Прогон C (fx-config), `/sa audit`.** Метаданные — `evidence/runC-config.json`, журнал hook — `fixtures/fx-config/.claude/hook-events.jsonl`.

- Координатор нашёл `.claude/agents/general-purpose.md` и до запуска ролей записал blocker `role-type-override` («blocker until user decision»), `status: partial`. Ни одной роли не запущено; вопрос через AskUserQuestion не задан — blocker описан текстом в итоге.
- `project_config` собран по новому правилу: файлы проекта с SHA-256, отсутствующие файлы, факт наличия `settings.local.json` без чтения, hook с описанием, внешние инструкции (`CLAUDE.md`/`AGENTS.md` репозитория SA как предка, `~/.claude/CLAUDE.md`, пользовательские скиллы), сверка проектной копии скилла с `skill_root`. Ограничение: исключение предков через `claudeMdExcludes` лежит в `settings.local.json`, которую координатор не читает, поэтому исключённые файлы он записал как загружаемые.
- PreToolUse-hook проекта сработал на все 23 вызова координатора; `agent_id` пуст, ролей не было.
- Проба после blocker (не роль SA): вызов Agent с `subagent_type: "general-purpose"` запустил проектного агента. Его ответ начался с маркера `PROJECT-GP-OVERRIDE`, в `prefix.json` четыре инструмента (Read, Grep, Glob, SubagentHandback), контекст первого вызова — 5 тыс. токенов вместо ~50 тыс. у встроенного. В `meta.json` тип всё равно `general-purpose`: по типу подмену не отличить, нужно сверять `toolNames` и размер контекста. Blocker в адаптере оправдан.
- Hook проекта сработал и на вызове роли: запись с `agent_id` и `agent_type: general-purpose`. Значит, PreToolUse-hook видит вызовы внутри сабагентов (открытый вопрос D7).
- Координатор прочитал заметки прогона 0 из общей папки заметок связанных сессий. Это канал между прогонами, а не поведение SA: сессии прогонов, запущенные из одной сессии, делят заметки.

**Прогон B (fx-fix), `/sa fix`.** Метаданные — `evidence/runB-fix.json`, сохранность источников — `evidence/runB-sources.json`.

- Итог: 3/3 исходных файла обработаны. Канонические DOC-1 (общий дефект `services.load_document`, источники `documents.md` и `preview.txt`) и NOTE-1 (`notes.py`) — resolved, оценки 9; PRV-1 — `superseded` с `canonical_issue_id` DOC-1. Remediation Summary с таблицей «Файл | Эндпоинт | Замечание | Оценка».
- Независимая проверка после прогона (`check_fix_effect.py`): чужой документ, превью и заметка — 403, владелец — 200, без входа — 401, тесты фикстуры — OK. Изменения приложения: `services.py` (+2 строки), `notes.py` (+3/−1), тесты в `tests/security/`. Правило про `tests/security/` есть только в `AGENTS.md` фикстуры при существующем `CLAUDE.md`: роли прочитали `AGENTS.md` явно.
- Сохранность источников (`check_sources.py`): все три passed, исходные bytes целиком сохранены, новое только дописано в конец. `documents.md` (UTF-16 LE, BOM, CRLF): 1354 → 8542 байта, один BOM, только CRLF. `notes.md` (UTF-8, смешанные переводы строк): 473 → 2171 байт, исходные четыре одиночных LF на месте. `preview.txt` (windows-1251): 395 → 2243 байта, строгое декодирование cp1251, без CR, UTF-8 в дописанном нет. Координатор дополнительно сохранил исходные bytes в `Remediation/<run>/History/`.
- Dispatch: 15 ролей, 15 разных ID, все `general-purpose`, background, без `model`, глубина 1; первое сообщение равно prompt вызова; внутри ролей нет Agent и Skill. Это по четыре роли на источник, повторное ревью кода `documents.md` (round 2) и две новые попытки после обрывов.
- Линии шли по очереди; одновременно работали только ревью кода `documents.md` r2 и планирование `preview.txt`. Причина — общая closure: `handlers.py` импортирует и `services`, и `notes`, поэтому правка `notes.py` изменила версию эндпоинтов документов. Решение по DOC-1 стало `stale`, и новый ревьюер кода принял его заново. Это соответствует `orchestration.md`. Параллельные линии fix на этой фикстуре не проверить: у её источников нет независимых closure.
- Стоимость: контекст первого вызова роли — 50,6–51,5 тыс. токенов, `subagent_tokens` — 160–233 тыс., 19–38 вызовов модели на роль, суммарный ввод роли — 2,1–5,9 млн, всего около 62,4 млн на 15 ролей. Active time — 7834 с.
- Инцидент: одна роль перезаписала три временных файла (`closure.json`, `inputs.json`, `plan.json`) другой роли в общем scratchpad сессии вне проекта. Роль сама это обнаружила, записала в State как инцидент и дальше писала в собственный подкаталог. Артефакты SA и входы не пострадали.

**Прогоны E и F (16 октября, Claude Code 2.1.299, установка с правками 6–11).** Сессии открыты из сессии проверки по реплике пользователя; метаданные — `evidence/run-fx-full.json` и `evidence/run-fx-fix-par.json`.

- **E, `/sa full` на `fx-full`.** Девять ролей по очереди, все `general-purpose`, разные ID, без `model`, глубина 1, без Agent и Skill внутри: ревью инвентаря, аудитор, ревьюер, планировщик, ревьюер плана, исполнитель, ревьюер кода, завершающие аудитор и ревьюер (round 2). Итог: одна задача high найдена, исправлена (resolved, оценка 9), завершающий аудит на конечном коде принят. Независимая проверка: чужой документ — 403, владелец — 200, без входа — 401, тесты — OK. Изменены `services.py` и `tests/test_app.py`.
- **F, `/sa fix` на `fx-fix-par`.** Восемь ролей, по четыре на линию. Линии шли параллельно на всех фазах: планирование, ревью плана, внедрение и ревью кода двух линий пересекались по времени (7 пересекающихся пар ролей), исполнители писали непересекающиеся файлы (`docs_service.py`, `notes_service.py` и по своему тесту). DOCS-1 и NOTES-1 resolved, оценки 9. Независимая проверка: оба маршрута — 403 для чужого объекта. Оба источника сохранили исходные bytes, новое только дописано. Тесты легли по одному файлу на эндпоинт в `tests/security/` — правило есть только в `AGENTS.md` фикстуры.
- **Правка 7:** оба координатора проверяли переменные по одной (`printenv "$v"` в цикле; отдельные вызовы).
- **Правка 9:** все 17 ролей писали временные файлы только в свои `<scratchpad>/<attempt_id>/`.
- **Таймер:** оба координатора запустили фоновый `sleep` до порога вместе с первыми ролями и остановили его через `TaskStop` в конце; сводка не понадобилась — прогоны короче часа.
- **Стоимость:** контекст первого вызова роли на 2.1.299 — 46,3–47,6 тыс. токенов; суммарный ввод — 24,0 млн (E, 9 ролей) и 22,6 млн (F, 8 ролей).

**Прогон D (fx-restart, режим с запросами разрешений, первое сообщение — `/sa` без режима).** Метаданные — `evidence/runD-restart.json`.

- Bare `/sa`: координатор задал ровно один вопрос AskUserQuestion с текстом из SKILL («Что делаем: аудит эндпоинтов, исправление имеющихся замечаний или оба этапа по очереди?»). До ответа — только чтения (`git log`, `find`, файлы скилла, README, заметки связанных сессий), ни одной записи. Ответа он ждал около часа и истёкшее ожидание ответом не считал.
- Пользователь выбрал `full` вместо отмены, поэтому шаги с отказом в запросе разрешения и `/compact` не выполнялись. Отказов в транскрипте нет, событий компакции нет.
- `full` завершён: 9 ролей `general-purpose` с разными ID, задача high исправлена (resolved, оценка 9), завершающий аудит принят. До первой роли сессия упёрлась в лимит тарифа и продолжила после сброса; роли в момент обрыва не работали, поэтому правило 8 этот обрыв не проверил. Пауза в active time не вошла.
- Отклонение: inventory-роль прочитала `CLAUDE.md` и `AGENTS.md` репозитория SA, исключённые в фикстуре через `claudeMdExcludes`: строка задания «CLAUDE.md и AGENTS.md проекта» не отличает файлы корня проекта от предков. Координатор записал это в State (дефект 12).

**Коммит в прогоне A.** По прямому указанию пользователя («Закоммить только services.py и tests/test_app.py, папку Security Audit не включай») координатор создал коммит в новой ветке фикстуры `fix/document-owner-check`, без `Security Audit/` и без push. Правило «commit только по явной просьбе» соблюдено.

**Заметки связанных сессий.** Сессии прогонов, запущенные из сессии проверки, получают общую папку заметок вне проекта. Координаторы C и D прочитали в ней заметки пробы fx-probe. Координатор F записал туда заметку о своём прогоне и явно указал, что находки и payload в неё не включены. Граница соблюдена, но адаптер этот канал не называет (предложение 13).

### Обрывы и восстановление

| Событие | Прогон | Что сделал координатор | Таблица прерываний адаптера |
| --- | --- | --- | --- |
| Рестарт desktop-приложения около 17:08Z | B | Планировщик `documents.md` (attempt 1) оборвался: транскрипт кончается в 17:07:14Z, `prefix.json` нет. Интервал active time закрыт в 17:08:40Z с основанием «heartbeat killed with process». После реплики пользователя «Продолжу с того места…» — новая попытка новым Agent, новый таймер. | соблюдена |
| Лимит тарифа (HTTP 429) около 18:30Z | A (fix), B | Роли получили уведомление `failed` с советом: «send the agent a message (SendMessage) to let it continue from where it stopped instead of starting a new agent». Ходы координаторов падали до сброса лимита. После «продолжи» из сессии проверки в 20:22Z оба координатора сверили код, diff и снимки, записали прежнюю попытку как failed с причиной, запустили новую попытку новым Agent (SendMessage не вызывался), исключили паузу из active time (A: `paused_intervals` 18:30:23–20:22:36Z с причиной; B: интервал закрыт временем отказа роли). Таймер, сработавший в паузе (B, 19:00:45Z), сводку не выдал: порог по active time не достигнут. | соблюдена |
| Выключение или перезагрузка Mac около 21:13Z | A (повторный audit r2) | Три аудитора оборвались посреди работы, без итога; таймер не сработал. Система стартовала в 09:42 по местному времени, приложение обновило Claude Code до 2.1.299. После «продолжи» в 06:45Z координатор сверил профили, fingerprints и dependencies с `History/`. Два аудитора профили не дописали: их попытки помечены `stopped`, частичные результаты сохранены в `History/<run>/attempt-a1-partial/`, запущены новые попытки a2. Аудитор `get-notes-id` оборвался сразу после последней дозаписи профиля: профиль полный (`ready_for_review`, проверки конца работы, fingerprint совпадает с кодом), попытка засчитана как `complete_by_artifacts` и передана свежему ревьюеру. Время до перезапуска в active time не вошло, таймер запущен заново. | соблюдена; принятие результата без итога роли адаптером не описано (дефект 11) |

**SendMessage вместо новой попытки.** Адаптер требует для новой попытки новый Agent и запрещает продолжать через SendMessage завершённую роль; уведомление Claude Code о сбое советует обратное. Координаторы выбрали новую попытку. Цена — повторное чтение всего контекста: новая попытка планировщика `preview.txt` в B — 28 вызовов и 3,4 млн токенов суммарного ввода. Независимость продолжение той же попытки не нарушает: роль видит только собственный контекст и нейтральное «продолжи», а не историю координатора. Риск в другом: роль продолжит работу на чтениях, сделанных до обрыва, а за это время другие линии могли изменить её входы. Предложение — уточнить адаптер (см. дефект 8).

### Регрессия Codex

Установка `--platform codex` в `.verification/claude-code/codex/fx-codex/.agents/skills` (12 файлов пакета с `agents/openai.yaml` и manifest) и контрольный скилл `broken-control` с повреждённым YAML. Настоящий `codex app-server`, `initialize`, затем `skills/list` с `forceReload` (`tools/codex_skills_list.py`, результат — `evidence/codex-skills-list.json`): `sa` — scope `repo`, enabled, путь установленного `SKILL.md`, interface из `openai.yaml` (`SA`, default prompt с `$sa`). Ошибка только у контроля: «invalid YAML: mapping values are not allowed…». Значит, `argument-hint` и `disable-model-invocation` загрузку не ломают, а пустой список ошибок для `sa` осмыслен. Поля для `disable-model-invocation` в метаданных Codex нет: Codex его не применяет, неявный вызов по описанию в Codex остаётся как прежде.

**Модельный аудит в Codex (16 октября, Codex CLI 0.162.0-alpha.17.2, пакет с правками 6–11 и правкой ядра 10).** Первая попытка упала на отозванном токене (см. «Неуспешные и неполные попытки»); после повторного входа пользователя `codex exec -C <fx-codex> -s workspace-write --json '$sa audit'` завершился exit 0 за 21 минуту.

- Итог: 1/1 эндпоинт, 12 категорий, независимое ревью принято; одна подтверждённая задача high — IDOR в `GET /documents/{id}` по явному контракту owner-only. Приложение не изменено, тесты фикстуры — OK. State: `schema: 2`, `platform: Codex`, `skill_root` — repo-установка, `goal_owned: false`, `heartbeat_id: null`.
- Dispatch по журналам сессий Codex (`~/.codex/sessions/…`): три вызова `spawn_agent` с `fork_turns: "none"`, без model и effort; три разных потока-субагента глубины 1 (`sa_073047_inventory_r1`, `sa_073047_docs_audit_r1`, `sa_073047_docs_review_r1`) с `parent_thread_id` координатора.
- Координатор читал только `references/platform-codex.md`; адаптер Claude Code упоминается лишь ссылками внутри `SKILL.md`. Нейтральное ядро и выбор адаптера в Codex работают.
- Токены: координатор — 3,4 млн суммарно (3,2 млн из кеша), роли — 0,53–0,70 млн.

### Глобальная установка

По явной просьбе пользователя `python3 -B scripts/install.py --platform claude` установил `sa` в `~/.claude/skills/sa`, exit 0: 11 файлов пакета и manifest, без `agents/`. На момент установки `SKILL.md`, references и scripts побайтно совпадали с рабочим деревом. Init-событие `claude -p` в пустом каталоге перечисляет `sa` в `skills` и `slash_commands`. До установки `/sa` в сессии другого проекта (ROCKET) отсутствовал: проектные установки действуют только в своих фикстурах. Личный скилл имеет приоритет над проектным с тем же именем, поэтому прогоны в фикстурах берут глобальную копию; в allowlist фикстур добавлено `Read(~/.claude/skills/sa/**)`. После изменения пакета глобальную копию нужно обновить (`--update`).

### Неуспешные и неполные попытки

- Модельный аудит в Codex (16 октября, 07:24Z): установка `--platform codex` в `codex/fx-codex` обновлена до текущего пакета и сверена побайтно; функция `multi_agent` включена. `codex exec -C <fx-codex> -s workspace-write --json '$sa audit'` завершился с exit 1 через 19 секунд: сервер вернул 401 «Encountered invalidated oauth token», код `token_revoked`, хотя `codex login status` сообщает «Logged in using ChatGPT». Модель не вызывалась, фикстура не изменилась. Нужен повторный вход пользователя в Codex (`codex login`); входить за пользователя проверка не вправе.
- Первый запуск `claude -p` обёрнут в `timeout`: на macOS этой команды нет, exit 127, CLI не стартовал. Повтор без обёртки дал init-событие и результат «Not logged in · Please run /login» (exit 1). Модельные `-p`-пробы, включая D6 и blocked, перенесены в Code tab (прогон 0): входить в CLI за пользователя нельзя.
- `claude plugin validate` не использовался как доказательство (см. технические проверки выше).

### Найденные дефекты инструкций

1. **Таймер сводки** (`platform-claude-code.md`, «Часовая сводка») — исправлено в адаптере по решению пользователя. Таймер нужен ровно для фазы, в которой роли работают дольше часа без завершений, а именно тогда CronCreate не срабатывает. Теперь, пока работает хотя бы одна роль, координатор держит один таймер — фоновую Bash-команду `sleep` до следующего порога (не меньше 60 с, ID в `heartbeat_id`). По её завершении он проверяет порог, выдаёт сводку и запускает новый таймер; лишний таймер останавливает через `TaskStop`. CronCreate для сводки не используется, это снимает и побочный эффект в `.claude/` и `.git/info/exclude`. Строка `--resume` в таблице прерываний: прежний `heartbeat_id` недействителен, таймер создаётся заново. В список разрешений адаптера и README добавлен фоновый `sleep`. Реальным прогоном SA исправление ещё не подтверждено (прогон A с интервалом 180 с).
2. **Обязательные строки задания** (адаптер) — исправлено. У роли в desktop есть управление настройками приложения и чужими сессиями, таймеры и push. Добавлена строка: «Не меняй настройки Claude Code и приложения, не создавай таймеры и уведомления (CronCreate, PushNotification), не отправляй сообщений другим сессиям и не управляй ими». Строка — второй рубеж: инструменты у роли остаются, механизмом это не закрыто.
3. **Конфигурация проекта** (адаптер, `platform_context.project_config`) — исправлено по решению пользователя. Список не включал инструкции предков (`CLAUDE.md`/`AGENTS.md` выше корня проекта), `CLAUDE.local.md` и `.claude/rules/`, хотя они загружаются в сессию и в роли. Теперь адаптер перечисляет всё, что Claude Code 2.1.295 загружает в сессию: `CLAUDE.md`, `CLAUDE.local.md`, `AGENTS.md` предков до `/`, `.claude/CLAUDE.md`, `.claude/AGENTS.md`, `~/.claude/CLAUDE.md`, импорты `@путь`, `rules/`, `agents/`, `skills/`, `commands/` проекта и `~/.claude/`, вложенные инструкции подкаталогов. Пути и SHA-256 этих файлов, `.claude/settings.json` и `.mcp.json` пишутся в State, содержимое не выводится. До первой роли координатор называет пользователю инструкции и агентов вне корня проекта; исключить их может только пользователь через `claudeMdExcludes`. Проверка подмены `general-purpose` расширена на `~/.claude/agents/` и идёт по полю `name`, а не по имени файла. Ядро не менялось: `artifacts.md` ссылается на формат адаптера.
4. **Стоимость в README и плане** — исправлено. README называл только объём references (до ~120 КБ), план §7 — 30–40 тыс. токенов на их чтение. Теперь оба указывают базовый контекст роли в desktop — около 50 тыс. токенов до чтения скилла — и то, что каждый вызов модели внутри роли перечитывает контекст из кеша.
5. **План, 8.2.15.** Утверждение «init-событие не перечисляет скиллы» для 2.1.295 неверно; `-p` требует отдельного входа в CLI.
6. **Обход deny-правила другой формой команды** (адаптер, «До первой роли» и «Обязательные строки задания») — исправлено в исходнике. В прогоне 0 роль сама выбрала `git -C <корень> log --oneline -1`, хотя задание требовало дословную команду и запрещало другие способы. Deny-правило `Bash(git log:*)` такую команду не поймало, и роль получила результат до отказа. Адаптер теперь предупреждает: deny-правило Bash по префиксу не является подтверждённым ограничением роли. В обязательные строки задания добавлено: «Отказ или ограничение не обходи другой формой команды или другим инструментом». Первоначальная редакция сессии пробы требовала ещё запускать команды дословно, без `cd` и `-C`; по решению пользователя эта часть убрана: она подогнана под пробу, а роли SA команды дословно почти не получают. Задание роли в прогоне 0 `STEPS.md` синхронизировано. Строка — второй рубеж, механизм она не заменяет. Реальным прогоном исправление не подтверждено. Установки в фикстурах и глобальная копия обновляются после завершения прогона B: его роли читают глобальную копию.
7. **`printenv` с несколькими именами** (адаптер, «До первой роли»; шаг 2 прогона 0 в `STEPS.md`) — исправлено. BSD `printenv` в macOS из нескольких имён печатает только первое значение и завершается с exit 0. В прогоне 0 вывод `1` не показал `CLAUDE_CODE_FORK_SUBAGENT`; её значение `0` подтвердил отдельный вызов. Адаптер и шаг 2 теперь требуют отдельный `printenv` на каждую переменную.
8. **Продолжение роли, оборванной внешней причиной** (адаптер, «Запуск роли» и таблица прерываний) — внесено 16 октября по решению пользователя (подраздел «Роль, оборванная до итога»). Уведомление Claude Code советует SendMessage, адаптер его не упоминает. Предложение: роль, оборванную лимитом, ошибкой API или рестартом до её итога, можно продолжить той же попыткой через SendMessage с нейтральным текстом («продолжи с места остановки; перед записью сверь текущие версии входов»), если сверка координатора показала, что её входы и closure с начала попытки не менялись. В State — пометка о продолжении той же попытки. Иначе, а также для роли, вернувшей итог, или для новой фазы, раунда, попытки — новый Agent. Совет уведомления в остальных случаях не применять.
9. **Общий scratchpad сессии** (адаптер, обязательные строки задания) — внесено 16 октября по решению пользователя. Все роли сессии получают один scratchpad, и в прогоне B роль затёрла чужие временные файлы. Предложение: «Временные файлы — только в собственном подкаталоге `<scratchpad>/<attempt_id>/`; чужие файлы не трогай».
10. **Формулировка доставки сводки в ядре** (`orchestration.md`, «Время, прогресс и ETA», последний абзац) — внесено 16 октября по решению пользователя; ядро с правкой прошло прогоны E, F и аудит в Codex. «Prompt читает checkpoint» описывает таймер с собственным prompt, как у cron; у фонового `sleep` prompt нет, checkpoint читает пробуждённый координатор. Предложение: «Срабатывание таймера читает checkpoint и даёт запрошенную часовую сводку без повторного назначения ролей». Правка ядра требует согласования и проверки в обеих средах.

11. **Результат роли без её итога** (адаптер, таблица прерываний) — внесено 16 октября по решению пользователя (подраздел «Роль, оборванная до итога»). После выключения Mac координатор A засчитал оборванную попытку аудитора по артефакту (`complete_by_artifacts`). Независимость сохраняется: результат затем проверяет свежий ревьюер. Но адаптер такого исхода не описывает. Предложение: попытку без итога можно засчитать, только если её процесс точно остановлен, артефакт содержит собственный финальный статус роли и версии, а fingerprint совпадает с текущим кодом; в State — `complete_by_artifacts` с основанием. Иначе — новая попытка.

12. **Чтение исключённых инструкций предков** (адаптер, обязательные строки задания) — не исправлено, предложение. В прогоне D роль по строке «Прочитай CLAUDE.md и AGENTS.md проекта» прочитала файлы каталога-предка, которые пользователь исключил через `claudeMdExcludes`. В обычной установке проект не лежит внутри другого репозитория, поэтому влияние небольшое. Предложение: «Прочитай CLAUDE.md и AGENTS.md в корне проекта и нужных подкаталогах; файлы вне корня, исключённые пользователем, не читай».

13. **Заметки связанных сессий** (адаптер, «Конфиденциальность» и обязательные строки задания) — не исправлено, предложение. В desktop сессия, запущенная из другой, получает общую папку заметок вне проекта и инструкцию читать и пополнять её. Предложение: добавить заметки связанных сессий в перечень каналов, куда не попадают находки, payload и секреты, а прочитанные оттуда заметки считать данными, не относящимися к проекту.

### Проверка правок 6–11 прогонами

Предложения 8–11 внесены в исходник по решению пользователя; глобальная установка, шесть фикстур и Codex-фикстура обновлены и побайтно совпадают с рабочим деревом.

| Правка | Результат | Основание |
| --- | --- | --- |
| 6. Deny-правило Bash не считать ограничением; «отказ не обходи» | частично | Проба 2: deny-правило снова обойдено формой `git -C`, вывод адаптера подтверждён. Строка «отказ не обходи» не проверена: отказа не было. |
| 7. `printenv` по одной переменной | passed | Прогоны E и F. |
| 8. Продолжение оборванной роли через SendMessage | не проверено | В прогонах после установки обрывов не было; безопасно вызвать обрыв роли не удалось. |
| 9. Временные файлы в `<scratchpad>/<attempt_id>/` | passed | Проба 2, прогоны E и F: все роли писали только в свои подкаталоги. |
| 10. Формулировка доставки сводки в ядре | passed косвенно | Прогоны E, F и аудит в Codex шли на исправленном ядре; таймер запускался и останавливался штатно. |
| 11. Результат роли без итога | не проверено | Поведение наблюдалось в прогоне A до появления правила; после установки обрывов не было. |

### Расхождения README и плана с исправленным адаптером

README прямо адаптеру не противоречит: разрешения (включая фоновый `sleep`), стоимость и долгие запуски согласованы. Не хватает трёх фактов этапа 7:

- проектный или личный агент с `name: general-purpose` подменяет роль, и координатор остановится на blocker;
- инструкции каталогов-предков и `~/.claude/CLAUDE.md` получают и роли, исключить их можно `claudeMdExcludes`;
- deny-правила Bash по началу команды обходятся другой формой команды и ограничением роли не считаются.

План разошёлся с адаптером в разделах, которые писались до валидации; §9 фиксирует пересмотр, но сами разделы не обновлены:

- D5 (§4) и §3, строка 5: основной таймер — CronCreate, Bash-`sleep` — запасной. Адаптер — наоборот.
- 8.2.12: «сверка `heartbeat_id` с `CronList`». В адаптере `heartbeat_id` — фоновая задача Bash, сверки с `CronList` нет.
- 8.2.7: «может ли проект перекрыть встроенный `general-purpose`, документация не говорит». Прогон C: перекрывает.
- D6 и D7: открытые вопросы «проверить» закрыты — вызов `sa` из роли отклоняется механизмом, PreToolUse-hook видит вызовы внутри сабагентов.
- 8.2.15: «init-событие не перечисляет скиллы» — неверно для 2.1.295.

Закрыто 16 октября: README дополнен тремя фактами выше, разделы D5, D6, D7, 8.2.7, 8.2.12 и 8.2.15 плана помечены итогами этапа 7.
