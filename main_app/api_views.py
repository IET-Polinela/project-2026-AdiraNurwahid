from rest_framework import viewsets, permissions
from .models import Report
from .serializers import ReportSerializer
from .permissions import IsOwnerAndDraftOrReadOnly


class ReportViewSet(viewsets.ModelViewSet):

    serializer_class = ReportSerializer

    permission_classes = [
        permissions.IsAuthenticated,
        IsOwnerAndDraftOrReadOnly
    ]

    def get_queryset(self):

        # hanya report milik user login
        return Report.objects.filter(
            reporter=self.request.user
        )

    def perform_create(self, serializer):

        serializer.save(
            reporter=self.request.user
        )