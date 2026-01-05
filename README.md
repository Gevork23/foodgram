# Foodgram

## Запуск проекта

1. Клонировать репозиторий
2. Создать файл `.env` на основе `.env.example`
3. Перейти в папку infra:
   ```bash
   docker compose up -d --build
   ```
Выполнить миграции:

docker compose exec backend python manage.py migrate
Создать суперпользователя:


docker compose exec backend python manage.py createsuperuser
Проект будет доступен:

http://localhost/

http://localhost/admin/

http://localhost/api/

http://localhost/api/docs/

```
cd infra
docker compose down -v
docker compose up -d --build
```