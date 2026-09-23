# DevOps Tools

Набор CLI-утилит для серверного администрирования и DevOps задач.

## Описание

Python-скрипты для автоматизации рутинных задач сисадмина: мониторинг, бэкапы, анализ логов, проверка SSL.

## Технологии

- **Язык:** Python 3.11+
- **CLI:** Click
- **Мониторинг:** psutil, requests
- **SSH:** paramiko
- **Уведомления:** smtplib, requests

## Инструменты

| Инструмент | Описание |
|------------|----------|
| `health` | Проверка состояния сервера (CPU, RAM, диск) |
| `backup` | Автоматические бэкапы по расписанию |
| `logs` | Анализ лог-файлов, поиск ошибок |
| `ssl` | Проверка SSL-сертификатов |
| `deploy` | Деплой приложений |
| `docker` | Управление Docker-контейнерами |

## Установка и запуск

```bash
# Клонирование
git clone https://github.com/AlexGoster/DevOps-tools.git
cd DevOps-tools

# Установка зависимостей
pip install -r requirements.txt

# Помощь
python tools/cli.py --help
```

## Примеры использования

```bash
# Проверка здоровья сервера
python tools/cli.py health --host example.com

# Бэкап директории
python tools/cli.py backup --source /var/www --dest /backup

# Анализ логов (только ошибки)
python tools/cli.py logs --file /var/log/nginx/access.log --errors-only

# Проверка SSL-сертификата
python tools/cli.py ssl --domain example.com

# Деплой приложения
python tools/cli.py deploy --repo /app --branch main
```

## Структура проекта

```
DevOps-tools/
├── tools/
│   ├── cli.py           # Главный CLI
│   ├── server_health.py # Мониторинг сервера
│   ├── backup.py        # Бэкапы
│   ├── log_analyzer.py  # Анализ логов
│   ├── ssl_checker.py   # Проверка SSL
│   ├── deploy.py        # Деплой
│   └── docker_manager.py
├── utils/
│   ├── ssh.py           # SSH-клиент
│   └── notifications.py # Уведомления
├── tests/
├── requirements.txt
└── README.md
```

## Сценарии использования

1. **Мониторинг сервера** — автоматическая проверка CPU/RAM/диска и уведомления
2. **Бэкапы** — ежедневное резервное копирование критичных данных
3. **Анализ логов** — быстрый поиск ошибок в больших логах
4. **SSL-проверка** — мониторинг срока действия сертификатов

## Что я изучила

- Работа с subprocess и системными вызовами
- SSH-подключения через paramiko
- Мониторинг системы (psutil)
- CLI-утилиты на Click

## License

MIT License - AlexGoster


Last updated: 2026-09-20


Last updated: 2026-09-20


Last updated: 2026-09-20


Last updated: 2026-09-23
