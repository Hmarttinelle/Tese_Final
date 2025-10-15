# calculos/views.py
from django.shortcuts import render, redirect
import json 
from .services import viga_service, pilar_service, sapata_service
from .models import HistoricoCalculo
from .forms import SystemConfigurationForm
from .models import SystemConfiguration 

# ==============================================================================
# VIEWS DA APLICAÇÃO
# ==============================================================================

#--- VIEW PARA INICÍAL ---
def index_view(request):
    return render(request, 'calculos/index.html')

# --- VIEW PARA VIGA ---
def viga_view(request):
    context = {}
    if request.method == 'POST':
        try:
            b = float(request.POST.get('b'))
            h = float(request.POST.get('h'))
            f_ck = float(request.POST.get('f_ck'))
            f_yk = float(request.POST.get('f_yk'))
            M_Ed_kNm = float(request.POST.get('M_Ed'))
            c_nom = float(request.POST.get('c_nom'))
            context['input_data'] = request.POST

            resultado = viga_service.dimensionar_viga(b=b, h=h, f_ck=f_ck, f_yk=f_yk, M_Ed_kNm=M_Ed_kNm, c_nom=c_nom)
            context['resultado'] = resultado

            # Se o cálculo foi um sucesso, guarda na base de dados
            if resultado.get('status') == 'Sucesso':
                HistoricoCalculo.objects.create(
                    elemento='Viga',
                    input_data=json.dumps(dict(request.POST)),
                    resultado_final=json.dumps(resultado)
                )

        except (ValueError, TypeError) as e:
            context['resultado'] = {'status': 'Erro', 'mensagem': f'Erro no cálculo: {e}'}
    return render(request, 'calculos/viga_dimensionamento.html', context)

# --- VIEW PARA PILARES ---
def pilar_view(request):
    context = {}
    if request.method == 'POST':
        try:
            b_mm = float(request.POST.get('b'))
            h_mm = float(request.POST.get('h'))
            l_m = float(request.POST.get('l'))
            lig_topo = request.POST.get('lig_topo')
            lig_base = request.POST.get('lig_base')
            f_ck = float(request.POST.get('f_ck'))
            f_yk = float(request.POST.get('f_yk'))
            N_Ed_kN = float(request.POST.get('N_Ed'))
            M0_Ed_kNm = float(request.POST.get('M_Ed'))
            c_nom_mm = float(request.POST.get('c_nom'))
            phi_ef = float(request.POST.get('phi_ef'))
            context['input_data'] = request.POST

            resultado = pilar_service.dimensionar_pilar(
                b_mm=b_mm, h_mm=h_mm, l_m=l_m, lig_topo=lig_topo, lig_base=lig_base,
                f_ck=f_ck, f_yk=f_yk, N_Ed_kN=N_Ed_kN, M0_Ed_kNm=M0_Ed_kNm,
                c_nom_mm=c_nom_mm, phi_ef=phi_ef
            )
            context['resultado'] = resultado

            # Se o cálculo foi um sucesso, guarda na base de dados
            if resultado.get('status') == 'Sucesso':
                # Criamos uma cópia dos dados de entrada para não modificar o original
                input_data_copy = dict(request.POST)
                # O 'csrfmiddlewaretoken' não é relevante para o histórico, por isso removemo-lo
                input_data_copy.pop('csrfmiddlewaretoken', None)
                
                HistoricoCalculo.objects.create(
                    elemento='Pilar',
                    input_data=json.dumps(input_data_copy),
                    resultado_final=json.dumps(resultado)
                )
            # ^^^^^^^^^^^^^^^^ FIM DO NOVO CÓDIGO ^^^^^^^^^^^^^^^

        except (ValueError, TypeError, ZeroDivisionError) as e:
            context['resultado'] = {'status': 'Erro', 'mensagem': f'Erro: {e}. Verifique os valores de entrada.'}
    return render(request, 'calculos/pilar_dimensionamento.html', context)

# --- VIEW PARA SAPATA ---
def sapata_view(request):
    context = {}
    if request.method == 'POST':
        try:
            sigma_adm_kpa = float(request.POST.get('sigma_adm'))
            f_ck = float(request.POST.get('f_ck'))
            f_yk = float(request.POST.get('f_yk'))
            c_nom_mm = float(request.POST.get('c_nom'))
            bp_mm = float(request.POST.get('bp'))
            hp_mm = float(request.POST.get('hp'))
            N_Ed_kN = float(request.POST.get('N_Ed'))
            M_Edy_kNm = float(request.POST.get('M_Edy'))
            context['input_data'] = request.POST
            
            resultado = sapata_service.dimensionar_sapata(
                sigma_adm_kpa, f_ck, f_yk, c_nom_mm, bp_mm, hp_mm, N_Ed_kN, M_Edy_kNm
            )
            context['resultado'] = resultado

            # Se o cálculo foi um sucesso, guarda na base de dados
            if resultado.get('status') == 'Sucesso':
                input_data_copy = dict(request.POST)
                input_data_copy.pop('csrfmiddlewaretoken', None)

                # Os dados de desenho em SVG são muito grandes e não precisam de ser guardados
                resultado_sem_svg = resultado.copy()
                resultado_sem_svg.pop('desenho_planta_svg', None)
                resultado_sem_svg.pop('desenho_corte_svg', None)
                
                HistoricoCalculo.objects.create(
                    elemento='Sapata',
                    input_data=json.dumps(input_data_copy),
                    resultado_final=json.dumps(resultado_sem_svg)
                )

        except (ValueError, TypeError, ZeroDivisionError) as e:
            context['resultado'] = {'status': 'Erro', 'mensagem': f'Erro: {e}. Verifique os valores de entrada.'}
            
    return render(request, 'calculos/sapata_dimensionamento.html', context)

# --- VIEW PARA HISTORICO ---
def historico_view(request):
    """
    Busca todos os cálculos guardados na base de dados e envia-os para a página de histórico.
    """
    # 1. Busca todos os objetos do HistoricoCalculo, ordenados pelos mais recentes primeiro.
    todos_os_calculos = HistoricoCalculo.objects.all().order_by('-timestamp')
    
    # 2. Prepara os dados para serem facilmente lidos no template
    #    (converte o texto JSON de volta para dicionários)
    calculos_processados = []
    for calculo in todos_os_calculos:
        calculos_processados.append({
            'id': calculo.id,
            'elemento': calculo.elemento,
            'timestamp': calculo.timestamp,
            'input_data': calculo.get_input_data_dict(),
            'resultado_final': calculo.get_resultado_final_dict()
        })

    # 3. Define o contexto que será enviado para o template
    context = {
        'calculos': calculos_processados
    }
    
    # 4. Renderiza a nova página de histórico com os dados
    return render(request, 'calculos/historico.html', context)

# --- VIEW PARA HISTORICO_DETALHE ---
def historico_detalhe_view(request, calculo_id):
    """
    Mostra os detalhes de um cálculo específico do histórico,
    incluindo os desenhos (se aplicável) e dados de entrada formatados.
    """
    try:
        calculo = HistoricoCalculo.objects.get(id=calculo_id)
        
        # Prepara os dados para o template
        resultado_final = calculo.get_resultado_final_dict()
        input_data = calculo.get_input_data_dict()
        
        context = {
            'calculo': {
                'id': calculo.id,
                'elemento': calculo.elemento,
                'timestamp': calculo.timestamp,
                'resultado_final': resultado_final
            }
        }

        # --- MELHORIA 1: Gerar desenhos novamente ---
        if calculo.elemento == 'Sapata' and 'dados_desenho' in resultado_final:
            context['calculo']['desenho_planta_svg'] = sapata_service.desenhar_sapata_planta_svg(resultado_final['dados_desenho'])
            context['calculo']['desenho_corte_svg'] = sapata_service.desenhar_sapata_corte_svg(resultado_final['dados_desenho'])

        # --- MELHORIA 2: Formatar dados de entrada com símbolos ---
        INPUT_MAP = {
            'b': {'label': 'Largura', 'symbol': 'b', 'unit': 'mm'},
            'h': {'label': 'Altura', 'symbol': 'h', 'unit': 'mm'},
            'l': {'label': 'Comprimento Real', 'symbol': 'l', 'unit': 'm'},
            'f_ck': {'label': 'Classe do Betão', 'symbol': 'f_{ck}', 'unit': ''},
            'f_yk': {'label': 'Classe do Aço', 'symbol': 'f_{yk}', 'unit': ''},
            'M_Ed': {'label': 'Momento Fletor', 'symbol': 'M_{Ed}', 'unit': 'kNm'},
            'c_nom': {'label': 'Recobrimento', 'symbol': 'c_{nom}', 'unit': 'mm'},
            'lig_topo': {'label': 'Ligação no Topo', 'symbol': '', 'unit': ''},
            'lig_base': {'label': 'Ligação na Base', 'symbol': '', 'unit': ''},
            'N_Ed': {'label': 'Esforço Axial', 'symbol': 'N_{Ed}', 'unit': 'kN'},
            'phi_ef': {'label': 'Coef. Fluência', 'symbol': r'\phi_{ef}', 'unit': ''},
            'sigma_adm': {'label': 'Tensão Admissível', 'symbol': r'\sigma_{adm}', 'unit': 'kPa'},
            'bp': {'label': 'Largura do Pilar', 'symbol': 'b_p', 'unit': 'mm'},
            'hp': {'label': 'Altura do Pilar', 'symbol': 'h_p', 'unit': 'mm'},
            'M_Edy': {'label': 'Momento Fletor (Y)', 'symbol': 'M_{Ed,y}', 'unit': 'kNm'},
        }
        
        input_formatado = []
        for key, value in input_data.items():
            if key in INPUT_MAP:
                info = INPUT_MAP[key]
                input_formatado.append({
                    'label': info['label'],
                    'symbol': info['symbol'],
                    'value': value,
                    'unit': info['unit']
                })
        
        context['calculo']['input_data_formatado'] = input_formatado

        return render(request, 'calculos/historico_detalhe.html', context)

    except HistoricoCalculo.DoesNotExist:
        return redirect('historico_calculos')

# --- VIEW PARA DELETAR HISTORICO ---
def historico_delete_view(request, calculo_id):
    """
    Encontra um cálculo pelo seu ID e elimina-o da base de dados.
    """
    # Usamos um bloco try/except para o caso de o cálculo já ter sido eliminado.
    try:
        calculo = HistoricoCalculo.objects.get(id=calculo_id)
        calculo.delete()
    except HistoricoCalculo.DoesNotExist:
        # Se não encontrar, não faz nada, apenas continua.
        pass
    
    # Redireciona o utilizador de volta para a página de histórico.
    return redirect('historico_calculos')


# --- VIEW DE CONFIGURAÇÕES ---
def configuracao_view(request):
    # Usamos .get_or_create() para garantir que temos sempre um objeto de configuração.
    # Ele tenta obter o primeiro objeto. Se não existir, cria um.
    config, created = SystemConfiguration.objects.get_or_create(id=1)

    if request.method == 'POST':
        # Se o formulário for submetido, preenchemo-lo com os dados enviados (e os ficheiros)
        form = SystemConfigurationForm(request.POST, request.FILES, instance=config)
        if form.is_valid():
            form.save() # Guarda a imagem carregada
            return redirect('pagina_inicial') # Redireciona para o menu principal após guardar
    else:
        # Se for um pedido GET, apenas mostramos o formulário ligado à configuração existente
        form = SystemConfigurationForm(instance=config)

    return render(request, 'calculos/configuracao.html', {'form': form})