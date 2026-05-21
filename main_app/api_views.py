from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q
from .models import Report
from .serializers import ReportSerializer
from .permissions import IsOwnerAndDraftOrReadOnly


class ReportViewSet(viewsets.ModelViewSet):
    serializer_class = ReportSerializer

    def get_queryset(self):
        """
        Mengembalikan queryset yang disesuaikan:
        - Admin: lihat semua laporan.
        - Citizen (member): lihat laporan non-DRAFT milik siapa saja
          PLUS laporan DRAFT milik diri sendiri.
        """
        user = self.request.user

        if user.role == 'admin':
            return Report.objects.all().order_by('-created_at')

        # Citizen: laporan milik user ini + laporan non-DRAFT (publik)
        return Report.objects.filter(
            Q(reporter=user) | Q(status__in=['REPORTED', 'VERIFIED', 'IN_PROGRESS', 'RESOLVED'])
        ).order_by('-created_at')

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