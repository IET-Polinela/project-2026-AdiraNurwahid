from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from main_app.models import Report

User = get_user_model()

class AuthenticationTests(APITestCase):

    def setUp(self):
        self.warga = User.objects.create_user(
            username='warga_test',
            password='Password123!',
            email='warga_test@test.com',
            role='member',
        )
        self.admin = User.objects.create_user(
            username='admin_test',
            password='AdminPass123!',
            email='admin_test@test.com',
            role='admin',
            is_staff=True,
        )

    def test_AUTH_01_login_warga_dengan_kredensial_valid(self):
        url = reverse('token_obtain_pair')
        payload = {
            'username': 'warga_test',
            'password': 'Password123!',
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            "Login dengan kredensial valid seharusnya mengembalikan HTTP 200"
        )
        self.assertIn(
            'access',
            response.data,
            "Respons login harus mengandung field 'access' (JWT Access Token)"
        )
        self.assertIn(
            'refresh',
            response.data,
            "Respons login harus mengandung field 'refresh' (JWT Refresh Token)"
        )

    def test_AUTH_02_login_warga_dengan_password_salah(self):
        url = reverse('token_obtain_pair')
        payload = {
            'username': 'warga_test',
            'password': 'passwordSALAH',
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            "Login dengan password salah seharusnya mengembalikan HTTP 401"
        )
        self.assertNotIn(
            'access',
            response.data,
            "Tidak boleh ada token yang dikeluarkan untuk kredensial invalid"
        )

    def test_AUTH_03_warga_tidak_bisa_akses_halaman_admin(self):
        """
        [AUTH-03] Pengguna berstatus Warga biasa mencoba
        mengakses URL endpoint/halaman portal Admin.

        Hasil yang diharapkan: HTTP 302 redirect (bukan 200).
        """
        # Login sebagai warga biasa (non-staff)
        self.client.login(username='warga_test', password='Password123!')

        # Coba akses halaman report_list yang hanya untuk admin/staff
        response = self.client.get(reverse('report_list'))

        # Warga biasa harus di-redirect (302) karena bukan admin
        self.assertIn(
            response.status_code,
            [302, 403],
            "Warga biasa seharusnya tidak bisa akses halaman admin (302 atau 403)"
        )
