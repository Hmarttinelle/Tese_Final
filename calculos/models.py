# calculos/models.py
from django.db import models

class HistoricoCalculo(models.Model):
    ELEMENTO_CHOICES = [
        ('Viga', 'Viga'),
        ('Pilar', 'Pilar'),
        ('Sapata', 'Sapata'),
    ]

    elemento = models.CharField(max_length=10, choices=ELEMENTO_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    input_data = models.JSONField()
    resultado_final = models.JSONField()

    def __str__(self):
        return f"{self.elemento} - {self.timestamp.strftime('%d/%m/%Y %H:%M')}"

   
    # def get_resultado_final_dict(self):
        try:
            return json.loads(self.resultado_final)
        except json.JSONDecodeError:
            return {}
        
class SystemConfiguration(models.Model):
    THEME_CHOICES = [
        ('light', 'Claro'),
        ('dark', 'Escuro'),
    ]
    background_image = models.ImageField(upload_to='backgrounds/', null=True, blank=True, verbose_name="Imagem de Fundo")

    theme_mode = models.CharField(
        max_length=10,
        choices=THEME_CHOICES,
        default='light',
        verbose_name="Tema da Aplicação"
    )

    primary_color = models.CharField(
        max_length=7,
        default='#0d6efd', # O azul original
        verbose_name="Cor Principal"
    )

    def __str__(self):
        return "Configuração do Sistema"

    class Meta:
        # Nome que aparecerá na área de administração do Django
        verbose_name_plural = "Configuração do Sistema"