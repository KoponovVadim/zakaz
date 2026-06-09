# Zakaz DeluxMedia

MVP внутреннего кабинета `zakaz.deluxmedia.ru` для сбора заявок RSForm и заказов VirtueMart с Joomla-сайтов через персональный PHP-коннектор.

Сейчас Direct-аналитика отложена. Основной фокус проекта: клиенты, сайты, статусы сайтов, коннектор, синхронизация и работа с заявками внутри конкретного сайта.

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
- Пакетная синхронизация RSForm/VirtueMart через PHP-коннектор с сохранением в `orders`.
- Отдельные разделы интерфейса для всех обращений, заявок RSForm и заказов VirtueMart.
- Discover RSForm-форм и фильтр заявок по конкретной форме.
- Календарь заказов с режимами день/неделя/месяц/год, сводками и составом заказов.
- Worker каждые 300 секунд синхронизирует сайты в статусе `active`.
- Дашборд клиентов и их сайтов со статусами жив/мертв.
- Карточка клиента со списком его сайтов и статусами.
- Карточка сайта с заявками/заказами, фильтрами, сортировкой и CSV.
- Карточка заказа: основные поля, товары, raw payload, комментарии, история статусов.
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
10. Открыть сайт, увидеть его заявки/заказы, отфильтровать, сменить внутренний статус, добавить комментарий, экспортировать CSV.
11. Открыть календарь заказов, выбрать день/неделю/месяц/год и посмотреть, что было принято и что именно заказали.

## Синхронизация

Ручные endpoint:

```bash
POST /api/sites/{id}/sync
POST /api/sites/{id}/full-backfill
POST /api/sites/{id}/sync-rsform
POST /api/sites/{id}/sync-virtuemart
POST /api/sites/{id}/full-backfill-rsform
POST /api/sites/{id}/full-backfill-virtuemart
```

Коннектор читает новые записи порциями по `since_id` и параметру `limit`. По умолчанию backend отправляет `CONNECTOR_SYNC_LIMIT=500`, коннектор ограничивает максимум до `1000`.
Заказы не дублируются: уникальный ключ `site_id + source_type + external_id`.
При повторной синхронизации внутренний статус менеджера не затирается.

Backend синхронизирует RSForm и VirtueMart отдельными курсорами, чтобы источники не смешивали `since_id`. После каждой успешно сохраненной пачки курсор обновляется. Если один источник упал, второй продолжает синхронизацию.

Обычная ручная синхронизация останавливается, когда коннектор вернул `has_more=false`, пустую пачку или достигнут `CONNECTOR_SYNC_MAX_BATCHES`. Для первичной загрузки тысяч заявок используйте Full backfill: он использует увеличенный лимит пачек `CONNECTOR_SYNC_BACKFILL_MAX_BATCHES`.

Ответ `sync` коннектора содержит служебные поля:

```json
{
  "count": 500,
  "limit": 500,
  "has_more": true,
  "next_since_id": "12345"
}
```

## RSForm формы

`discover` теперь сохраняет найденные RSForm-формы в `rsform_forms`: `external_form_id`, название формы, количество отправок и время последнего обнаружения.

API форм:

```bash
GET /api/rsform/forms
GET /api/rsform/forms?client_id={id}
GET /api/rsform/forms?site_id={id}
```

Заявки RSForm сохраняют `source_form_id` и `source_form_name`. Фильтр заказов поддерживает:

```bash
GET /api/orders?source_type=rsform&site_id={site_id}&source_form_id={form_id}
```

В CSV export добавлена колонка `source_form_name`.

## Календарь заказов

Главный рабочий раздел для руководителя: `/calendar`.

Режимы:

- День — список заявок и заказов за выбранный день, сгруппированный по часам.
- Неделя — 7 дней с количеством обращений, RSForm/VirtueMart и суммой заказов.
- Месяц — календарная сетка месяца с кликом в конкретный день.
- Год — 12 месяцев, сумма, средний чек и топ-3 товара месяца.

Рабочая дата заказа считается так:

```sql
COALESCE(orders.created_at_source, orders.received_at)
```

`created_at_source` заполняется датой из Joomla-коннектора, `received_at` — датой приема записи backend. Все фильтры и агрегаты календаря работают по этой рабочей дате.

API календаря:

```bash
GET /api/calendar/summary?mode=month&date=2026-06-09
GET /api/calendar/buckets?mode=week&date=2026-06-09
GET /api/calendar/orders?date_from=2026-06-01&date_to=2026-06-30
GET /api/calendar/export.csv?date_from=2026-06-01&date_to=2026-06-30
```

Фильтры календаря:

- `client_id`
- `site_id`
- `source_type`
- `source_form_id`
- `internal_status`
- `external_status`
- `search`

`calendar/orders` возвращает состав заказа: для VirtueMart — товары из `order_items`, для RSForm — форму, основные поля заявки, сообщение и raw-поля.

## Заявки И Заказы Сайта

Основные endpoint:

```bash
GET /api/orders?site_id={id}
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

В интерфейсе заявки открываются из карточки конкретного сайта. Фильтры списка и CSV:

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

Для пакетной синхронизации можно настроить:

- `CONNECTOR_SYNC_LIMIT` — размер пачки, по умолчанию `500`, максимум на стороне коннектора `1000`.
- `CONNECTOR_SYNC_MAX_BATCHES` — максимум пачек для обычного Sync, по умолчанию `50`.
- `CONNECTOR_SYNC_BACKFILL_MAX_BATCHES` — максимум пачек для Full backfill, по умолчанию `200`.

Для сайтов на Beget backend автоматически отправляет к PHP-коннектору заголовок `Cookie: beget=begetok`, чтобы проходить HTML-челлендж хостинга и получать JSON-ответ `leadhub-connector.php`.

`FERNET_KEY` можно сгенерировать так:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
