import random
from django.core.management.base import BaseCommand
from faker import Faker
from main_app.models import Report

fake = Faker('id_ID')


class Command(BaseCommand):
    help = 'Generate fake reports'

    def add_arguments(self, parser):
        parser.add_argument('num_records', type=int)

    def handle(self, *args, **kwargs):
        num_records = kwargs['num_records']

        categories = ['Jalan Rusak', 'Sampah', 'Lampu Mati', 'Drainase', 'Keamanan']

        # ✅ SESUAI MODEL (max_length=10)
        status_choices = ['REPORTED', 'VERIFIED', 'RESOLVED']

        for _ in range(num_records):
            Report.objects.create(
                # 🔒 dibatasi biar aman
                title=fake.sentence(nb_words=4)[:100],
                category=random.choice(categories),
                description=fake.text(),
                location=fake.city()[:100],
                status=random.choice(status_choices),
            )

        self.stdout.write(
            self.style.SUCCESS(f'Berhasil membuat {num_records} data!')
        )