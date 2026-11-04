# Быстрое развертывание через Ansible

Плейбук автоматизирует раскатку конфигурации `chrony.conf` на любое количество серверов с Zabbix Agent 2.

## Инструкция по запуску:

1. Отредактируйте файл `inventory.ini.example`, добавив ваши серверы, и сохраните как `inventory.ini`:
   ```bash
   cp inventory.ini.example inventory.ini
   nano inventory.ini
   ```

2. Запустите плейбук:
   ```bash
   ansible-playbook -i inventory.ini playbook.yml
   ```

3. Плейбук автоматически:
   - Проверит установку и статус `chrony`.
   - Создаст каталог `/etc/zabbix/zabbix_agent2.d/` при необходимости.
   - Скопирует файл `chrony.conf`.
   - Перезапустит службу `zabbix-agent2`.
   - Проверит работоспособность метрики `chrony.tracking` и выведет результат в консоль.
