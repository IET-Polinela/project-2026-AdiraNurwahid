from rest_framework import serializers
from .models import Report


class ReportSerializer(serializers.ModelSerializer):

    reporter_username = serializers.ReadOnlyField(
        source='reporter.username'
    )

    class Meta:
        model = Report
        fields = '__all__'

        read_only_fields = [
            'reporter',
            'reporter_username',
            'created_at',
            'updated_at'
        ]