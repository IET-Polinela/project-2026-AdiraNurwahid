from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from .models import Report
from .serializers import ReportSerializer
from .permissions import IsOwnerAndDraftOrReadOnly
from rest_framework.pagination import PageNumberPagination

class ReportPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class ReportViewSet(viewsets.ModelViewSet):
    serializer_class = ReportSerializer
    pagination_class = ReportPagination

    def get_queryset(self):
        """Filter dan pagination untuk Lab 12.

        Mendukung query param:
        - ?tab=my_reports -> hanya laporan milik user login.
        - ?tab=feed -> semua laporan kecuali DRAFT.
        """
        user = self.request.user
        tab = self.request.query_params.get('tab', 'my_reports').lower()

        queryset = Report.objects.all()

        if tab == 'feed':
            queryset = queryset.exclude(status='DRAFT')
        else:
            queryset = queryset.filter(reporter=user)

        return queryset.order_by('-created_at')

    def get_permissions(self):
        """
        - list, retrieve  → IsAuthenticated
        - create          → IsAuthenticated
        - update, partial_update, destroy → IsAuthenticated + IsOwnerAndDraftOrReadOnly
        """
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [
                permissions.IsAuthenticated,
                IsOwnerAndDraftOrReadOnly,
            ]
        else:
            permission_classes = [permissions.IsAuthenticated]

        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """
        Reporter otomatis diisi dari user yang sedang login.
        Frontend TIDAK perlu (dan tidak bisa) mengirim field 'reporter'.
        """
        serializer.save(reporter=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """
        Override destroy untuk memberikan pesan error yang jelas
        saat laporan tidak bisa dihapus.
        """
        instance = self.get_object()  # otomatis trigger has_object_permission

        # Cek kepemilikan dan status (sudah di-handle permission, ini fallback)
        if instance.reporter != request.user:
            raise PermissionDenied(
                "Hanya pemilik laporan yang dapat menghapus laporan."
            )
        if instance.status != 'DRAFT':
            raise PermissionDenied(
                "Hanya pemilik laporan dengan status DRAFT yang dapat menghapus laporan."
            )

        return super().destroy(request, *args, **kwargs)