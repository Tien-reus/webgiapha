from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand, call_command
from django.db import connection

from genealogy.models import FamilyMember


class Command(BaseCommand):
    help = 'Load local seed data into database when FamilyMember table is empty.'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Force load fixture even if data exists.')

    def handle(self, *args, **options):
        force = options.get('force', False)
        if FamilyMember.objects.exists() and not force:
            self.stdout.write(self.style.SUCCESS('Seed skipped: FamilyMember already has data.'))
            return

        self._ensure_legacy_branch_default()

        fixture_path = Path(settings.BASE_DIR) / 'genealogy' / 'data' / 'seed.json'
        if not fixture_path.exists():
            self.stdout.write(self.style.WARNING('Seed skipped: genealogy/data/seed.json not found.'))
            return

        call_command('loaddata', str(fixture_path))
        self.stdout.write(self.style.SUCCESS('Seed loaded from genealogy/data/seed.json'))

    def _ensure_legacy_branch_default(self):
        # Some older deployments created a non-null `branch` column that is no longer
        # present in the current model. In that case, inserts from fixture fail unless
        # database-level default is set.
        if connection.vendor != 'postgresql':
            return

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'genealogy_familymember'
                  AND column_name = 'branch'
                LIMIT 1
                """
            )
            has_branch = cursor.fetchone() is not None
            if not has_branch:
                return

            cursor.execute(
                """
                ALTER TABLE public.genealogy_familymember
                ALTER COLUMN branch SET DEFAULT 'canh_truong'
                """
            )
