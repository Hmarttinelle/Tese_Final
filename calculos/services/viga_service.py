# calculos/services/viga_service.py
import math

# ==============================================================================
# FUNÇÕES AUXILIARES
# ==============================================================================
def encontrar_combinacao_barras_otima(As_req_cm2, b_mm, c_nom_mm, phi_estribo_mm):
    """
    Encontra a combinação ótima de varões (diâmetro e quantidade) que satisfaz
    a área de aço necessária e respeita os espaçamentos mínimos.
    Retorna a solução com a menor área de aço que cumpre os requisitos.
    """
    vergalhoes_padrao = {25: 4.909, 20: 3.142, 16: 2.011, 12: 1.131}
    largura_disponivel = b_mm - 2 * c_nom_mm - 2 * phi_estribo_mm
    solucoes_validas = []
    
    for diametro, area_varao in vergalhoes_padrao.items():
        if area_varao <= 0: continue
        
        n_barras = math.ceil(As_req_cm2 / area_varao)
        if n_barras < 2: n_barras = 2 # Mínimo de 2 varões para uma viga

        # Verificação do espaçamento mínimo (EC2, 8.2)
        espacamento_min = max(diametro, 20) # 20mm ou o diâmetro do varão
        largura_necessaria = n_barras * diametro + (n_barras - 1) * espacamento_min
        
        if largura_necessaria <= largura_disponivel:
            area_total = n_barras * area_varao
            texto_verificacao = f"Para {n_barras}Ø{diametro}: Largura necessária ≈ {largura_necessaria:.0f} mm. Largura disponível = {largura_disponivel:.0f} mm. -> OK"
            solucoes_validas.append({
                "n_barras": n_barras,
                "diametro": diametro,
                "area_total": area_total,
                "verificacao": texto_verificacao
            })
            
    if not solucoes_validas:
        return (0, 0, 0, "Nenhuma combinação de armadura coube numa única camada.")
        
    # Encontra a solução que tem a menor área de aço (mais económica)
    solucao_otima = min(solucoes_validas, key=lambda x: x['area_total'])
    
    return (
        solucao_otima['n_barras'],
        solucao_otima['diametro'],
        solucao_otima['area_total'],
        solucao_otima['verificacao']
    )

# ==============================================================================
# FUNÇÃO PRINCIPAL DE DIMENSIONAMENTO
# ==============================================================================
def dimensionar_viga(b, h, f_ck, f_yk, M_Ed_kNm, c_nom):
    """
    Função principal que realiza o dimensionamento de uma viga à flexão simples.
    Recebe os dados de entrada e retorna um dicionário com o resultado e o passo a passo.
    """
    passos = []
    
    # --- Parâmetros de Cálculo ---
    gamma_c, gamma_s, alpha_cc, lambda_val = 1.5, 1.15, 1.0, 0.8
    f_cd_mpa = alpha_cc * f_ck / gamma_c
    f_yd_mpa = f_yk / gamma_s
    M_Ed_Nm = M_Ed_kNm * 1000
    b_m = b / 1000
    phi_estribo = 8.0 # Diâmetro do estribo assumido para o cálculo

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
    _, phi_long_final, _, _ = encontrar_combinacao_barras_otima(As_req_cm2_temp, b, c_nom, phi_estribo)

    # --- Iteração 2: Recálculo com o diâmetro final para maior precisão ---
    if phi_long_final != phi_long_assumido and phi_long_final != 0:
        passos.append({"titulo": "6. Recálculo (Iteração 2)", "calculo": f"O diâmetro final ótimo ({phi_long_final}mm) é diferente do assumido ({phi_long_assumido}mm). Procede-se a um recálculo para garantir a precisão."})
        
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

    n_barras, phi_long_final, As_prov_cm2, verif_esp = encontrar_combinacao_barras_otima(As_req_cm2, b, c_nom, phi_estribo)
    if n_barras == 0:
        raise ValueError(verif_esp)
    passos.append({"titulo": "8. Proposta de Armadura (Solução Ótima)", "calculo": f"A melhor solução para {As_req_cm2:.2f} cm² é {n_barras}Ø{phi_long_final} ({As_prov_cm2:.2f} cm²).<br>{verif_esp}"})

    # --- Verificações Finais de Armadura Mínima ---
    if f_ck <= 50:
        f_ctm = 0.30 * f_ck**(2/3)
    else:
        f_ctm = 2.12 * math.log(1 + (f_ck + 8) / 10)
    
    as_min_termo1 = 0.26 * (f_ctm / f_yk) * b_m * d_m * 10000
    as_min_termo2 = 0.0013 * b_m * d_m * 10000
    As_min_cm2 = max(as_min_termo1, as_min_termo2)
    
    As_final_cm2 = max(As_prov_cm2, As_min_cm2)
    combinacao_final_str = f"{n_barras} Ø {phi_long_final}"

    calculo_as_min = (f"f_ctm = 0.30 x {f_ck:.0f}^(2/3) = {f_ctm:.2f} MPa<br>"
                      f"As,min₁ = 0.26 x ({f_ctm:.2f} / {f_yk:.0f}) x {b:.0f} x {d:.1f} = {as_min_termo1:.2f} cm²<br>"
                      f"As,min₂ = 0.0013 x {b:.0f} x {d:.1f} = {as_min_termo2:.2f} cm²<br>"
                      f"As,min = max({as_min_termo1:.2f}, {as_min_termo2:.2f}) = {As_min_cm2:.2f} cm²<br>"
                      f"Área de armadura a adotar: max(As,prov, As,min) = max({As_prov_cm2:.2f}, {As_min_cm2:.2f}) = <b>{As_final_cm2:.2f} cm²</b>")
    passos.append({"titulo": "9. Verificação da Armadura Mínima", "formula": r"A_{s,min} = max(0.26\frac{f_{ctm}}{f_{yk}} \cdot b_t \cdot d; 0.0013 \cdot b_t \cdot d)", "calculo": calculo_as_min})

    passos.append({"titulo": "10. Armadura Superior Construtiva (Porta-Estribos)",                 
                   "calculo": "Para garantir a correta montagem da armadura e o posicionamento dos estribos, adota-se uma armadura superior construtiva. "
                                "Adicionalmente, a Sec. 9.2.1.2 da norma exige uma armadura superior nos apoios para resistir a eventuais momentos negativos. "
                                "A prática comum para vigas de edifícios correntes consiste em utilizar uma armadura mínima de <b>2 Ø 10</b>."
    })

    # --- Montagem do resultado final ---
    dados_desenho = {"b": b, "h": h, "c_nom": c_nom, "phi_estribo": phi_estribo, "n_barras": n_barras, "phi_long": phi_long_final}
    resultado = {
        'status': 'Sucesso',
        'mensagem': 'Cálculo iterativo efetuado com sucesso.',
        'combinacao_final': combinacao_final_str,
        'As_final_cm2': f"{As_final_cm2:.2f}",
        'passos': passos,
        'dados_desenho': dados_desenho
    }
    return resultado