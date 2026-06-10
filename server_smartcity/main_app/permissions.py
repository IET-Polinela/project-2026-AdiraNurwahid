from rest_framework import permissions


class IsOwnerAndDraftOrReadOnly(permissions.BasePermission):
    """
    Custom permission untuk Report:
    - Safe methods (GET, HEAD, OPTIONS): diizinkan untuk semua user login.
    - UPDATE (PUT/PATCH): hanya pemilik laporan DAN status masih DRAFT.
    - DELETE: hanya pemilik laporan DAN status masih DRAFT.
      Jika status VERIFIED atau bukan DRAFT → 403 Forbidden.
    """

    message = "Tidak ada akses."

    def get_message(self, request, obj):
        """Return dynamic error message based on action."""
        if obj.reporter != request.user:
            return "Hanya pemilik laporan yang dapat mengubahnya."
        if obj.status != 'DRAFT':
            if request.method == 'DELETE':
                return "Hanya pemilik laporan dengan status DRAFT yang dapat menghapus laporan."
            return "Hanya pemilik laporan dengan status DRAFT yang dapat mengubahnya."
        return self.message

    def has_object_permission(self, request, view, obj):
        # Safe methods (GET list/detail) → izinkan
        if request.method in permissions.SAFE_METHODS:
            return True

        # Untuk PUT, PATCH, DELETE → wajib pemilik DAN status DRAFT
        is_owner = obj.reporter == request.user
        is_draft = obj.status == 'DRAFT'

        if not is_owner or not is_draft:
            self.message = self.get_message(request, obj)
            return False

        return True