# management/commands/load_initial_data.py
import os
import csv
import json
from django.core.management.base import BaseCommand
from django.conf import settings
from recipes.models import Tag, Ingredient
from users.models import User

class Command(BaseCommand):
    help = 'Load initial data (tags and ingredients)'
    
    def handle(self, *args, **options):
        # 1. Создаем теги
        self.create_tags()
        
        # 2. Загружаем ингредиенты из JSON
        self.load_ingredients_from_json()
        
        # 3. Создаем тестового пользователя
        self.create_test_user()
        
        self.stdout.write(self.style.SUCCESS('All data loaded successfully!'))
    
    def create_tags(self):
        tags_data = [
            {'name': 'Завтрак', 'color': '#FF0000', 'slug': 'breakfast'},
            {'name': 'Обед', 'color': '#00FF00', 'slug': 'lunch'},
            {'name': 'Ужин', 'color': '#0000FF', 'slug': 'dinner'},
            {'name': 'Десерт', 'color': '#FFA500', 'slug': 'dessert'},
            {'name': 'Напиток', 'color': '#800080', 'slug': 'drink'},
        ]
        
        count = 0
        for tag_data in tags_data:
            tag, created = Tag.objects.get_or_create(
                name=tag_data['name'],
                defaults={'color': tag_data['color'], 'slug': tag_data['slug']}
            )
            if created:
                count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Created {count} tags'))
    
    def load_ingredients_from_json(self):
        # Путь к файлу ingredients.json
        json_path = os.path.join('..', 'data', 'ingredients.json')
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                ingredients_data = json.load(f)
        except FileNotFoundError:
            self.stdout.write(self.style.WARNING(f'File {json_path} not found'))
            # Попробуем загрузить из CSV
            self.load_ingredients_from_csv()
            return
        
        count = 0
        for item in ingredients_data:
            name = item.get('name', '').strip()
            measurement_unit = item.get('measurement_unit', '').strip()
            
            if name and measurement_unit:
                ingredient, created = Ingredient.objects.get_or_create(
                    name=name,
                    measurement_unit=measurement_unit
                )
                if created:
                    count += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'Loaded {count} ingredients from JSON'
        ))
    
    def load_ingredients_from_csv(self):
        # Путь к файлу ingredients.csv
        csv_path = os.path.join('..', 'data', 'ingredients.csv')
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                count = 0
                
                for row in reader:
                    name = row.get('name', '').strip()
                    measurement_unit = row.get('measurement_unit', '').strip()
                    
                    if name and measurement_unit:
                        ingredient, created = Ingredient.objects.get_or_create(
                            name=name,
                            measurement_unit=measurement_unit
                        )
                        if created:
                            count += 1
                
                self.stdout.write(self.style.SUCCESS(
                    f'Loaded {count} ingredients from CSV'
                ))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(
                f'Neither JSON nor CSV file found in ../data/'
            ))
    
    def create_test_user(self):
        # Создаем тестового пользователя для рецептов
        try:
            user, created = User.objects.get_or_create(
                email='test@example.com',
                defaults={
                    'username': 'testuser',
                    'first_name': 'Test',
                    'last_name': 'User',
                    'password': 'testpass123'  # Пароль будет хэширован
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()
                self.stdout.write(self.style.SUCCESS('Created test user'))
            else:
                self.stdout.write(self.style.WARNING('Test user already exists'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating test user: {e}'))