from rest_framework import permissions

class IsOwnerAndDraftOrReadOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):

        # Read only boleh semua login
        if request.method in permissions.SAFE_METHODS:
            return True

        # Edit/Delete hanya pemilik DAN status DRAFT
        return (
            obj.reporter == request.user
            and obj.status == 'DRAFT'
        )