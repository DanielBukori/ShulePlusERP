from django.core.management.base import BaseCommand
from django.db import transaction

from shule_core.models import AcademicResult


class Command(BaseCommand):
    help = 'Backfill A-Level result combinations from each student.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Report eligible records without changing them.',
        )

    def handle(self, *args, **options):
        results = AcademicResult.objects.filter(
            school_class__level='A',
            subject__level='A',
            combination__isnull=True,
            student__combination__isnull=False,
        )
        result_count = results.count()

        if options['dry_run']:
            self.stdout.write(f'{result_count} A-Level results can be updated.')
            return

        with transaction.atomic():
            batch = []
            for result in results.select_related('student').iterator(chunk_size=500):
                result.combination_id = result.student.combination_id
                batch.append(result)
                if len(batch) == 500:
                    AcademicResult.objects.bulk_update(batch, ['combination'])
                    batch = []

            if batch:
                AcademicResult.objects.bulk_update(batch, ['combination'])

        self.stdout.write(self.style.SUCCESS(
            f'Updated combinations on {result_count} A-Level results.'
        ))
