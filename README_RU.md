# Zabbix Chrony NTP Monitoring Template (`zabbix-template-chrony`)

[🇬🇧 Read in English](README.md) | [🇷🇺 Читать на русском](README_RU.md)

[![Zabbix](https://img.shields.io/badge/Zabbix-7.0%20LTS%20%7C%207.4%2B-red?logo=zabbix)](https://www.zabbix.com/)
[![Chrony](https://img.shields.io/badge/NTP-Chrony-blue)](https://chrony-project.org/)
[![Agent](https://img.shields.io/badge/Agent-Zabbix%20Agent%202-green)](https://www.zabbix.com/documentation/current/en/manual/concepts/agent2)
[![GitHub Repository](https://img.shields.io/badge/GitHub-qwertykolea%2Fzabbix--template--chrony-181717?logo=github)](https://github.com/qwertykolea/zabbix-template-chrony)

Профессиональный production-ready комплекс для мониторинга клиента NTP (`chrony`) с помощью **Zabbix Agent 2**.

Разработано в соответствии с официальными стандартами Zabbix 7.4: архитектура **Master + Dependent Items**, парсинг сырых CSV данных через нативный Preprocessing, низкоуровневое обнаружение источников времени (LLD), встроенный нативный дашборд Zabbix 7.0+, готовый дашборд для Grafana, отсутствие внешних bash-скриптов и нулевая нагрузка на серверы.

---

## 🚀 Ключевые преимущества

| Характеристика | Данное решение (Suite) | Типовые шаблоны из интернета |
| :--- | :--- | :--- |
| **Количество вызовов `chronyc`** | **Всего 2 запроса в минуту** (`tracking` и `sources`) | 10–15 разрозненных вызовов каждую минуту |
| **Внешние bash-скрипты** | **0 (Zero-script)**. Только 1 файл `.conf` в агенте | 2-3 bash/awk/sed скрипта в `/usr/local/bin` |
| **Зависимость от локали ОС** | **Нет**. Используется флаг `-c` (чистый CSV) | **Высокая** (парсинг английских слов через `awk`) |
| **Поддержка чистых клиентов** | **100%**. Не требует открытия портов и слушателей | Падает с ошибкой, требуя сокета сервера и клиентов |
| **Режимы работы** | **2 шаблона в комплекте**: Passive и Active | Только один жестко заданный режим |
| **Обнаружение источников (LLD)** | **Автоматическое (LLD)** для каждого апстрима | Нет или статичный сбор |
| **Встроенный дашборд шаблона** | **Нативный дашборд Zabbix 7.0/7.4** с KPI и графиками | Отсутствует |
| **Интеграция с Grafana** | **Готовый JSON** для плагина Zabbix | Отсутствует |
| **Триггеры и алертинг** | Многоуровневые с защитой от флуда при рестарте | Отсутствуют либо базовые |

---

## 📁 Структура проекта

```text
zabbix-template-chrony/
├── README.md                                 # Английская документация
├── README_RU.md                              # Русская документация
├── agent2_conf/
│   └── chrony.conf                           # Конфигурация UserParameter для агента
├── templates/
│   ├── template_chrony_agent2_passive.yaml   # Шаблон для пассивного агента (Zabbix agent)
│   ├── template_chrony_agent2_active.yaml    # Шаблон для активного агента (Zabbix agent active)
│   └── generate.py                           # Детерминированный генератор шаблонов
├── dashboards/
│   └── grafana/
│       ├── chrony-overview.json              # Дашборд Grafana под официальный плагин Zabbix
│       ├── README.md                         # Инструкция по импорту в Grafana (EN)
│       └── README_RU.md                      # Инструкция по импорту в Grafana (RU)
└── deploy/
    ├── install.sh                            # Скрипт автоматической установки на Linux
    ├── uninstall.sh                          # Скрипт чистого удаления
    └── ansible/                              # Автоматизация для парка серверов
        ├── playbook.yml                      # Ansible playbook
        ├── inventory.ini.example             # Пример инвентаря
        ├── README.md                         # Инструкция к Ansible (EN)
        └── README_RU.md                      # Инструкция к Ansible (RU)
```

---

## ⚡ Быстрый старт (Установка на Linux-хост)

### Вариант 1: Однострочная онлайн-установка с GitHub (Рекомендуется)

```bash
curl -fsSL https://raw.githubusercontent.com/qwertykolea/zabbix-template-chrony/main/deploy/install.sh | sudo bash
```

### Вариант 2: Локальный запуск из клонированного репозитория

```bash
git clone https://github.com/qwertykolea/zabbix-template-chrony.git
cd zabbix-template-chrony/deploy
sudo chmod +x install.sh
sudo ./install.sh
```

### Вариант 3: Ручная установка (1 минута)

1. Скопируйте файл конфигурации:
   ```bash
   sudo cp agent2_conf/chrony.conf /etc/zabbix/zabbix_agent2.d/chrony.conf
   sudo chmod 644 /etc/zabbix/zabbix_agent2.d/chrony.conf
   ```

2. Перезапустите службу агента:
   ```bash
   sudo systemctl restart zabbix-agent2
   ```

3. Проверьте опрос метрик:
   ```bash
   zabbix_agent2 -t chrony.tracking
   zabbix_agent2 -t chrony.sources
   ```

---

## 🖥️ Настройка в Zabbix Web UI

1. Перейдите в **Data collection** -> **Templates** -> кнопка **Import**.
2. Выберите подходящий файл из папки `templates/`:
   * `template_chrony_agent2_passive.yaml` — для серверов, доступных Zabbix-серверу/прокси напрямую по порту 10050.
   * `template_chrony_agent2_active.yaml` — для серверов за NAT / Firewall, где агент сам инициирует исходящее соединение на 10051 порт.
3. Привяжите импортированный шаблон к целевым хостам в разделе **Hosts**.
4. Проверьте поступление данных в **Monitoring** -> **Latest data** (фильтр `Chrony`).

---

## 📊 Состав метрик

### 1. Системные метрики синхронизации (System Tracking)
* `Chrony: Service process state` — статус процесса `chronyd` (проверяется нативно через `proc.num[chronyd]`).
* `Chrony: System time offset` — смещение локальных часов относительно эталона в секундах (`s`, float).
* `Chrony: System time offset (display)` — отформатированное строковое значение смещения с авто-выбором единиц (`µs`, `ms`, `s`) для триггеров и оповещений.
* `Chrony: RMS offset` — долгосрочное среднеквадратичное отклонение времени (`s`).
* `Chrony: Last offset` — оценочное отклонение при последнем замере (`s`).
* `Chrony: Stratum` — текущий стратум источника синхронизации.
* `Chrony: Leap status` — статус синхронизации и високосной секунды:
  * `0` — Normal (часы штатно синхронизированы);
  * `1` — Insert second;
  * `2` — Delete second;
  * `3` — Not synchronised (рассинхрон).
* `Chrony: Root delay` — сетевая задержка до первичного источника Stratum 1 (`s`).
* `Chrony: Root dispersion` — максимальная расчетная погрешность (`s`).
* `Chrony: Frequency` — дрейф частоты локального кварцевого генератора (`ppm`).
* `Chrony: Residual frequency` — остаточная погрешность частоты (`ppm`).
* `Chrony: Skew` — доверительный интервал погрешности частоты (`ppm`).
* `Chrony: Update interval` — интервал между двумя последними обновлениями часов (`s`).
* `Chrony: Reference source IP` — текущий активный сервер времени (IP/ID).

### 2. Сводные метрики источников (Sources Summary)
* `Chrony: Configured sources count` — общее число настроенных NTP-серверов в пуле.
* `Chrony: Synchronized sources count` — количество источников в статусе синхронизации (`*` или `+`).

### 3. Низкоуровневое обнаружение источников (LLD)
Zabbix автоматически обнаруживает каждый апстрим-источник времени и создает персональные элементы данных:
* `Chrony: Source [{#SOURCE_NAME}]: State` — статус источника (`*` = синхронизирован, `+` = кандидат, `-` = отсеян, `?` = недоступен, `x` = ложный источник / falseticker, `~` = высокая вариативность джиттера).
* `Chrony: Source [{#SOURCE_NAME}]: Stratum` — стратум конкретного сервера.
* `Chrony: Source [{#SOURCE_NAME}]: Reachability register` — 8-битный регистр доступности (преобразован из восьмеричной системы в диапазон 0–255: `255` = 100% ответов на последние 8 запросов, `0` = сервер недоступен).
* `Chrony: Source [{#SOURCE_NAME}]: Last sample offset` — персональное смещение относительно данного источника (`s`).
* `Chrony: Source [{#SOURCE_NAME}]: Root distance / delay` — сетевая задержка до данного источника (`s`).
* `Chrony: Source [{#SOURCE_NAME}]: Margin of error` — доверительный интервал погрешности измерения смещения (`s`).
* `Chrony: Source [{#SOURCE_NAME}]: Last sample age (last Rx)` — время в секундах с момента получения последнего пакета от источника (`s`).
* `Chrony: Source [{#SOURCE_NAME}]: Poll interval` — интервал опроса источника (log2).

---

## 🔔 Матрица триггеров и алертинга

| Важность (Severity) | Название триггера | Условие срабатывания | Описание и зависимости |
| :--- | :--- | :--- | :--- |
| **High** | `Chrony: Service process is not running` | `last(proc.num[chronyd])=0` | Служба `chronyd` остановлена или упала. |
| **High** | `Chrony: Host is not synchronised with NTP` | `last(chrony.tracking.leap_status)=3` | Потеряна связь со всеми серверами времени (зависит от работы службы). |
| **High** | `Chrony: Stratum is invalid (0 or >= 16)` | `stratum=0 or stratum>=16` | Источники не отдают валидный стратум (зависит от работы службы). |
| **High** | `Chrony: No synchronized NTP sources available` | `max(synced_count, 10m)=0` | Нет ни одного синхронизированного (`*`) или кандидатного (`+`) сервера времени на протяжении 10 минут. |
| **Warning** | `Chrony: Clock offset is excessive (> 100ms)` | `min(offset, 3m) > 0.1s or max(offset, 3m) < -0.1s` | Дрейф времени превышает 100 мс на протяжении более 3 минут (сглаживание сетевых пиков). |
| **High** | `Chrony: Clock offset is critical (> 500ms)` | `last(offset) > 0.5s or last(offset) < -0.5s` | Критическое расхождение времени. Зависит от предупреждающего триггера. |
| **Warning** | `Chrony: Root dispersion is excessive (> 100ms)` | `min(root_dispersion, 5m) > 0.1s` | Расчетная погрешность дисперсии превышает `{$CHRONY.DISPERSION.WARN}` на протяжении 5 минут. Ранний признак деградации сетевого маршрута. |
| **Warning** | `Chrony: NTP stratum increased (Stratum >= 5)` | `min(stratum, 15m)>=5 and last(stratum)<16` | Уровень стратума деградировал до 5 или выше на протяжении 15 минут. |
| **Info** | `Chrony: Leap second announcement detected` | `leap_status=1 or leap_status=2` | Вышестоящие NTP-серверы анонсировали вставку или удаление високосной секунды. |
| **Info** | `Chrony: Active reference source is flapping` | `changecount(ref_ip, 1h) > 5` | Активный сервер времени сменился более 5 раз за последний час. Признак нестабильности сетевого пути или джиттера. |
| **Warning (Отключен по умолчанию)** | `Chrony: Low number of synchronized NTP sources (< 2)` | `last(synced_count) < 2` | Число активных синхронизированных источников упало ниже порога. Можно включить в интерфейсе Zabbix. |
| **Warning (Прототип)** | `Chrony: NTP source [{#SOURCE_NAME}] is flagged as false ticker` | `last(state)="x"` | Chrony выявил, что данный сервер передает недостоверное время. |
| **Info (Прототип)** | `Chrony: NTP source [{#SOURCE_NAME}] is unreachable` | `last(reach)=0` | Все 8 последних попыток связаться с источником завершились неудачей. |
| **Info (Прототип)** | `Chrony: NTP source [{#SOURCE_NAME}] response is delayed (> 1h)` | `min(last_rx, 15m) > 3600` | От данного источника нет ответов более 1 часа. |

### Пользовательские макросы (User Macros):
Вы можете настраивать пороги прямо в шаблоне или на уровне конкретного хоста:
* `{$CHRONY.OFFSET.WARN}`: `0.1` (порог предупреждения в секундах, по умолчанию 100 мс);
* `{$CHRONY.OFFSET.CRIT}`: `0.5` (критический порог в секундах, по умолчанию 500 мс);
* `{$CHRONY.DISPERSION.WARN}`: `0.1` (порог предупреждения для корневой дисперсии в секундах, по умолчанию 100 мс);
* `{$CHRONY.SOURCES.MIN.WARN}`: `2` (минимальное число источников для опционального триггера).

---

## 📈 Визуализация и дашборды

### 1. Встроенный многостраничный дашборд шаблона (Zabbix 7.0 LTS / 7.4+)
В шаблон интегрирован современный нативный дашборд **Chrony NTP overview**, доступный сразу в дашбордах хоста:

* **Страница 1: Overview**
  * **Современные KPI-карточки**: Аккуратные карточки только со значением, выверенным размером шрифта и цветовыми порогами состояний:
    * `System time offset`: Значение отображается с точностью до 6 знаков после запятой (`-0.000519 ms`) без научной экспоненциальной записи (`E-4`) с сохранением цветовых порогов состояния (`зеленый` < 50 мс, `желтый` >= 50 мс, `красный` >= 100 мс);
    * `Reference source IP`: Полный IPv4-адрес без сокращений и обрезания троеточием;
    * `Stratum`: Целочисленное отображение (`3` вместо `3.00`) с цветовой индикацией (`зеленый` 1–3, `желтый` 4–9, `красный` 16);
    * `Leap status`: Полный статус (`Normal`, `Insert second`, `Not synchronised`) без обрезания текста.
  * **График смещения времени**: Сравнение System time offset, RMS offset и Last offset.
  * **График сетевых задержек и дисперсии**: Root delay и Root dispersion до эталона Stratum 1.
  * **График частоты и стабильности кварца**: Дрейф частоты (ppm) и расчетная погрешность (skew).
  * **График количества источников (NTP sources count)**: Динамика настроенных и активных синхронизированных серверов во времени.
  * **Сетка графиков LLD-источников**: Полноширинная сетка 2 колонки на 3 строки со смещением, задержкой и погрешностью до 6 обнаруженных серверов.

* **Страница 2: NTP Sources (Peers)**
  * Выделенная вкладка с сеткой на 6 строк и 2 колонки (до 12 графиков одновременно без пагинации) и высотой 24 единицы, где одновременно отображаются графики всех обнаруженных серверов времени. Каждый график отображает сразу 3 ключевых параметра: **Offset** (зеленый), **Delay** (красный) и **Margin of error** (синий).

### 2. Готовый дашборд для Grafana
Для тех, кто использует Grafana с официальным **плагином Zabbix** (`alexanderzobnin-zabbix-datasource`), в папке [`dashboards/grafana/`](dashboards/grafana/) подготовлен файл экспорта:
* Выпадающие списки выбора группы узлов и конкретного узла сети.
* Подробные графики и карточки ключевых метрик.
* Инструкция по импорту находится в [руководстве по Grafana](dashboards/grafana/README_RU.md).

---

## 🛠️ Диагностика и проверка с хоста

Если при проверке командой `zabbix_agent2 -t chrony.tracking` возвращается ошибка или пустое значение:

1. **Проверьте права пользователя `zabbix`**:
   ```bash
   sudo -u zabbix chronyc -c tracking
   ```
2. **Если сокет `/run/chrony/chronyd.sock` закрыт**:
   Убедитесь, что каталог `/run/chrony` имеет права на чтение:
   ```bash
   chmod o+rx /run/chrony
   chmod 666 /run/chrony/chronyd.sock
   ```
3. **Проверьте синтаксис UserParameter через агент**:
   ```bash
   zabbix_agent2 -t chrony.sources
   ```

---

## 🗑️ Удаление

Для полного удаления конфигурации с хоста:

```bash
curl -fsSL https://raw.githubusercontent.com/qwertykolea/zabbix-template-chrony/main/deploy/uninstall.sh | sudo bash
```
