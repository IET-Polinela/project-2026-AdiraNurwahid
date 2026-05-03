from django.db import models

class Report(models.Model):
    STATUS_CHOICES = [
        ('REPORTED', 'Dilaporkan'),
        ('VERIFIED', 'Diverifikasi'),
        ('RESOLVED', 'Diselesaikan'),
    ]

    title = models.CharField(max_length=100, verbose_name='Judul')
    category = models.CharField(max_length=50, verbose_name='Kategori')
    description = models.TextField(verbose_name='Deskripsi')
    location = models.CharField(max_length=100, verbose_name='Lokasi')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='REPORTED', verbose_name='Status')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title