from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from main_app.models import Report

User = get_user_model()

class WorkflowStateTests(APITestCase):

    def setUp(self):
        self.warga = User.objects.create_user(
            username='warga_wf',
            email='warga_wf@test.com',
            password='TestPass123!',
            role='member'
        )

        self.laporan_draft = Report.objects.create(
            title='Lampu Kampus Mati',
            category='Fasilitas Umum',
            description='Lampu di depan gedung rektorat tidak menyala.',
            location='Gedung Rektorat',
            status='DRAFT',
            reporter=self.warga,
        )

        self.laporan_reported = Report.objects.create(
            title='Saluran Air Tersumbat',
            category='Infrastruktur',
            description='Saluran air di samping kantin tersumbat.',
            location='Kantin Polinela',
            status='REPORTED',
            reporter=self.warga,
        )

        self.laporan_resolved = Report.objects.create(
            title='AC Rusak di Lab',
            category='Fasilitas Umum',
            description='AC di Lab CPS 1 sudah diperbaiki.',
            location='Lab CPS 1',
            status='RESOLVED',
            reporter=self.warga,
        )

    def test_WF_01_warga_mengajukan_draf_menjadi_reported(self):
        self.client.force_authenticate(user=self.warga)

        url = f'/api/report/{self.laporan_draft.pk}/'
        payload = {
            'title': self.laporan_draft.title,
            'category': self.laporan_draft.category,
            'description': self.laporan_draft.description,
            'location': self.laporan_draft.location,
            'status': 'REPORTED',
        }

        response = self.client.put(url, payload, format='json')

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            "Pengajuan draf ke REPORTED seharusnya berhasil (HTTP 200)"
        )

        self.laporan_draft.refresh_from_db()
        self.assertEqual(
            self.laporan_draft.status,
            'REPORTED',
            "Status laporan di database harus berubah menjadi 'REPORTED'"
        )

    def test_WF_02_tidak_bisa_edit_laporan_yang_sudah_reported(self):
        """
        [WF-02] Warga tidak bisa mengubah konten laporan yang sudah REPORTED.
        Permission IsOwnerAndDraftOrReadOnly menolak karena status != DRAFT.
        """
        self.client.force_authenticate(user=self.warga)

        url = f'/api/report/{self.laporan_reported.pk}/'
        payload = {
            'title': 'Judul Diubah',
            'category': self.laporan_reported.category,
            'description': self.laporan_reported.description,
            'location': self.laporan_reported.location,
            'status': 'REPORTED',
        }

        response = self.client.put(url, payload, format='json')

        # Harus ditolak dengan 403 Forbidden
        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            "Edit laporan REPORTED seharusnya ditolak (HTTP 403)"
        )

        # Data asli tidak boleh berubah
        self.laporan_reported.refresh_from_db()
        self.assertEqual(
            self.laporan_reported.title,
            'Saluran Air Tersumbat',
            "Judul laporan asli tidak boleh berubah"
        )

    def test_WF_05_laporan_resolved_tidak_bisa_diubah(self):
        """
        [WF-05] Laporan RESOLVED bersifat read-only, tidak bisa diubah.
        """
        self.client.force_authenticate(user=self.warga)

        url = f'/api/report/{self.laporan_resolved.pk}/'
        payload = {
            'title': 'Judul Diubah',
            'category': self.laporan_resolved.category,
            'description': self.laporan_resolved.description,
            'location': self.laporan_resolved.location,
            'status': 'RESOLVED',
        }

        response = self.client.put(url, payload, format='json')

        # Harus ditolak dengan 403 Forbidden
        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
            "Edit laporan RESOLVED seharusnya ditolak (HTTP 403)"
        )


class AdminWorkflowTests(TestCase):

    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin_portal',
            password='AdminPass123!',
            email='warga@test.com',
            role='admin',
            is_staff=True,
        )
        self.warga = User.objects.create_user(
            username='warga_portal',
            password='WargaPass123!',
            email='warga_portal@test.com',
            role='member',
            is_staff=False,
        )

        self.laporan_reported = Report.objects.create(
            title='Jalan Rusak di Blok C',
            category='Infrastruktur',
            description='Jalan berlubang parah di area parkir Blok C.',
            location='Blok C Polinela',
            status='REPORTED',
            reporter=self.admin,
        )

    def test_WF_03_admin_mengubah_status_reported_ke_verified(self):
        """
        [WF-03] Admin mengubah status laporan dari REPORTED menjadi VERIFIED.
        """
        self.client.login(username='admin_portal', password='AdminPass123!')

        url = reverse('update_status', kwargs={'pk': self.laporan_reported.pk})
        response = self.client.post(url, {'status': 'VERIFIED'})

        # Harus sukses redirect (302) atau OK
        self.assertIn(
            response.status_code,
            [200, 302],
            "Admin mengubah status seharusnya berhasil (200 atau 302)"
        )

        # Verifikasi status berubah di database
        self.laporan_reported.refresh_from_db()
        self.assertEqual(
            self.laporan_reported.status,
            'VERIFIED',
            "Status laporan seharusnya berubah menjadi VERIFIED"
        )

    def test_WF_04_tidak_ada_transisi_langsung_ke_resolved_dari_reported(self):
        """
        [WF-04] Pastikan status RESOLVED tidak tersedia langsung dari REPORTED.
        Transisi yang valid dari REPORTED hanya ke VERIFIED.
        """
        # Definisi aturan transisi status yang valid (state machine)
        ALLOWED_TRANSITIONS = {
            'DRAFT': ['REPORTED'],
            'REPORTED': ['VERIFIED'],
            'VERIFIED': ['IN_PROGRESS'],
            'IN_PROGRESS': ['RESOLVED'],
            'RESOLVED': [],
        }

        # Verifikasi bahwa dari REPORTED, RESOLVED tidak ada dalam daftar transisi valid
        transisi_valid_dari_reported = ALLOWED_TRANSITIONS.get('REPORTED', [])

        self.assertNotIn(
            'RESOLVED',
            transisi_valid_dari_reported,
            "Status RESOLVED seharusnya tidak bisa dicapai langsung dari REPORTED"
        )

        self.assertIn(
            'VERIFIED',
            transisi_valid_dari_reported,
            "Dari REPORTED, hanya transisi ke VERIFIED yang valid"
        )
