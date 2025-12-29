# Foodgram

## Запуск проекта

1. Клонировать репозиторий
2. Создать файл `.env` на основе `.env.example`
3. Перейти в папку infra:
   ```bash
   docker compose up -d --build
Выполнить миграции:

bash
Копировать код
docker compose exec backend python manage.py migrate
Создать суперпользователя:

bash
Копировать код
docker compose exec backend python manage.py createsuperuser
Проект будет доступен:

http://localhost/

http://localhost/admin/

http://localhost/api/

http://localhost/api/docs/

yaml
Копировать код

---

## 5️⃣ Последняя проверка перед `git push`

Выполни:
```bash
git status
❗ Убедись, что НЕ ВИДИШЬ:

.env

media/

static/

node_modules/

Если всё чисто — смело:

bash
Копировать код
git add .
git commit -m "Foodgram backend + frontend + docker"
git push