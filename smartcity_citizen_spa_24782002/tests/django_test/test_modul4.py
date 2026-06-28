from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from main_app.models import Report

User = get_user_model()

class CRUDAndValidationTests(APITestCase):

    def setUp(self):
        self.warga = User.objects.create_user(
            username='warga_crud',
            email='warga_crud@test.com',
            password='TestPass123!',
            role='member'
        )
        self.client.force_authenticate(user=self.warga)

    def test_FT_01_buat_laporan_dengan_data_lengkap(self):
        """
        [FT-01] Membuat laporan baru dengan data lengkap.
        Harus return HTTP 201 Created dan data tersimpan di DB.
        """
        url = reverse('report-list')

        payload = {
            'title': 'Laporan Lengkap Baru',
            'category': 'Infrastruktur',
            'description': 'Deskripsi lengkap laporan.',
            'location': 'Jl. Merdeka No. 1',
        }

        response = self.client.post(url, payload, format='json')

        # Verifikasi HTTP 201 Created
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            "Pembuatan laporan dengan data lengkap seharusnya berhasil (HTTP 201)"
        )

        # Verifikasi data tersimpan di database
        self.assertTrue(
            Report.objects.filter(title='Laporan Lengkap Baru').exists(),
            "Laporan seharusnya tersimpan di database"
        )

        # Verifikasi reporter otomatis diisi
        laporan = Report.objects.get(title='Laporan Lengkap Baru')
        self.assertEqual(
            laporan.reporter,
            self.warga,
            "Reporter harus otomatis diisi dari user yang login"
        )

    def test_FT_02_ditolak_jika_judul_kosong(self):
        """
        [FT-02] Laporan ditolak jika judul (title) kosong.
        Harus return HTTP 400 Bad Request.
        """
        url = reverse('report-list')

        # Payload TANPA field title
        payload = {
            'category': 'Infrastruktur',
            'description': 'Deskripsi ada, tapi judul kosong.',
            'location': 'Jl. Merdeka No. 1',
        }

        response = self.client.post(url, payload, format='json')

        # Verifikasi HTTP 400 Bad Request
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            "Laporan tanpa judul seharusnya ditolak (HTTP 400)"
        )

        # Verifikasi ada pesan error untuk field title
        self.assertIn(
            'title',
            response.data,
            "Respons error harus menyebutkan field 'title' yang bermasalah"
        )

    def test_FT_03_ditolak_jika_deskripsi_kosong(self):
        """
        [FT-03] Laporan ditolak jika deskripsi kosong.
        Harus return HTTP 400 Bad Request.
        """
        url = reverse('report-list')

        # Payload TANPA field description
        payload = {
            'title': 'Judul Ada',
            'category': 'Infrastruktur',
            'location': 'Jl. Merdeka No. 1',
        }

        response = self.client.post(url, payload, format='json')

        # Verifikasi HTTP 400 Bad Request
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            "Laporan tanpa deskripsi seharusnya ditolak (HTTP 400)"
        )

        # Verifikasi ada pesan error untuk field description
        self.assertIn(
            'description',
            response.data,
            "Respons error harus menyebutkan field 'description' yang bermasalah"
        )

    def test_FT_04_xss_script_disimpan_sebagai_string_literal(self):
        url = reverse('report-list')

        kode_xss = '<script>alert("xss")</script>'
        payload = {
            'title': 'Laporan XSS Test',
            'category': 'Keamanan',
            'description': kode_xss,
            'location': 'Lab Keamanan Siber',
        }

        response = self.client.post(url, payload, format='json')

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            "Data dengan karakter HTML harus tetap diterima oleh API"
        )

        laporan = Report.objects.get(title='Laporan XSS Test')

        self.assertIn(
            'script',
            laporan.description.lower(),
            "Kode XSS harus tersimpan sebagai string literal di database"
        )
