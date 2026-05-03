from django import forms
from .models import Report

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['title', 'category', 'description', 'location']

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if len(title) < 5:
            raise forms.ValidationError("Judul minimal 5 karakter!")
        return title

    def clean_description(self):
        desc = self.cleaned_data.get('description')
        if len(desc) < 10:
            raise forms.ValidationError("Deskripsi terlalu pendek!")
        return desc