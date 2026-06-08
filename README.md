# Zakaz DeluxMedia

MVP внутреннего кабинета `zakaz.deluxmedia.ru` для сбора заявок RSForm и заказов VirtueMart с Joomla-сайтов через персональный PHP-коннектор.

Сейчас Direct-аналитика отложена. Основной фокус проекта: клиенты, сайты, коннектор, синхронизация и работа с заказами.

## Быстрый старт

```bash
cp .env.example .env
docker compose up -d --build
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.scripts.create_admin
docker compose exec backend python -m app.scripts.create_demo_orders
```

После запуска:

- интерфейс: `http://localhost/`
- API: `http://localhost/api`
- OpenAPI: `http://localhost/api/docs`

Демо-доступ по умолчанию:

- email: `admin@example.com`
- пароль: `admin12345`

## Что готово

- FastAPI backend, PostgreSQL, SQLAlchemy 2, Alembic.
- JWT auth с bcrypt-хешами паролей.
- CRUD клиентов.
- CRUD сайтов с генерацией `site_uid`, секрета, Fernet-шифрованием и SHA-256 хешем.
- Персональная выдача `leadhub-connector.php` под Joomla 3/4/5.
- `ping`, `discover`, `sync`, `activate`, `disable`.
- Синхронизация RSForm/VirtueMart через PHP-коннектор с сохранением в `orders`.
- Worker каждые 300 секунд синхронизирует сайты в статусе `active`.
- Таблица заказов с фильтрами по дате, клиенту, сайту, источнику, статусу и поиску.
- CSV export заказов с учетом текущих фильтров.
- Карточка заказа: основные поля, товары, raw payload, комментарии, история статусов.
- Дашборд с последними заказами.
- Карточка клиента со списком сайтов и последними заказами.
- Demo seed для проверки заказов без реального Joomla-сайта.
- Docker Compose: `postgres`, `backend`, `worker`, `frontend`, `nginx`.

## Команды разработки

Backend локально:

```bash
cd backend
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Frontend локально:

```bash
cd frontend
npm install
npm run dev
```

## Администратор

Скрипт берет `ADMIN_EMAIL` и `ADMIN_PASSWORD` из `.env`.

```bash
docker compose exec backend python -m app.scripts.create_admin
```

## Тестовые заказы

Чтобы быстро проверить таблицу, карточку заказа, комментарии, статусы и CSV:

```bash
docker compose exec backend python -m app.scripts.create_demo_orders
```

Скрипт идемпотентный: его можно запускать повторно, дубли не создаются.

## Основной сценарий

1. Войти в кабинет.
2. Создать клиента.
3. Добавить сайт, выбрать Joomla 3/4/5 и источники RSForm/VirtueMart.
4. Скачать `leadhub-connector.php`.
5. Загрузить файл в корень сайта: `public_html/leadhub-connector.php`.
6. Нажать проверку подключения.
7. Выполнить discover.
8. Активировать синхронизацию.
9. Нажать Sync в списке сайтов или дождаться worker для active-сайтов.
10. Открыть заказы, отфильтровать, сменить внутренний статус, добавить комментарий, экспортировать CSV.

## Синхронизация

Ручные endpoint:

```bash
POST /api/sites/{id}/sync
POST /api/sites/{id}/sync-rsform
POST /api/sites/{id}/sync-virtuemart
```

Коннектор читает новые записи порциями до 100 штук по `since_id`.
Заказы не дублируются: уникальный ключ `site_id + source_type + external_id`.
При повторной синхронизации внутренний статус менеджера не затирается.

## Заказы

Основные endpoint:

```bash
GET /api/orders
GET /api/orders/{id}
PUT /api/orders/{id}/status
POST /api/orders/{id}/comments
GET /api/orders/export.csv
```

Поддерживаемые внутренние статусы:

- `new`
- `in_progress`
- `done`
- `cancelled`

Фильтры списка и CSV:

- `date_from`
- `date_to`
- `client_id`
- `site_id`
- `source_type`
- `internal_status`
- `search`

## Production заметки

Перед установкой на VDS обязательно задайте сильные значения:

- `JWT_SECRET_KEY`
- `FERNET_KEY`
- `POSTGRES_PASSWORD`

`FERNET_KEY` можно сгенерировать так:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
