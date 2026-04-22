from pathlib import Path

from django.conf import settings
from django.core.management import BaseCommand, call_command

from genealogy.models import FamilyMember


class Command(BaseCommand):
    help = 'Load bundled initial genealogy data when database is empty.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Load fixture even when family data already exists.',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        if FamilyMember.objects.exists() and not force:
            self.stdout.write(self.style.SUCCESS('Seed skipped: family data already exists.'))
            return

        fixture_path = Path(settings.BASE_DIR) / 'genealogy' / 'data' / 'initial_data.json'
        if not fixture_path.exists():
            self.stdout.write(self.style.WARNING('Seed skipped: fixture file not found.'))
            return

        call_command('loaddata', str(fixture_path))
        self.stdout.write(self.style.SUCCESS('Seed completed: initial family data loaded.'))
