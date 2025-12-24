# management/commands/load_data.py
import csv
import json
import os
from django.core.management.base import BaseCommand
from recipes.models import Tag, Ingredient

class Command(BaseCommand):
    help = 'Load data from CSV or JSON files'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            type=str,
            default='json',
            choices=['csv', 'json'],
            help='Format of the data file (csv or json)'
        )

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
    
        self.stdout.write(self.style.SUCCESS(
            f'Successfully created {count} tags'
        ))
    
    def handle(self, *args, **options):
        # Сначала создаем теги
        self.create_tags()
    
        data_dir = os.path.join('..', 'data')
    
        if options['format'] == 'csv':
            self.load_csv_data(data_dir)
        else:
            self.load_json_data(data_dir)
    
    def load_csv_data(self, data_dir):
        csv_file = os.path.join(data_dir, 'ingredients.csv')
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            
            for row in reader:
                name = row['name'].strip()
                measurement_unit = row['measurement_unit'].strip()
                
                ingredient, created = Ingredient.objects.get_or_create(
                    name=name,
                    measurement_unit=measurement_unit
                )
                
                if created:
                    count += 1
            
            self.stdout.write(self.style.SUCCESS(
                f'Successfully loaded {count} ingredients from CSV'
            ))
    
    def load_json_data(self, data_dir):
        json_file = os.path.join(data_dir, 'ingredients.json')
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            count = 0
            
            for item in data:
                name = item['name'].strip()
                measurement_unit = item['measurement_unit'].strip()
                
                ingredient, created = Ingredient.objects.get_or_create(
                    name=name,
                    measurement_unit=measurement_unit
                )
                
                if created:
                    count += 1
            
            self.stdout.write(self.style.SUCCESS(
                f'Successfully loaded {count} ingredients from JSON'
            ))