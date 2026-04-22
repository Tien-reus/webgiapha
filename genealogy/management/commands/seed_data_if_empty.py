from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand, call_command

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

        fixture_path = Path(settings.BASE_DIR) / 'genealogy' / 'data' / 'seed.json'
        if not fixture_path.exists():
            self.stdout.write(self.style.WARNING('Seed skipped: genealogy/data/seed.json not found.'))
            return

        call_command('loaddata', str(fixture_path))
        self.stdout.write(self.style.SUCCESS('Seed loaded from genealogy/data/seed.json'))
