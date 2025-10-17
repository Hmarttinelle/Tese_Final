# calculos/services/viga_service.py
import math
from . import armadura_service

def dimensionar_viga(b, h, f_ck, f_yk, M_Ed_kNm, c_nom):
    """
    Função principal que realiza o dimensionamento de uma viga à flexão simples,
    agora utilizando o novo serviço de otimização de armaduras.
    """
    passos = []
    
    # --- Parâmetros de Cálculo ---
    gamma_c, gamma_s, alpha_cc, lambda_val = 1.5, 1.15, 1.0, 0.8
    f_cd_mpa = alpha_cc * f_ck / gamma_c
    f_yd_mpa = f_yk / gamma_s
    M_Ed_Nm = M_Ed_kNm * 1000
    b_m = b / 1000
    phi_estribo = 8.0

    passos.append({"titulo": "1. Parâmetros de Cálculo", "calculo": f"f_cd = {f_ck:.0f} / {gamma_c} = {f_cd_mpa:.2f} MPa; f_yd = {f_yk:.0f} / {gamma_s} = {f_yd_mpa:.2f} MPa"})

    # --- Iteração 1: Estimar diâmetro para calcular altura útil (d) ---
    phi_long_assumido = 16.0
    passos.append({"titulo": "2. Iteração 1 - Suposição inicial", "calculo": f"Assumir: Ø Estribo = {phi_estribo} mm; Ø Arm. Long. = {phi_long_assumido} mm."})
    
    d = h - c_nom - phi_estribo - (phi_long_assumido / 2)
    d_m = d / 1000
    passos.append({"titulo": "3. Altura útil estimada (d₁)", "formula": r"d = h - c_{nom} - \phi_{estribo} - \frac{\phi_{long}}{2}", "calculo": f"d₁ = {h:.1f} - {c_nom:.1f} - {phi_estribo:.1f} - {phi_long_assumido:.1f} / 2 = {d:.1f} mm"})

    mu = M_Ed_Nm / (b_m * d_m**2 * (f_cd_mpa * 10**6)) if (b_m * d_m**2 * f_cd_mpa) > 0 else 0
    passos.append({"titulo": "4. Momento reduzido (μ₁)", "formula": r"\mu = \frac{M_{Ed}}{b \cdot d^2 \cdot f_{cd}}", "calculo": f"μ₁ = {M_Ed_Nm:.0f} / ({b_m} x {d_m:.3f}² x ({f_cd_mpa:.2f} x 10^6)) = {mu:.3f}"})
    
    mu_lim = lambda_val * 0.45 * (1 - 0.5 * lambda_val * 0.45)
    if mu > mu_lim:
        raise ValueError(f"Momento reduzido (μ={mu:.3f}) excede o limite (μ_lim={mu_lim:.3f}). A secção necessita de ser redimensionada.")
    passos.append({"titulo": "5. Verificação de ductilidade", "calculo": f"μ ({mu:.3f}) <= μ_lim ({mu_lim:.3f}) -> OK"})

    # --- Cálculo intermédio para encontrar o diâmetro ótimo ---
    xi_temp = (1 - math.sqrt(1 - 2 * mu)) / lambda_val if mu < 0.5 else 1.25
    z_temp = d_m * (1 - 0.5 * lambda_val * xi_temp)
    As_req_cm2_temp = (M_Ed_Nm / (z_temp * (f_yd_mpa * 10**6))) * 10000 if z_temp > 0 else 0
    
    largura_disponivel = b - 2 * c_nom - 2 * phi_estribo
    solucoes_temp = armadura_service.encontrar_combinacoes_otimas(As_req_cm2_temp, largura_disponivel)
    
    solucao_unica_temp = solucoes_temp.get('unica')
    
    phi_long_final = 0
    if solucao_unica_temp:
        phi_long_final = int(solucao_unica_temp['combinacao_str'].split('Ø')[1])

    # --- Iteração 2: Recálculo com o diâmetro final para maior precisão ---
    if phi_long_final and phi_long_final != phi_long_assumido:
        passos.append({"titulo": "6. Recálculo (Iteração 2)", "calculo": f"O diâmetro da solução de varão único ({phi_long_final}mm) é diferente do assumido ({phi_long_assumido}mm). Procede-se a um recálculo para garantir a precisão."})
        d = h - c_nom - phi_estribo - (phi_long_final / 2)
        d_m = d / 1000
        passos.append({"titulo": "6.1. Nova Altura útil (d₂)", "calculo": f"d₂ = {h:.1f} - {c_nom:.1f} - {phi_estribo:.1f} - {phi_long_final:.1f} / 2 = {d:.1f} mm"})
        mu = M_Ed_Nm / (b_m * d_m**2 * (f_cd_mpa * 10**6)) if (b_m * d_m**2 * f_cd_mpa) > 0 else 0
        passos.append({"titulo": "6.2. Novo Momento reduzido (μ₂)", "formula": r"\mu = \frac{M_{Ed}}{b \cdot d^2 \cdot f_{cd}}", "calculo": f"μ₂ = {M_Ed_Nm:.0f} / ({b_m} x {d_m:.3f}² x ({f_cd_mpa:.2f} x 10^6)) = {mu:.3f}"})
        if mu > mu_lim:
            raise ValueError("Momento reduzido excede o limite após recálculo.")
    
    # --- Cálculo Final da Armadura ---
    xi = (1 - math.sqrt(1 - 2 * mu)) / lambda_val if mu < 0.5 else 1.25
    z = d_m * (1 - 0.5 * lambda_val * xi)
    As_req_cm2 = (M_Ed_Nm / (z * (f_yd_mpa * 10**6))) * 10000 if z > 0 else 0
    
    calculo_as_req = (f"ξ = (1 - √(1 - 2 x {mu:.3f})) / {lambda_val} = {xi:.3f}<br>"
                      f"z = {d_m:.3f} x (1 - 0.5 x {lambda_val} x {xi:.3f}) = {z:.3f} m<br>"
                      f"As,req = {M_Ed_Nm:.0f} / ({z:.3f} x ({f_yd_mpa:.2f} x 10^6)) = <b>{As_req_cm2:.2f} cm²</b>")
    passos.append({"titulo": "7. Área de Aço Necessária", "formula": r"\xi = \frac{1 - \sqrt{1 - 2\mu}}{\lambda} \ ; \ z = d(1 - 0.5\lambda\xi) \ ; \ A_s = \frac{M_{Ed}}{z \cdot f_{yd}}", "calculo": calculo_as_req})

    solucoes = armadura_service.encontrar_combinacoes_otimas(As_req_cm2, largura_disponivel)
    solucao_unica = solucoes.get('unica')
    solucao_mista = solucoes.get('mista')

    if not solucao_unica and not solucao_mista:
        raise ValueError("Não foi possível encontrar uma combinação de armadura válida que coubesse na secção.")

    # Determinar a solução principal (a mais económica de todas)
    if solucao_unica and solucao_mista:
        solucao_principal = min([solucao_unica, solucao_mista], key=lambda x: x['area_total_cm2'])
    else:
        solucao_principal = solucao_unica or solucao_mista
    
    combinacao_final_str = solucao_principal['combinacao_str']
    As_prov_cm2 = solucao_principal['As_final_cm2']
    
    # Adicionar passo com as duas opções
    texto_proposta = f"Para {As_req_cm2:.2f} cm², foram encontradas as seguintes soluções:<br>"
    if solucao_mista:
        texto_proposta += f" • <b>Opção Mista (mais económica): {solucao_mista['combinacao_str']}</b> ({solucao_mista['As_final_cm2']:.2f} cm²)<br>"
    if solucao_unica:
        texto_proposta += f" • <b>Opção Diâmetro Único: {solucao_unica['combinacao_str']}</b> ({solucao_unica['As_final_cm2']:.2f} cm²)<br>"
    texto_proposta += f"<br>A solução ótima adotada é a de menor área total: <b>{combinacao_final_str}</b>."
    passos.append({"titulo": "8. Proposta de Armadura (Soluções Ótimas)", "calculo": texto_proposta})

    # --- Verificações Finais de Armadura Mínima ---
    if f_ck <= 50: f_ctm = 0.30 * f_ck**(2/3)
    else: f_ctm = 2.12 * math.log(1 + (f_ck + 8) / 10)
    as_min_termo1 = 0.26 * (f_ctm / f_yk) * b_m * d_m * 10000
    as_min_termo2 = 0.0013 * b_m * d_m * 10000
    As_min_cm2 = max(as_min_termo1, as_min_termo2)
    As_final_cm2 = max(As_prov_cm2, As_min_cm2)
    
    calculo_as_min = (f"f_ctm = 0.30 x {f_ck:.0f}^(2/3) = {f_ctm:.2f} MPa<br>"
                      f"As,min₁ = 0.26 x ({f_ctm:.2f} / {f_yk:.0f}) x {b:.0f} x {d:.1f} = {as_min_termo1:.2f} cm²<br>"
                      f"As,min₂ = 0.0013 x {b:.0f} x {d:.1f} = {as_min_termo2:.2f} cm²<br>"
                      f"As,min = max({as_min_termo1:.2f}, {as_min_termo2:.2f}) = {As_min_cm2:.2f} cm²<br>"
                      f"Área de armadura a adotar: max(As,prov, As,min) = max({As_prov_cm2:.2f}, {As_min_cm2:.2f}) = <b>{As_final_cm2:.2f} cm²</b>")
    passos.append({"titulo": "9. Verificação da Armadura Mínima", "formula": r"A_{s,min} = max(0.26\frac{f_{ctm}}{f_{yk}} \cdot b_t \cdot d; 0.0013 \cdot b_t \cdot d)", "calculo": calculo_as_min})

    passos.append({"titulo": "10. Armadura Superior Construtiva (Porta-Estribos)", "calculo": "Para garantir a correta montagem da armadura e o posicionamento dos estribos, adota-se uma armadura superior construtiva. A prática comum consiste em utilizar uma armadura mínima de <b>2 Ø 10</b>."})

    # --- Montagem do resultado final ---
    try:
        n_barras = sum([int(s.split('Ø')[0].strip()) for s in combinacao_final_str.split(' + ')])
        phi_long_desenho = max([int(s.split('Ø')[1].strip()) for s in combinacao_final_str.split(' + ')])
    except:
        n_barras, phi_long_desenho = 0, 0

    dados_desenho = {"b": b, "h": h, "c_nom": c_nom, "phi_estribo": phi_estribo, "n_barras": n_barras, "phi_long": phi_long_desenho}
    
    resultado = {
        'status': 'Sucesso',
        'mensagem': 'Cálculo iterativo efetuado com sucesso.',
        'combinacao_final': combinacao_final_str,
        'As_final_cm2': f"{As_final_cm2:.2f}",
        'combinacao_unica': solucao_unica,
        'combinacao_mista': solucao_mista,
        'passos': passos,
        'dados_desenho': dados_desenho
    }
    return resultado