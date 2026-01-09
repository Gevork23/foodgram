set -e

if [ -n "$DB_HOST" ]; then
  echo "Waiting for database..."
  while ! nc -z "$DB_HOST" "$DB_PORT"; do
    sleep 0.2
  done
  echo "Database port is open"
fi

echo "Running migrations..."
until python manage.py migrate --noinput; do
  echo "Migrate failed, retrying in 1s..."
  sleep 1
done

echo "Loading initial data..."
python manage.py load_data || true

echo "Creating superuser if not exists..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()

email = '${DJANGO_SUPERUSER_EMAIL}'
username = '${DJANGO_SUPERUSER_USERNAME}' or 'admin'
first_name = '${DJANGO_SUPERUSER_FIRST_NAME}' or 'admin'
last_name = '${DJANGO_SUPERUSER_LAST_NAME}' or 'admin'
password = '${DJANGO_SUPERUSER_PASSWORD}' or 'admin'

if email and not User.objects.filter(email=email).exists():
    User.objects.create_superuser(
        email=email,
        username=username,
        first_name=first_name,
        last_name=last_name,
        password=password,
    )
    print('Superuser created:', email)
else:
    print('Superuser already exists (or email not set):', email)
"

echo "Collect static..."
python manage.py collectstatic --noinput
cp -r /app/static/. /app_static/ 2>/dev/null || true

exec gunicorn foodgram.wsgi:application --bind 0.0.0.0:8000 --workers=3
