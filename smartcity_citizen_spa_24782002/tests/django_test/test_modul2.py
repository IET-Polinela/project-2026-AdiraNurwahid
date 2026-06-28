from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from main_app.models import Report

User = get_user_model()

class PrivacyAndDataHidingTests(APITestCase):

    def setUp(self):
        self.warga_a = User.objects.create_user(
            username='warga_a',
            email='warga_a@test.com',
            password='Password123!',
            role='member'
        )
        self.warga_b = User.objects.create_user(
            username='warga_b',
            email='warga_b@test.com',
            password='Password123!',
            role='member'
        )

        self.draft_milik_b = Report.objects.create(
            title='Draf Rahasia Warga B',
            category='Infrastruktur',
            description='Ini adalah draf yang belum diajukan.',
            location='Lokasi Rahasia',
            status='DRAFT',
            reporter=self.warga_b,
        )

        self.laporan_publik_a = Report.objects.create(
            title='Jalan Berlubang di Depan Kampus',
            category='Infrastruktur',
            description='Ada lubang besar yang membahayakan pengendara.',
            location='Jl. Soekarno Hatta',
            status='REPORTED',
            reporter=self.warga_a,
        )

        self.laporan_publik_b = Report.objects.create(
            title='Sampah Menumpuk di Trotoar',
            category='Kebersihan',
            description='Sampah tidak diangkut selama seminggu.',
            location='Jl. Gatot Subroto',
            status='REPORTED',
            reporter=self.warga_b,
        )

    def test_PRIV_01_feed_kota_menyembunyikan_identitas_reporter(self):
        """
        [PRIV-01] Feed kota menyembunyikan identitas reporter.
        reporter_name harus 'Warga Anonim' untuk semua laporan di feed.
        """
        self.client.force_authenticate(user=self.warga_a)
        response = self.client.get('/api/report/?tab=feed')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data.get('results', [])
        self.assertTrue(
            len(results) > 0,
            "Feed kota seharusnya memiliki minimal 1 laporan"
        )

        for laporan in results:
            self.assertEqual(
                laporan['reporter_name'],
                'Warga Anonim',
                f"Laporan '{laporan['title']}' seharusnya menampilkan reporter "
                f"sebagai 'Warga Anonim', tetapi menampilkan '{laporan['reporter_name']}'"
            )

    def test_PRIV_02_laporan_saya_menampilkan_nama_asli(self):
        """
        [PRIV-02] Tab my_reports menampilkan nama asli reporter.
        """
        self.client.force_authenticate(user=self.warga_a)
        response = self.client.get('/api/report/?tab=my_reports')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data.get('results', [])
        self.assertTrue(len(results) > 0, "Harus ada laporan milik Warga A")

        for laporan in results:
            self.assertEqual(
                laporan['reporter_name'],
                'warga_a',
                f"Pada tab 'my_reports', reporter_name seharusnya menampilkan "
                f"username asli 'warga_a', bukan '{laporan['reporter_name']}'"
            )

    def test_PRIV_03_tidak_bisa_baca_draf_orang_lain(self):
        """
        [PRIV-03] Warga A tidak bisa membaca detail draf milik Warga B.
        Sistem harus return 404 karena draf orang lain tidak ada dalam queryset.
        """
        # Autentikasi sebagai Warga A
        self.client.force_authenticate(user=self.warga_a)

        # Coba akses detail draf milik Warga B
        url = f'/api/report/{self.draft_milik_b.pk}/'
        response = self.client.get(url)

        # Harus 404 - draf orang lain tidak terlihat
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            "Draf milik Warga B seharusnya tidak terlihat oleh Warga A (HTTP 404)"
        )

    def test_PRIV_04_tidak_bisa_modifikasi_draf_orang_lain(self):
        """
        [PRIV-04] Warga A tidak bisa memodifikasi draf milik Warga B.
        Harus return 404 karena objek tidak ada di queryset Warga A.
        """
        # Autentikasi sebagai Warga A
        self.client.force_authenticate(user=self.warga_a)

        # Coba PUT ke draf milik Warga B
        url = f'/api/report/{self.draft_milik_b.pk}/'
        payload = {
            'title': 'Judul Diubah Oleh Warga A',
            'category': 'Infrastruktur',
            'description': 'Deskripsi diubah.',
            'location': 'Lokasi diubah',
            'status': 'DRAFT',
        }
        response = self.client.put(url, payload, format='json')

        # Harus 404 - tidak bisa menemukan objek
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
            "Modifikasi draf orang lain seharusnya gagal dengan HTTP 404"
        )

        # Pastikan data asli tidak berubah
        self.draft_milik_b.refresh_from_db()
        self.assertEqual(
            self.draft_milik_b.title,
            'Draf Rahasia Warga B',
            "Judul draf asli tidak boleh berubah"
        )
