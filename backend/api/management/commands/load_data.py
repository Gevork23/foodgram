# backend/api/management/commands/load_data.py
import csv
import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from api.models import Ingredient, Tag


DEFAULT_TAGS = [
    {"name": "Завтрак", "slug": "breakfast"},
    {"name": "Обед", "slug": "lunch"},
    {"name": "Ужин", "slug": "dinner"},
]


class Command(BaseCommand):
    help = "Load initial data: ingredients (csv/json) + default tags"

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv",
            dest="csv_path",
            default=None,
            help="Path to ingredients.csv (optional). If not provided, tries ../data/ingredients.csv and data/ingredients.csv",
        )
        parser.add_argument(
            "--json",
            dest="json_path",
            default=None,
            help="Path to ingredients.json (optional). If not provided, tries ../data/ingredients.json and data/ingredients.json",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        # manage.py лежит в backend/
        # поэтому "корень проекта" = backend/..
        backend_dir = Path.cwd().resolve()
        project_root = backend_dir.parent

        # --- TAGS ---
        created_tags = 0
        for t in DEFAULT_TAGS:
            _, created = Tag.objects.get_or_create(
                slug=t["slug"],
                defaults={"name": t["name"]},
            )
            created_tags += int(created)
        self.stdout.write(self.style.SUCCESS(
            f"Tags: created {created_tags}, total {Tag.objects.count()}"
        ))

        # --- INGREDIENTS PATHS ---
        csv_candidates = []
        json_candidates = []

        if options["csv_path"]:
            csv_candidates.append(Path(options["csv_path"]))
        if options["json_path"]:
            json_candidates.append(Path(options["json_path"]))

        # авто-поиск в двух типичных местах:
        # 1) ../data/... (когда запускаем из backend/)
        # 2) data/...    (когда запускаем из корня проекта)
        csv_candidates += [
            project_root / "data" / "ingredients.csv",
            backend_dir / "data" / "ingredients.csv",
        ]
        json_candidates += [
            project_root / "data" / "ingredients.json",
            backend_dir / "data" / "ingredients.json",
        ]

        csv_path = self._first_existing(csv_candidates)
        json_path = self._first_existing(json_candidates)

        if csv_path:
            created = self._load_csv(csv_path)
            self.stdout.write(self.style.SUCCESS(
                f"Ingredients loaded from CSV: +{created}, total {Ingredient.objects.count()}"
            ))
            return

        if json_path:
            created = self._load_json(json_path)
            self.stdout.write(self.style.SUCCESS(
                f"Ingredients loaded from JSON: +{created}, total {Ingredient.objects.count()}"
            ))
            return

        self.stdout.write(self.style.WARNING(
            "No ingredients file found (CSV/JSON). Checked:\n"
            + "\n".join([str(p.resolve()) for p in (csv_candidates + json_candidates)])
        ))

    def _first_existing(self, paths):
        for p in paths:
            try:
                pp = p.resolve()
            except Exception:
                pp = p
            if pp.exists() and pp.is_file():
                return pp
        return None

    def _load_csv(self, path: Path) -> int:
        created = 0
        with path.open("r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or len(row) < 2:
                    continue
                name = row[0].strip()
                unit = row[1].strip()
                if not name or not unit:
                    continue
                _, was_created = Ingredient.objects.get_or_create(
                    name=name, measurement_unit=unit
                )
                created += int(was_created)
        return created

    def _load_json(self, path: Path) -> int:
        created = 0
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        for item in data:
            name = (item.get("name") or "").strip()
            unit = (item.get("measurement_unit") or "").strip()
            if not name or not unit:
                continue
            _, was_created = Ingredient.objects.get_or_create(
                name=name, measurement_unit=unit
            )
            created += int(was_created)
        return created
