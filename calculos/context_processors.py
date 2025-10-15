# calculos/context_processors.py
from .models import SystemConfiguration

def system_config_processor(request):
    """
    Este processador de contexto torna a configuração do sistema
    (como a imagem de fundo, tema e cor) disponível em todos os templates.
    """
    try:
        # Tenta obter a primeira (e única) configuração do sistema
        config = SystemConfiguration.objects.first()
    except Exception:
        config = None
    
    return {'system_config': config}