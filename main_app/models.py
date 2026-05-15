from django.db import models
from django.conf import settings


class Report(models.Model):

    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('REPORTED', 'Dilaporkan'),
        ('VERIFIED', 'Diverifikasi'),
        ('IN_PROGRESS', 'Diproses'),
        ('RESOLVED', 'Diselesaikan'),
    ]

    title = models.CharField(
        max_length=100,
        verbose_name='Judul'
    )

    category = models.CharField(
        max_length=50,
        verbose_name='Kategori'
    )

    description = models.TextField(
        verbose_name='Deskripsi'
    )

    location = models.CharField(
        max_length=100,
        verbose_name='Lokasi'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT',
        verbose_name='Status'
    )

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reports'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.title