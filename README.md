# Foodgram

Foodgram — это веб-сервис для публикации и обмена рецептами.
Пользователи могут создавать рецепты, добавлять их в избранное,
подписываться на авторов и формировать список покупок.

---

## Автор

**Геворк (Gevork23)**  
GitHub: [https://github.com/Gevork23](https://github.com/Gevork23)

---

## Стек технологий

- Python 3.12
- Django
- Django REST Framework
- PostgreSQL
- Docker / Docker Compose
- Nginx
- Gunicorn
- GitHub Actions (CI/CD)

---

## Локальный запуск проекта (Docker)

### 1. Клонировать репозиторий
```
git clone https://github.com/Gevork23/foodgram.git
cd foodgram
```

### 2. Создать файл .env
Пример переменных окружения:
```
DEBUG=False
SECRET_KEY=django-secret-key
ALLOWED_HOSTS=127.0.0.1,localhost

POSTGRES_DB=foodgram
POSTGRES_USER=foodgram
POSTGRES_PASSWORD=foodgram
DB_HOST=db
DB_PORT=5432
```
### 3. Запустить контейнеры

docker compose -f docker-compose.production.yml up -d --build

### 4. Выполнить миграции

docker compose exec backend python manage.py migrate
### 5. Загрузить ингредиенты и теги

docker compose exec backend python manage.py load_data
### 6. Создать суперпользователя (если нужно)

docker compose exec backend python manage.py createsuperuser

Данные администратора
- Email: admin@example.com
- Пароль: admin

#### Панель администратора доступна по адресу:
/admin/

#### Домен проекта
https://oski.myftp.biz

### Документация API

#### Swagger / OpenAPI:
/docs/

#### Redoc:
/docs/redoc.html

#### CI/CD
Проект использует GitHub Actions:
- проверка кода (flake8, black, isort)
- сборка Docker-образов
- публикация в Docker Hub
- автоматический деплой на сервер
