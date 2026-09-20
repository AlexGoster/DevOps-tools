# DevOps Tools

CLI утилиты для серверного администрирования и DevOps задач.

## Инструменты

- **server_health** — проверка состояния сервера
- **backup** — автоматические бэкапы
- **deploy** — деплой приложений
- **log_analyzer** — анализ лог файлов
- **ssl_checker** — проверка SSL сертификатов
- **docker_manager** — управление Docker контейнерами

## Установка

```bash
pip install -r requirements.txt
python tools/cli.py --help
```

## Использование

```bash
python tools/cli.py health --host example.com
python tools/cli.py backup --source /var/www --dest /backup
python tools/cli.py deploy --repo /app --branch main
python tools/cli.py logs --file /var/log/nginx/access.log --errors-only
python tools/cli.py ssl --domain example.com
```

MIT License - AlexGoster


Last updated: 2026-09-20
