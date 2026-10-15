# EcoVision

Веб-приложение (mobile-first): по фото предмета определяет тип отхода и подсказывает, куда его выбросить.

**Фото → тип отхода → куда выбрасывать.** Распознавание — модель Roboflow (Hosted API),
справочник категорий, история и обратная связь — Django + SQLite, интерфейс — React.

## Аккаунты

Пользоваться приложением можно без регистрации: история тогда хранится за устройством
(анонимный `X-Client-Id`). Если зарегистрироваться или войти (вкладка «Профиль»):

- история привязывается к аккаунту и видна с любого устройства;
- распознавания, сделанные на этом устройстве до входа, переносятся в аккаунт;
- после выхода анонимно они больше не видны.

Вход — по имени пользователя и паролю (имя без учёта регистра), пароль проверяется стандартными
валидаторами Django. API использует токен: `Authorization: Token <key>`. Один токен на пользователя,
поэтому «Выйти» завершает сессию на всех устройствах. Вход и регистрация ограничены 10 попытками
в минуту с одного IP (`AUTH_RATE` в `.env`).

```
[React SPA] --REST--> [Django + DRF] --HTTPS--> [Roboflow API]
                            |
                         [SQLite] + media/
```

## Требования

- Python 3.11+
- Node.js 20+
- Аккаунт Roboflow: API-ключ и ID модели

## Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate            # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env           # macOS/Linux: cp .env.example .env
```

Заполните в `backend/.env`:

| Переменная | Что указать |
|---|---|
| `DJANGO_SECRET_KEY` | любая длинная случайная строка |
| `ROBOFLOW_API_KEY` | Private API Key из настроек Roboflow |
| `ROBOFLOW_MODEL_ID` | ID модели, можно сразу с версией: `waste-bd0et/10` |
| `ROBOFLOW_MODEL_VERSION` | версия, если не указана в `ROBOFLOW_MODEL_ID` |
| `ROBOFLOW_API_URL` | `https://serverless.roboflow.com` (или `detect.roboflow.com` / `classify.roboflow.com`) |
| `ROBOFLOW_MODEL_TYPE` | `object-detection` или `classification` |

Ключ Roboflow хранится только в `backend/.env` — он не попадает во фронтенд, git и логи.

```bash
python manage.py migrate
python manage.py seed_waste       # 10 категорий отходов + маппинг классов модели
python manage.py createsuperuser  # для админки
python manage.py runserver        # http://localhost:8000
```

- Админка: http://localhost:8000/admin/ — категории, цвета контейнеров, маппинг классов модели,
  история распознаваний с фото, обратная связь (фильтр «верно / неверно»).
- Проверка: http://localhost:8000/api/health/ → `{"status": "ok", "model_configured": true}`.
- `seed_waste` не затирает правки из админки; `seed_waste --overwrite` возвращает значения по умолчанию.

### Тесты

```bash
cd backend
python -m pytest -q
```

Тесты не обращаются к Roboflow и работают без интернета.

## Frontend

```bash
cd frontend
npm install
copy .env.example .env           # macOS/Linux: cp .env.example .env
npm run dev                      # http://localhost:5173
```

`VITE_API_URL` в `frontend/.env` — адрес API (по умолчанию `http://localhost:8000/api`).

### Проверка с телефона в локальной сети

1. Запустите backend на всех интерфейсах: `python manage.py runserver 0.0.0.0:8000`.
2. В `backend/.env` добавьте IP компьютера в `DJANGO_ALLOWED_HOSTS` и `http://<IP>:5173` в `CORS_ALLOWED_ORIGINS`.
3. В `frontend/.env`: `VITE_API_URL=http://<IP>:8000/api`, затем `npm run dev -- --host`.
4. Откройте на телефоне `http://<IP>:5173`.

## Модель и маппинг классов

Сейчас подключена модель `waste-bd0et/10` (детекция). Её классы и категории:

| Класс модели | Категория |
|---|---|
| plastic | Пластик |
| paper, cardboard | Бумага и картон |
| glass | Стекло |
| metal | Металл |
| biological | Органика |
| Electronics | Электроника |
| clothes, shoes | Одежда и обувь |

Маппинг редактируется в админке (на странице категории). Если модель вернёт класс без маппинга,
пользователь увидит «нет правил», а в логе сервера появится предупреждение с именем класса.
Начальные значения — в `backend/catalog/seed_data.py`.

## API

| Метод | URL | Описание |
|---|---|---|
| POST | `/api/recognize/` | Загрузить фото (`multipart/form-data`, поле `image`) |
| GET | `/api/recognitions/?page=1` | История текущего устройства |
| GET / DELETE | `/api/recognitions/{id}/` | Детали / удаление (вместе с фото) |
| POST | `/api/recognitions/{id}/feedback/` | Оценка результата |
| GET | `/api/categories/?search=` | Справочник категорий |
| GET | `/api/categories/{slug}/` | Категория |
| GET | `/api/health/` | Состояние сервиса |
| POST | `/api/auth/register/` | Регистрация `{username, password}` → `{token, user}` |
| POST | `/api/auth/login/` | Вход → `{token, user}` |
| POST | `/api/auth/logout/` | Выход (удаляет токен) |
| GET | `/api/auth/me/` | Текущий пользователь |

Все запросы передают заголовок `X-Client-Id` — анонимный ID устройства (создаётся фронтендом),
и `Authorization: Token <key>`, если пользователь вошёл.
Ошибки возвращаются в формате `{"error": {"code": "...", "message": "..."}}`.
Распознавание ограничено 30 запросами в минуту на устройство (`RECOGNIZE_RATE` в `.env`).

## Деплой на Vercel

Из репозитория создаются **два проекта Vercel**: фронтенд (папка `frontend`) и бэкенд (папка `backend`).
У serverless-функций нет постоянного диска, поэтому бэкенду нужна база Postgres (например,
[Neon](https://neon.tech) или [Supabase](https://supabase.com), есть бесплатные тарифы). Фото хранятся
в этой же базе (`MEDIA_STORAGE=db`) и отдаются Django по адресу `/media/...`; счётчики лимитов запросов —
тоже в базе (таблица `django_cache`), отдельный Redis не нужен.

### 1. База

Создайте базу Postgres и скопируйте строку подключения (`postgresql://…?sslmode=require`).
Один раз подготовьте её с локального компьютера:

```bash
cd backend
venv\Scripts\activate
set DATABASE_URL=postgresql://...          # macOS/Linux: export DATABASE_URL=...
python manage.py migrate
python manage.py createcachetable
python manage.py seed_waste
python manage.py createsuperuser
```

После изменений моделей повторяйте `migrate` так же.

### 2. Бэкенд

Vercel → Add New → Project → этот репозиторий, **Root Directory: `backend`**, Framework Preset: Other.
Точка входа — `backend/api/index.py`, маршрутизация — `backend/vercel.json`. Переменные окружения:

| Переменная | Значение |
|---|---|
| `DJANGO_SECRET_KEY` | длинная случайная строка |
| `DJANGO_DEBUG` | `False` |
| `DATABASE_URL` | строка подключения Postgres |
| `MEDIA_STORAGE` | `db` |
| `MAX_UPLOAD_MB` | `4` (функции Vercel принимают запросы до 4.5 МБ) |
| `CORS_ALLOWED_ORIGINS` | адрес фронтенда, например `https://ecovision.vercel.app` |
| `CORS_ALLOWED_ORIGIN_REGEXES` | необязательно: `^https://ecovision-[a-z0-9-]+\.vercel\.app$` для preview-деплоев |
| `ROBOFLOW_API_KEY`, `ROBOFLOW_API_URL`, `ROBOFLOW_MODEL_ID`, `ROBOFLOW_MODEL_TYPE` | как в локальном `.env` |
| `TIME_ZONE` | например `Europe/Moscow` |

Адреса проекта `*.vercel.app` добавляются в `ALLOWED_HOSTS` и `CSRF_TRUSTED_ORIGINS` автоматически;
для своего домена укажите `DJANGO_ALLOWED_HOSTS` и `CSRF_TRUSTED_ORIGINS`.
Проверка: `https://<бэкенд>.vercel.app/api/health/`, админка — `/admin/`.

### 3. Фронтенд

Vercel → Add New → Project → этот же репозиторий, **Root Directory: `frontend`**, Framework Preset: Vite.
Переменные окружения:

| Переменная | Значение |
|---|---|
| `VITE_API_URL` | `https://<бэкенд>.vercel.app/api` |
| `VITE_MAX_UPLOAD_MB` | `4` |

`frontend/vercel.json` перенаправляет все пути на `index.html`, чтобы ссылки вроде `/history` открывались после обновления страницы.

### Ограничения

- Первый запрос после простоя медленнее: холодный старт функции плюс ответ Roboflow.
- Фото хранятся в базе, поэтому следите за её размером (одно фото после сжатия — 100–300 КБ).
