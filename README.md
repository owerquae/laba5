# Управление библиотекой (Django + PostgreSQL + Docker)

Веб-приложение на Django для добавления, поиска и редактирования записей о книгах с поддержкой выбора хранилища (**PostgreSQL**, **JSON**, **XML**), проверкой на дубликаты, AJAX-поиском и CRUD-операциями.

## Стек технологий
- **Backend:** Python 3.11, Django, Gunicorn, WhiteNoise
- **База данных:** PostgreSQL 15 (в Docker) / SQLite (локально)
- **Frontend:** Bootstrap 5, JavaScript (Fetch API / AJAX)
- **Контейнеризация:** Docker, Docker Compose

---

## Быстрый старт (Production / Docker Compose)

1. **Клонируйте репозиторий:**
   ```bash
   git clone https://github.com
   cd laba4
   ```

2. **Создайте файл `.env` на основе `.env.example`:**
   ```bash
   cp .env.example .env
   ```
   Отредактируйте `.env`, указав надёжные `SECRET_KEY` и `POSTGRES_PASSWORD`.

3. **Соберите и запустите контейнеры:**
   ```bash
   docker-compose up -d --build
   ```
   Приложение будет доступно по адресу: `http://localhost:8000`

4. **Остановка контейнеров:**
   ```bash
   docker-compose down
   ```
   *(Данные PostgreSQL сохраняются в именованном volume `postgres_data`, а статика — в `static_volume`).*

---

## Запуск для локальной разработки (без Docker)

1. Создайте и активируйте виртуальное окружение:
   ```bash
   python -m venv venv
   source venv/bin/activate      # Linux/macOS
   venv\Scripts\activate         # Windows
   ```
2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
3. Примените миграции и запустите сервер (если переменные `POSTGRES_*` не заданы, автоматически используется SQLite):
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

---

## Миграция данных из SQLite в PostgreSQL

В проекте предусмотрено два способа переноса данных из `db.sqlite3` в контейнер с PostgreSQL:

### Способ 1: Через встроенный скрипт `migrate_sqlite_to_postgres.py`
Поместите файл `db.sqlite3` в корень проекта и выполните внутри запущенного контейнера:
```bash
docker-compose exec web python migrate_sqlite_to_postgres.py
```

### Способ 2: Через стандартные фикстуры Django (`dumpdata` / `loaddata`)
1. Выгрузите записи из локальной базы SQLite:
   ```bash
   python manage.py dumpdata books --indent 2 > books_dump.json
   ```
2. Загрузите их в PostgreSQL внутри Docker:
   ```bash
   docker-compose exec web python manage.py loaddata books_dump.json
   ```
