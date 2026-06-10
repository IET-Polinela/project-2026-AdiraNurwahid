from rest_framework import serializers
from .models import Report

class ReportSerializer(serializers.ModelSerializer):

    reporter_username = serializers.SerializerMethodField()

    is_owner = serializers.SerializerMethodField()

    def get_reporter_username(self, obj):
        request = self.context.get('request')

        if request:
            tab = request.query_params.get('tab')

            # Feed Kota harus anonim
            if tab == 'feed':
                return 'Warga Anonim'

        return obj.reporter.username

    def get_is_owner(self, obj):
        request = self.context.get('request')

        if request and request.user.is_authenticated:
            return obj.reporter == request.user

        return False

    class Meta:
        model = Report
        fields = '__all__'