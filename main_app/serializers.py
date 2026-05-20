from rest_framework import serializers
from .models import Report


class ReportSerializer(serializers.ModelSerializer):

    class Meta:
        model = Report

        # reporter disembunyikan
        exclude = ['reporter']