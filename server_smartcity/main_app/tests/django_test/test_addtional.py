from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from main_app.models import Report

User = get_user_model()

# =============================================================================
# ADDITIONAL TESTS FOR 100% STATEMENT COVERAGE
# =============================================================================

class SerializerAndModelCoverageTests(APITestCase):
    """
    Kelas pengujian tambahan untuk menaikkan coverage model dan serializer.
    """
    def setUp(self):
        self.warga = User.objects.create_user(
            username='warga_str_test',
            email='warga_str_test@test.com',
            password='Password123!',
            role='member'
        )

    def test_report_model_str(self):
        """
        Menguji str(report) agar memanggil __str__ dan mengembalikan judul laporan.
        """
        report = Report.objects.create(
            title='Laporan Str Uji',
            category='Lainnya',
            description='Deskripsi',
            location='Lokasi',
            status='REPORTED',
            reporter=self.warga
        )
        self.assertEqual(str(report), 'Laporan Str Uji')

    def test_report_serializer_no_request_context(self):
        """
        Menguji serializer tanpa menyertakan request dalam context,
        sehingga reporter_name mengembalikan 'Warga Anonim' dan is_owner False.
        """
        from main_app.serializers import ReportSerializer
        report = Report.objects.create(
            title='Laporan Serializer Uji',
            category='Lainnya',
            description='Deskripsi',
            location='Lokasi',
            status='REPORTED',
            reporter=self.warga
        )
        serializer = ReportSerializer(report, context={})
        self.assertFalse(serializer.data['is_owner'])
        self.assertEqual(serializer.data['reporter_name'], 'Warga Anonim')


class MainAppMonolithicViewsCoverageTests(TestCase):
    """
    Menguji view monolitik di main_app/views.py untuk mencakup semua alur
    dispatch, GET, POST, validasi form, dan API detail/pencarian non-DRF.
    """
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin_mono',
            password='Password123!',
            email='admin_mono@test.com',
            role='admin',
            is_staff=True
        )
        self.citizen = User.objects.create_user(
            username='citizen_mono',
            password='Password123!',
            email='citizen_mono@test.com',
            role='citizen',
            is_staff=False
        )
        self.report = Report.objects.create(
            title='Laporan Monolitik Uji',
            category='Infrastruktur',
            description='Ada kerusakan infrastruktur.',
            location='Bandung',
            status='REPORTED',
            reporter=self.citizen
        )

    def test_report_detail_api_valid(self):
        from main_app.views import report_detail_api
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get('/dummy-url/')
        request.user = self.admin
        response = report_detail_api(request, self.report.id)
        self.assertEqual(response.status_code, 200)

    def test_report_detail_api_invalid(self):
        from main_app.views import report_detail_api
        from django.test import RequestFactory
        from django.http import Http404
        factory = RequestFactory()
        request = factory.get('/dummy-url/')
        request.user = self.admin
        with self.assertRaises(Http404):
            report_detail_api(request, 99999)

    def test_report_search_unauthenticated(self):
        response = self.client.get(reverse('report_search') + '?q=Lampu')
        self.assertEqual(response.status_code, 403)

    def test_report_search_citizen(self):
        self.client.login(username='citizen_mono', password='Password123!')
        response = self.client.get(reverse('report_search') + '?q=Lampu')
        self.assertEqual(response.status_code, 403)

    def test_report_search_admin(self):
        self.client.login(username='admin_mono', password='Password123!')
        response = self.client.get(reverse('report_search') + '?q=Monolitik')
        self.assertEqual(response.status_code, 200)

    def test_home_view(self):
        self.client.login(username='admin_mono', password='Password123!')
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main_app/home.html')

    def test_report_list_view_unauthenticated(self):
        response = self.client.get(reverse('report_list'))
        self.assertEqual(response.status_code, 302)

    def test_report_list_view_citizen(self):
        self.client.login(username='citizen_mono', password='Password123!')
        response = self.client.get(reverse('report_list'))
        self.assertEqual(response.status_code, 302)

    def test_report_list_view_admin(self):
        self.client.login(username='admin_mono', password='Password123!')
        response = self.client.get(reverse('report_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main_app/home.html')

    def test_report_create_view_unauthenticated(self):
        response = self.client.get(reverse('add_report'))
        self.assertEqual(response.status_code, 302)

    def test_report_create_view_citizen(self):
        self.client.login(username='citizen_mono', password='Password123!')
        response = self.client.get(reverse('add_report'))
        self.assertEqual(response.status_code, 302)

    def test_report_create_view_admin_get(self):
        self.client.login(username='admin_mono', password='Password123!')
        response = self.client.get(reverse('add_report'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main_app/add_report.html')

    def test_report_create_view_admin_post_valid(self):
        self.client.login(username='admin_mono', password='Password123!')
        payload = {
            'title': 'Laporan Form Baru',
            'category': 'Infrastruktur',
            'description': 'Deskripsi baru.',
            'location': 'Jakarta',
            'status': 'DRAFT'
        }
        response = self.client.post(reverse('add_report'), payload)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('report_list'), fetch_redirect_response=False)
        self.assertTrue(Report.objects.filter(title='Laporan Form Baru').exists())

    def test_report_detail_view_unauthenticated(self):
        response = self.client.get(reverse('report_detail', kwargs={'pk': self.report.id}))
        self.assertEqual(response.status_code, 302)

    def test_report_detail_view_citizen(self):
        self.client.login(username='citizen_mono', password='Password123!')
        response = self.client.get(reverse('report_detail', kwargs={'pk': self.report.id}))
        self.assertEqual(response.status_code, 302)

    def test_report_detail_view_admin(self):
        self.client.login(username='admin_mono', password='Password123!')
        response = self.client.get(reverse('report_detail', kwargs={'pk': self.report.id}))
        self.assertEqual(response.status_code, 200)

    def test_report_update_view_unauthenticated(self):
        response = self.client.get(reverse('update_report', kwargs={'pk': self.report.id}))
        self.assertEqual(response.status_code, 302)

    def test_report_update_view_citizen(self):
        self.client.login(username='citizen_mono', password='Password123!')
        response = self.client.get(reverse('update_report', kwargs={'pk': self.report.id}))
        self.assertEqual(response.status_code, 302)

    def test_report_update_view_admin_get(self):
        self.client.login(username='admin_mono', password='Password123!')
        response = self.client.get(reverse('update_report', kwargs={'pk': self.report.id}))
        self.assertEqual(response.status_code, 200)

    def test_report_update_view_admin_post_valid(self):
        self.client.login(username='admin_mono', password='Password123!')
        payload = {
            'title': 'Laporan Terupdate',
            'category': 'Infrastruktur',
            'description': 'Deskripsi terupdate.',
            'location': 'Jakarta',
            'status': 'REPORTED'
        }
        response = self.client.post(reverse('update_report', kwargs={'pk': self.report.id}), payload)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('report_list'), fetch_redirect_response=False)
        self.report.refresh_from_db()
        self.assertEqual(self.report.title, 'Laporan Terupdate')

    def test_report_delete_view_unauthenticated(self):
        response = self.client.get(reverse('delete_report', kwargs={'pk': self.report.id}))
        self.assertEqual(response.status_code, 302)

    def test_report_delete_view_citizen(self):
        self.client.login(username='citizen_mono', password='Password123!')
        response = self.client.get(reverse('delete_report', kwargs={'pk': self.report.id}))
        self.assertEqual(response.status_code, 302)

    def test_report_delete_view_admin_get(self):
        self.client.login(username='admin_mono', password='Password123!')
        response = self.client.get(reverse('delete_report', kwargs={'pk': self.report.id}))
        self.assertEqual(response.status_code, 200)

    def test_report_delete_view_admin_post(self):
        self.client.login(username='admin_mono', password='Password123!')
        response = self.client.post(reverse('delete_report', kwargs={'pk': self.report.id}))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('report_list'), fetch_redirect_response=False)
        self.assertFalse(Report.objects.filter(id=self.report.id).exists())

    def test_report_delete_view_direct_delete_method(self):
        from main_app.views import ReportDeleteView
        from django.test import RequestFactory
        from django.contrib.messages.storage.fallback import FallbackStorage

        factory = RequestFactory()
        request = factory.post(reverse('delete_report', kwargs={'pk': self.report.id}))
        request.user = self.admin

        setattr(request, 'session', {})
        messages_storage = FallbackStorage(request)
        setattr(request, '_messages', messages_storage)

        view = ReportDeleteView()
        view.setup(request, pk=self.report.id)
        view.object = view.get_object()

        response = view.delete(request)
        self.assertEqual(response.status_code, 302)

    def test_report_update_status_view_unauthenticated(self):
        response = self.client.post(reverse('update_status', kwargs={'pk': self.report.id}), {'status': 'VERIFIED'})
        self.assertEqual(response.status_code, 302)

    def test_report_update_status_view_citizen(self):
        self.client.login(username='citizen_mono', password='Password123!')
        response = self.client.post(reverse('update_status', kwargs={'pk': self.report.id}), {'status': 'VERIFIED'})
        self.assertEqual(response.status_code, 302)
