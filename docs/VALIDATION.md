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
