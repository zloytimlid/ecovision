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
