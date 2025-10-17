# calculos/views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from .services import viga_service, pilar_service, sapata_service
from .models import HistoricoCalculo, SystemConfiguration
from .forms import SystemConfigurationForm

# ==============================================================================
# FUNÇÃO AUXILIAR PARA GUARDAR HISTÓRICO (MODIFICADA)
# ==============================================================================

def _salvar_calculo_no_historico(request, elemento, resultado):
    """
    Guarda o resultado de um cálculo e RETORNA o objeto salvo.
    """
    if resultado.get('status') == 'Sucesso':
        input_data_copy = request.POST.copy().dict()
        input_data_copy.pop('csrfmiddlewaretoken', None)

        resultado_final_para_db = resultado.copy()
        if elemento == 'Sapata':
            resultado_final_para_db.pop('desenho_planta_svg', None)
            resultado_final_para_db.pop('desenho_corte_svg', None)
        
        calculo_obj = HistoricoCalculo.objects.create(
            elemento=elemento,
            input_data=input_data_copy,
            resultado_final=resultado_final_para_db
        )
        return calculo_obj # <-- ALTERAÇÃO: Retorna o objeto criado
    return None

# ==============================================================================
# VIEWS DA APLICAÇÃO (MODIFICADAS)
# ==============================================================================

def index_view(request):
    return render(request, 'calculos/index.html')

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
            
            # ALTERAÇÃO: Captura o ID do cálculo salvo e adiciona ao contexto
            calculo_salvo = _salvar_calculo_no_historico(request, 'Viga', resultado)
            if calculo_salvo:
                resultado['calculo_id'] = calculo_salvo.id
            
            context['resultado'] = resultado

        except (ValueError, TypeError) as e:
            context['resultado'] = {'status': 'Erro', 'mensagem': f'Erro no cálculo: {e}'}
    return render(request, 'calculos/viga_dimensionamento.html', context)

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
            
            calculo_salvo = _salvar_calculo_no_historico(request, 'Pilar', resultado)
            if calculo_salvo:
                resultado['calculo_id'] = calculo_salvo.id
            
            context['resultado'] = resultado

        except (ValueError, TypeError, ZeroDivisionError) as e:
            context['resultado'] = {'status': 'Erro', 'mensagem': f'Erro: {e}. Verifique os valores de entrada.'}
    return render(request, 'calculos/pilar_dimensionamento.html', context)

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
            
            calculo_salvo = _salvar_calculo_no_historico(request, 'Sapata', resultado)
            if calculo_salvo:
                resultado['calculo_id'] = calculo_salvo.id
            
            context['resultado'] = resultado

        except (ValueError, TypeError, ZeroDivisionError) as e:
            context['resultado'] = {'status': 'Erro', 'mensagem': f'Erro: {e}. Verifique os valores de entrada.'}
            
    return render(request, 'calculos/sapata_dimensionamento.html', context)

def historico_view(request):
    todos_os_calculos = HistoricoCalculo.objects.all().order_by('-timestamp')
    context = {'calculos': todos_os_calculos}
    return render(request, 'calculos/historico.html', context)

def historico_detalhe_view(request, calculo_id):
    try:
        calculo = HistoricoCalculo.objects.get(id=calculo_id)
        
        resultado_final = calculo.resultado_final
        input_data = calculo.input_data
        
        context = {
            'calculo': {
                'id': calculo.id,
                'elemento': calculo.elemento,
                'timestamp': calculo.timestamp,
                'resultado_final': resultado_final,
            }
        }

        if calculo.elemento == 'Sapata' and 'dados_desenho' in resultado_final:
            context['calculo']['desenho_planta_svg'] = sapata_service.desenhar_sapata_planta_svg(resultado_final['dados_desenho'])
            context['calculo']['desenho_corte_svg'] = sapata_service.desenhar_sapata_corte_svg(resultado_final['dados_desenho'])

        INPUT_MAP = {
            'b': {'label': 'Largura', 'symbol': 'b', 'unit': 'mm'}, 'h': {'label': 'Altura', 'symbol': 'h', 'unit': 'mm'},
            'l': {'label': 'Comprimento Real', 'symbol': 'l', 'unit': 'm'}, 'f_ck': {'label': 'Classe do Betão', 'symbol': 'f_{ck}', 'unit': ''},
            'f_yk': {'label': 'Classe do Aço', 'symbol': 'f_{yk}', 'unit': ''}, 'M_Ed': {'label': 'Momento Fletor', 'symbol': 'M_{Ed}', 'unit': 'kNm'},
            'c_nom': {'label': 'Recobrimento', 'symbol': 'c_{nom}', 'unit': 'mm'}, 'lig_topo': {'label': 'Ligação no Topo', 'symbol': '', 'unit': ''},
            'lig_base': {'label': 'Ligação na Base', 'symbol': '', 'unit': ''}, 'N_Ed': {'label': 'Esforço Axial', 'symbol': 'N_{Ed}', 'unit': 'kN'},
            'phi_ef': {'label': 'Coef. Fluência', 'symbol': r'\phi_{ef}', 'unit': ''}, 'sigma_adm': {'label': 'Tensão Admissível', 'symbol': r'\sigma_{adm}', 'unit': 'kPa'},
            'bp': {'label': 'Largura do Pilar', 'symbol': 'b_p', 'unit': 'mm'}, 'hp': {'label': 'Altura do Pilar', 'symbol': 'h_p', 'unit': 'mm'},
            'M_Edy': {'label': 'Momento Fletor (Y)', 'symbol': 'M_{Ed,y}', 'unit': 'kNm'},
        }
        
        input_formatado = []
        for key, value in input_data.items():
            if key in INPUT_MAP:
                info = INPUT_MAP[key]
                input_formatado.append({'label': info['label'], 'symbol': info['symbol'], 'value': value, 'unit': info['unit']})
        
        context['calculo']['input_data_formatado'] = input_formatado

        return render(request, 'calculos/historico_detalhe.html', context)

    except HistoricoCalculo.DoesNotExist:
        return redirect('historico_calculos')

def historico_delete_view(request, calculo_id):
    try:
        calculo = HistoricoCalculo.objects.get(id=calculo_id)
        calculo.delete()
    except HistoricoCalculo.DoesNotExist:
        pass
    
    return redirect('historico_calculos')

def configuracao_view(request):
    config, created = SystemConfiguration.objects.get_or_create(id=1)

    if request.method == 'POST':
        form = SystemConfigurationForm(request.POST, request.FILES, instance=config)
        if form.is_valid():
            form.save()
            return redirect('pagina_inicial')
    else:
        form = SystemConfigurationForm(instance=config)

    return render(request, 'calculos/configuracao.html', {'form': form})
    
def gerar_relatorio_pdf_view(request, calculo_id):
    try:
        calculo = HistoricoCalculo.objects.get(id=calculo_id)
    except HistoricoCalculo.DoesNotExist:
        return HttpResponse("Cálculo não encontrado.", status=404)

    INPUT_MAP = {
        'b': {'label': 'Largura', 'symbol': 'b', 'unit': 'mm'}, 'h': {'label': 'Altura', 'symbol': 'h', 'unit': 'mm'},
        'l': {'label': 'Comprimento Real', 'symbol': 'l', 'unit': 'm'}, 'f_ck': {'label': 'Classe do Betão', 'symbol': 'f_{ck}', 'unit': ''},
        'f_yk': {'label': 'Classe do Aço', 'symbol': 'f_{yk}', 'unit': ''}, 'M_Ed': {'label': 'Momento Fletor', 'symbol': 'M_{Ed}', 'unit': 'kNm'},
        'c_nom': {'label': 'Recobrimento', 'symbol': 'c_{nom}', 'unit': 'mm'}, 'lig_topo': {'label': 'Ligação no Topo', 'symbol': '', 'unit': ''},
        'lig_base': {'label': 'Ligação na Base', 'symbol': '', 'unit': ''}, 'N_Ed': {'label': 'Esforço Axial', 'symbol': 'N_{Ed}', 'unit': 'kN'},
        'phi_ef': {'label': 'Coef. Fluência', 'symbol': r'\phi_{ef}', 'unit': ''}, 'sigma_adm': {'label': 'Tensão Admissível', 'symbol': r'\sigma_{adm}', 'unit': 'kPa'},
        'bp': {'label': 'Largura do Pilar', 'symbol': 'b_p', 'unit': 'mm'}, 'hp': {'label': 'Altura do Pilar', 'symbol': 'h_p', 'unit': 'mm'},
        'M_Edy': {'label': 'Momento Fletor (Y)', 'symbol': 'M_{Ed,y}', 'unit': 'kNm'},
    }
    input_formatado = []
    for key, value in calculo.input_data.items():
        if key in INPUT_MAP:
            info = INPUT_MAP[key]
            input_formatado.append({'label': info['label'], 'value': value, 'unit': info['unit']})
    
    calculo.input_data_formatado = input_formatado

    html_string = render_to_string('calculos/relatorio_pdf.html', {'calculo': calculo})
    pdf = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="relatorio_{calculo.elemento.lower()}_{calculo.id}.pdf"'
    
    return response