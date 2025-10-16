# calculos/forms.py
from django import forms
from .models import SystemConfiguration

class SystemConfigurationForm(forms.ModelForm):
    class Meta:
        model = SystemConfiguration
        fields = ['theme_mode', 'primary_color', 'background_image']
        
        labels = {
            'theme_mode': 'Modo do Tema',
            'primary_color': 'Cor Principal da Interface',
            'background_image': 'Carregar nova imagem de fundo (opcional)',
        }
        
        widgets = {
            # CORREÇÃO AQUI: Alterado de forms.Select para forms.RadioSelect
            'theme_mode': forms.RadioSelect,
            'primary_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'background_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }