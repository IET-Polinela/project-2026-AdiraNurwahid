from rest_framework import serializers
from .models import Report

class ReportSerializer(serializers.ModelSerializer):

    reporter_name = serializers.SerializerMethodField()

    is_owner = serializers.SerializerMethodField()

    def get_reporter_name(self, obj):
        request = self.context.get('request')

        if request:
            tab = request.query_params.get('tab')

            # Feed Kota harus anonim
            if tab == 'feed':
                return 'Warga Anonim'

            # Tampilkan nama asli untuk pemilik laporan
            if request.user and request.user.is_authenticated:
                return obj.reporter.username if obj.reporter else 'Warga Anonim'

        # Jika tidak ada request context, kembalikan Warga Anonim
        return 'Warga Anonim'

    def get_is_owner(self, obj):
        request = self.context.get('request')

        if request and request.user.is_authenticated:
            return obj.reporter == request.user

        return False

    class Meta:
        model = Report
        fields = '__all__'
