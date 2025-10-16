# calculos/services/sapata_service.py
import math

# ==============================================================================
# FUNÇÕES AUXILIARES PARA ENCONTRAR COMBINAÇÃO DE BARRAS OTIMIZADAS
# ==============================================================================

def encontrar_combinacao_barras_otima(As_req_cm2, b_mm, c_nom_mm, phi_estribo_mm):
    vergalhoes_padrao = {25: 4.909, 20: 3.142, 16: 2.011, 12: 1.131} 
    largura_disponivel = b_mm - 2 * c_nom_mm - 2 * phi_estribo_mm
    solucoes_validas = []
    for diametro, area_varao in vergalhoes_padrao.items():
        n_barras = math.ceil(As_req_cm2 / area_varao) if area_varao > 0 else 0
        if n_barras == 0: continue
        if n_barras < 2: n_barras = 2
        espacamento_min = max(diametro, 20, 27)
        largura_necessaria = n_barras * diametro + (n_barras - 1) * espacamento_min
        if largura_necessaria <= largura_disponivel:
            area_total = n_barras * area_varao
            texto_verificacao = f"Para {n_barras}Ø{diametro}: Largura necessária ≈ {largura_necessaria:.0f} mm. Largura disponível = {largura_disponivel:.0f} mm. -> OK"
            solucoes_validas.append({"n_barras": n_barras, "diametro": diametro, "area_total": area_total, "verificacao": texto_verificacao})
    if not solucoes_validas: return (0, 0, 0, "Nenhuma combinação de armadura coube numa única camada.")
    solucao_otima = min(solucoes_validas, key=lambda x: x['area_total'])
    return (solucao_otima['n_barras'], solucao_otima['diametro'], solucao_otima['area_total'], solucao_otima['verificacao'])

# ==============================================================================
# FUNÇÕES AUXILIARES PARA DESENHOS
# ==============================================================================

def desenhar_sapata_planta_svg(dados_desenho):
    A = dados_desenho['A_m']
    B = dados_desenho['B_m']
    bp = dados_desenho['bp_mm'] / 1000
    hp = dados_desenho['hp_mm'] / 1000
    c_nom = dados_desenho['c_nom_mm'] / 1000
    phi_x, esp_x_mm = dados_desenho['phi_x'], dados_desenho['esp_x_mm']
    phi_y, esp_y_mm = dados_desenho['phi_y'], dados_desenho['esp_y_mm']

    padding = 60
    escala = 300 / max(A, B) if max(A, B) > 0 else 1
    largura_svg, altura_svg = A * escala + 2 * padding, B * escala + 2 * padding
    
    svg = f'<svg width="100%" viewBox="0 0 {largura_svg} {altura_svg}" xmlns="http://www.w3.org/2000/svg">'
    svg += '<style>.dim-text { font-family: Arial, sans-serif; font-size: 12px; fill: #333; text-anchor: middle; }</style>'
    svg += f'<rect x="0" y="0" width="{largura_svg}" height="{altura_svg}" fill="#f9f9f9"/>'
    svg += f'<rect x="{padding}" y="{padding}" width="{A*escala}" height="{B*escala}" fill="#ececec" stroke="#333" stroke-width="2"/>'
    x_pilar, y_pilar = padding + (A - bp) / 2 * escala, padding + (B - hp) / 2 * escala
    svg += f'<rect x="{x_pilar}" y="{y_pilar}" width="{bp*escala}" height="{hp*escala}" fill="#c0c0c0" stroke="#333" stroke-width="1"/>'
    if phi_x > 0 and esp_x_mm > 0:
        num_barras_x = int(B / (esp_x_mm / 1000))
        for i in range(1, num_barras_x):
            y_i = padding + i * (esp_x_mm / 1000) * escala
            if y_i > padding + B*escala - c_nom*escala: break
            svg += f'<line x1="{padding + c_nom*escala}" y1="{y_i}" x2="{padding + A*escala - c_nom*escala}" y2="{y_i}" stroke="#005a9e" stroke-width="{max(1, phi_x/4)}"/>'
    if phi_y > 0 and esp_y_mm > 0:
        num_barras_y = int(A / (esp_y_mm / 1000))
        for i in range(1, num_barras_y):
            x_i = padding + i * (esp_y_mm / 1000) * escala
            if x_i > padding + A*escala - c_nom*escala: break
            svg += f'<line x1="{x_i}" y1="{padding + c_nom*escala}" x2="{x_i}" y2="{padding + B*escala - c_nom*escala}" stroke="#cc0000" stroke-width="{max(1, phi_y/4)}"/>'
    y_cota_a = padding + B * escala + padding/2
    svg += f'<path d="M {padding} {y_cota_a - 10} L {padding} {y_cota_a + 10} M {padding} {y_cota_a} L {padding + A*escala} {y_cota_a} M {padding + A*escala} {y_cota_a - 10} L {padding + A*escala} {y_cota_a + 10}" stroke="#333" stroke-width="1" fill="none"/>'
    svg += f'<text x="{padding + A*escala/2}" y="{y_cota_a - 5}" class="dim-text">{B:.2f} m</text>'
    x_cota_b = padding / 2
    svg += f'<path d="M {x_cota_b - 10} {padding} L {x_cota_b + 10} {padding} M {x_cota_b} {padding} L {x_cota_b} {padding + B*escala} M {x_cota_b - 10} {padding + B*escala} L {x_cota_b + 10} {padding + B*escala}" stroke="#333" stroke-width="1" fill="none"/>'
    svg += f'<text x="{x_cota_b - 5}" y="{padding + B*escala/2}" class="dim-text" transform="rotate(-90, {x_cota_b - 5}, {padding + B*escala/2})">{A:.2f} m</text>'
    svg += '</svg>'
    return svg

def desenhar_sapata_corte_svg(dados_desenho):
    A, H, bp, c_nom, phi_x = dados_desenho['A_m'], dados_desenho['H_mm'] / 1000, dados_desenho['bp_mm'] / 1000, dados_desenho['c_nom_mm'] / 1000, dados_desenho['phi_x']
    padding, escala = 50, 350 / A if A > 0 else 1
    largura_svg, altura_svg = A * escala + 2 * padding, H * escala + 2 * padding + 30
    svg = f'<svg width="100%" viewBox="0 0 {largura_svg} {altura_svg}" xmlns="http://www.w3.org/2000/svg">'
    svg += '<style>.dim-text { font-family: Arial, sans-serif; font-size: 12px; fill: #333; text-anchor: middle; }</style>'
    svg += f'<rect x="0" y="0" width="{largura_svg}" height="{altura_svg}" fill="#f9f9f9"/>'
    y_base = padding + 30
    svg += f'<rect x="{padding}" y="{y_base}" width="{A*escala}" height="{H*escala}" fill="#ececec" stroke="#333" stroke-width="2"/>'
    x_pilar = padding + (A - bp) / 2 * escala
    svg += f'<rect x="{x_pilar}" y="{y_base - 30}" width="{bp*escala}" height="30" fill="#c0c0c0" stroke="#333" stroke-width="1"/>'
    if phi_x > 0:
        num_barras = min(int(A / 0.15), 10); esp_barras = (A * escala - 2 * c_nom * escala) / (num_barras -1) if num_barras > 1 else 0
        cy = y_base + H * escala - c_nom * escala - (phi_x/2000*escala)
        for i in range(num_barras):
            cx = padding + c_nom*escala + i * esp_barras
            svg += f'<circle cx="{cx}" cy="{cy}" r="{phi_x/2000*escala}" fill="#005a9e" stroke="#333" stroke-width="0.5"/>'
    y_cota_a, x_cota_h = y_base + H * escala + padding/2, padding + A * escala + padding/2
    svg += f'<path d="M {padding} {y_cota_a - 10} L {padding} {y_cota_a + 10} M {padding} {y_cota_a} L {padding + A*escala} {y_cota_a} M {padding + A*escala} {y_cota_a - 10} L {padding + A*escala} {y_cota_a + 10}" stroke="#333" stroke-width="1" fill="none"/>'
    svg += f'<text x="{padding + A*escala/2}" y="{y_cota_a - 5}" class="dim-text">{A:.2f} m</text>'
    svg += f'<path d="M {x_cota_h-10} {y_base} L {x_cota_h+10} {y_base} M {x_cota_h} {y_base} L {x_cota_h} {y_base+H*escala} M {x_cota_h-10} {y_base+H*escala} L {x_cota_h+10} {y_base+H*escala}" stroke="#333" stroke-width="1" fill="none"/>'
    svg += f'<text x="{x_cota_h + 15}" y="{y_base + H*escala/2}" class="dim-text" transform="rotate(90, {x_cota_h + 15}, {y_base + H*escala/2})">{H*1000:.0f} mm</text>'
    svg += '</svg>'
    return svg

# ==============================================================================
# FUNÇÃO PRINCIPAL DE DIMENSIONAMENTO 
# ==============================================================================
def dimensionar_sapata(sigma_adm_kpa, f_ck, f_yk, c_nom_mm, bp_mm, hp_mm, N_Ed_kN, M_Edy_kNm):
    passos = []
    gamma_g_avg = 1.4
    
    passos.append({"titulo": "FASE 1: DIMENSIONAMENTO GEOTÉCNICO (ELS)", "calculo": "Objetivo: encontrar as dimensões em planta (A x B) da sapata que garantem que as tensões no solo são admissíveis."})
    
    N_k_kN = N_Ed_kN / gamma_g_avg
    M_ky_kNm = M_Edy_kNm / gamma_g_avg
    passos.append({"titulo": "1.1. Esforços de Serviço (ELS)", "formula": r"N_k = \frac{N_{Ed}}{\gamma_{G,avg}} \, ; \, M_k = \frac{M_{Ed}}{\gamma_{G,avg}}", "calculo": f"N_k ≈ {N_Ed_kN:.2f} / {gamma_g_avg} = {N_k_kN:.2f} kN<br>M_k,y ≈ {M_Edy_kNm:.2f} / {gamma_g_avg} = {M_ky_kNm:.2f} kNm"})

    A_req_preliminar = N_k_kN / sigma_adm_kpa if sigma_adm_kpa > 0 else 1.0
    A_majorada = A_req_preliminar * 1.2
    
    calculo_estimativa = f"Área teórica necessária = {N_k_kN:.2f} kN / {sigma_adm_kpa} kPa = {A_req_preliminar:.2f} m²<br>"
    calculo_estimativa += f"Área majorada (≈+20% para peso próprio e momentos) = {A_req_preliminar:.2f} x 1.20 = {A_majorada:.2f} m²<br>"
    
    if bp_mm == hp_mm:
        A_m = math.sqrt(A_majorada)
        B_m = A_m
        calculo_estimativa += f"Como o pilar é quadrado, a sapata será quadrada: A = B = √{A_majorada:.2f} = {A_m:.2f} m"
    else:
        proporcao = hp_mm / bp_mm if bp_mm > 0 else 1
        A_m = math.sqrt(A_majorada / proporcao)
        B_m = A_m * proporcao
        calculo_estimativa += f"Como o pilar é retangular, a sapata mantém a proporção ({proporcao:.2f}): B ≈ {proporcao:.2f} * A<br>"
        calculo_estimativa += f"A ≈ √({A_majorada:.2f} / {proporcao:.2f}) = {A_m:.2f} m<br>"
        calculo_estimativa += f"B ≈ {A_m:.2f} * {proporcao:.2f} = {B_m:.2f} m"

    passos.append({"titulo": "1.2. Estimativa Inicial das Dimensões", "formula": r"A_{req} = \frac{N_k}{\sigma_{adm}} \, ; \, A_{maj} = A_{req} \cdot 1.20", "calculo": calculo_estimativa})
    
    for i in range(50):
        H_estimado_m = max(A_m, B_m) / 8 if max(A_m, B_m) / 8 > 0.4 else 0.4
        W_k_kN = A_m * B_m * H_estimado_m * 25
        N_total_k_kN = N_k_kN + W_k_kN
        e_y_m = M_ky_kNm / N_total_k_kN if N_total_k_kN > 0 else 0
        
        sigma_max_kpa_real = (N_total_k_kN / (A_m * B_m)) * (1 + 6 * e_y_m / B_m) if (A_m * B_m) > 0 else 0
        sigma_min_kpa_real = (N_total_k_kN / (A_m * B_m)) * (1 - 6 * e_y_m / B_m) if (A_m * B_m) > 0 else 0

        calculo_iter = f"<b>Tentativa #{i+1} com A={A_m:.2f}m, B={B_m:.2f}m</b><br>"
        calculo_iter += f"H_estimado (Regra empírica: max(A,B)/8 ≥ 0.4m) = max({A_m:.2f}, {B_m:.2f})/8 = {max(A_m, B_m)/8:.3f}m. Adota-se {H_estimado_m:.2f}m<br>"
        calculo_iter += f"W_k = {A_m:.2f} x {B_m:.2f} x {H_estimado_m:.2f} x 25 = {W_k_kN:.2f} kN<br>"
        calculo_iter += f"N_total,k = {N_k_kN:.2f} + {W_k_kN:.2f} = {N_total_k_kN:.2f} kN<br>"
        calculo_iter += f"e_y = {M_ky_kNm:.2f} / {N_total_k_kN:.2f} = {e_y_m:.3f} m<br>"
        calculo_iter += f"Limite (B/6) = {B_m/6:.3f} m.  Verificação: {e_y_m:.3f} ≤ {B_m/6:.3f} -> {'OK' if e_y_m <= B_m / 6 else 'FALHOU'}<br>"
        
        if e_y_m > B_m / 6:
            passos.append({"titulo": f"1.3. Iteração Geotécnica", "calculo": calculo_iter + "<br><b>A excentricidade é muito elevada. A aumentar dimensões...</b>"})
            B_m += 0.05; A_m = B_m * (bp_mm / hp_mm) if hp_mm > 0 else B_m
            continue
        
        calculo_iter += f"σ_max = ({N_total_k_kN:.2f} / ({A_m:.2f}x{B_m:.2f})) x (1 + 6x{e_y_m:.3f}/{B_m:.2f}) = {sigma_max_kpa_real:.2f} kPa<br>"
        calculo_iter += f"σ_min = ({N_total_k_kN:.2f} / ({A_m:.2f}x{B_m:.2f})) x (1 - 6x{e_y_m:.3f}/{B_m:.2f}) = {sigma_min_kpa_real:.2f} kPa<br>"
        calculo_iter += f"Verificação σ_max: {sigma_max_kpa_real:.2f} kPa ≤ {sigma_adm_kpa} kPa -> {'OK' if sigma_max_kpa_real <= sigma_adm_kpa else 'FALHOU'}<br>"
        calculo_iter += f"Verificação σ_min: {sigma_min_kpa_real:.2f} kPa ≥ 0 kPa -> {'OK' if sigma_min_kpa_real >= 0 else 'FALHOU'}"
        passos.append({"titulo": f"1.3. Iteração Geotécnica", "formula": r"H_{est} \approx \frac{max(A,B)}{8} \, ; \, W_k = A{\cdot}B{\cdot}H_{est}{\cdot}\gamma_{c} \, ; \, N_{total,k} = N_k + W_k \, ; \,e_y = \frac{M_k}{N_{total,k}} \, ; \, \sigma_{max,min} = \frac{N_{total,k}}{A \cdot B} (1 \pm \frac{6e_y}{B})", "calculo": calculo_iter})
        
        if sigma_max_kpa_real <= sigma_adm_kpa and sigma_min_kpa_real >= 0:
            break
        B_m += 0.05
        A_m = B_m * (bp_mm / hp_mm) if hp_mm > 0 else B_m
    else: raise ValueError("Não foi possível encontrar dimensões geotécnicas válidas.")

    A_final_m, B_final_m = math.ceil(A_m*20)/20, math.ceil(B_m*20)/20
    passos.append({"titulo": "1.4. Dimensões Finais em Planta", "calculo": f"Adotam-se as dimensões da última iteração válida, arredondadas para o múltiplo de 5 cm superior:<br><b>A = {A_final_m:.2f} m</b><br><b>B = {B_final_m:.2f} m</b>"})
    
    passos.append({"titulo": "FASE 2: DIMENSIONAMENTO ESTRUTURAL (ELU)", "calculo": "Objetivo: encontrar a altura (H) e as armaduras para resistir aos esforços de cálculo."})

    gamma_c, gamma_s = 1.5, 1.15; f_cd_mpa, f_yd_mpa = f_ck/gamma_c, f_yk/gamma_s
    passos.append({"titulo": "2.1. Parâmetros dos Materiais (ELU)", "formula": r"f_{cd} = \frac{f_{ck}}{\gamma_c} \, ; \, f_{yd} = \frac{f_{yk}}{\gamma_s}", "calculo": f"f_cd = {f_ck:.0f} / {gamma_c} = {f_cd_mpa:.2f} MPa<br>f_yd = {f_yk:.0f} / {gamma_s} = {f_yd_mpa:.2f} MPa"})
    
    sigma_Ed_kpa = N_Ed_kN/(A_final_m*B_final_m) if (A_final_m*B_final_m)>0 else 0
    passos.append({"titulo": "2.2. Tensão de Cálculo no Solo (ELU)", "formula": r"\sigma_{Ed} = \frac{N_{Ed}}{A \cdot B}", "calculo": f"σ_Ed = {N_Ed_kN:.2f} / ({A_final_m:.2f} x {B_final_m:.2f}) = {sigma_Ed_kpa:.2f} kPa"})
    
    d_pre_rigidez = (max(A_final_m, B_final_m)*1000 - max(bp_mm, hp_mm))/3
    calculo_d_pre = f"Para garantir um comportamento de sapata rígida, a altura útil (d) pode ser pré-dimensionada para ser superior a um terço do voo.<br>" + \
                    f"d ≥ (B - h_p) / 3 = ({B_final_m*1000:.0f} - {hp_mm}) / 3 = {d_pre_rigidez:.0f} mm<br>" + \
                    "A verificação ao punçoamento determinará a altura final."
    passos.append({"titulo":"2.3. Pré-dimensionamento da Altura (d)", "formula":r"d \ge \frac{B-h_p}{3}", "calculo":calculo_d_pre})
    
    d_m, H_final_mm = 0.15, 0
    for i in range(50):
        d_mm_iter = d_m*1000; u1 = 2*(bp_mm+hp_mm)+math.pi*2*d_mm_iter; Acrit_m2 = (bp_mm/1000+math.pi*d_m)*(hp_mm/1000+math.pi*d_m)
        V_Ed_pun_kN = N_Ed_kN - sigma_Ed_kpa*Acrit_m2; k = min(2.0, 1+math.sqrt(200/d_mm_iter)) if d_m>0 else 1.0; rho_l = 0.005
        VRd_c_pun_kN = (0.18/gamma_c)*k*(100*rho_l*f_ck)**(1/3)*(u1/1000)*d_m*1000 if d_m>0 else 0
        if VRd_c_pun_kN > V_Ed_pun_kN:
            formula_pun = r"u_1 = 2(b_p+h_p) + 2\pi d \, ; \, A_{crit} = (b_p+\pi d)(h_p+\pi d) \, ; \, k = 1+\sqrt{\frac{200}{d}} \le 2.0"
            formula_pun += r"\, ; \, V_{Ed} = N_{Ed} - \sigma_{Ed} \cdot A_{crit} \, ; \, V_{Rd,c} = \frac{0.18}{\gamma_c} k (100 \rho_l f_{ck})^{1/3} u_1 d"

            calculo_pun = "A altura útil (d) é determinada pelo programa de forma iterativa, aumentando 'd' em incrementos de 10mm desde 150mm até que V_Ed ≤ V_Rd,c.<br>" + \
                          f"<b>Verificação para a altura útil final d = {d_m*1000:.0f} mm:</b><br>" + \
                          f"Perímetro crítico u₁ = 2({bp_mm}+{hp_mm}) + 2π({d_m*1000:.0f}) = {u1:.0f} mm<br>" + \
                          f"Área crítica A_crit = ({bp_mm/1000:.3f} + π*{d_m:.3f}) * ({hp_mm/1000:.3f} + π*{d_m:.3f}) = {Acrit_m2:.2f} m²<br>" + \
                          f"Taxa de armadura ρ_l = {rho_l*100:.1f}% (valor prático e seguro assumido para a verificação ao punçoamento)<br>" + \
                          f"k = 1 + √(200/{d_m*1000:.0f}) = {k:.3f} (≤ 2.0)<br>" + \
                          f"V_Ed = {N_Ed_kN:.2f} - {sigma_Ed_kpa:.2f} x {Acrit_m2:.2f} = {V_Ed_pun_kN:.2f} kN<br>" + \
                          f"V_Rd,c = (0.18/{gamma_c}) x {k:.3f} x (100x{rho_l}x{f_ck})^(1/3) x {u1/1000:.3f} x {d_m:.3f} x 1000 = {VRd_c_pun_kN:.2f} kN<br>" + \
                          f"<b>Condição: {V_Ed_pun_kN:.2f} kN ≤ {VRd_c_pun_kN:.2f} kN -> OK</b><br>"
            H_m, H_final_mm = d_m + c_nom_mm/1000 + 0.016, math.ceil((d_m + c_nom_mm/1000 + 0.016)*1000/50)*50
            calculo_pun += f"<br>Como d={d_m*1000:.0f}mm foi o primeiro valor a cumprir o requisito, é este o valor adotado.<br>" + \
                            f"Altura Total (H) = d + c_nom + ø/2 ≈ {d_m*1000:.0f} + {c_nom_mm} + 16/2 = {d_m*1000+c_nom_mm+8:.0f} mm.<br>" + \
                            f"(Nota: Adota-se um diâmetro de armadura comum e seguro, ø16, para esta estimativa de H)<br>" + \
                           f"Arredondando para múltiplo de 50mm: <b>H = {H_final_mm:.0f} mm</b>"
            passos.append({"titulo":"2.4. Altura da Sapata (Punçoamento)", "formula":formula_pun, "calculo":calculo_pun})
            break
        d_m += 0.01
    else: raise ValueError("Não foi possível determinar uma altura válida contra o punçoamento.")
    
    passos.append({"titulo": "FASE 3: DIMENSIONAMENTO À FLEXÃO (ELU)", "calculo": "Objetivo: calcular a armadura necessária em cada direção."})
    
    n_barras_y_m_temp, phi_y_temp, _, _ = encontrar_combinacao_barras_otima(1, 1000, c_nom_mm, 0)
    n_barras_x_m_temp, phi_x_temp, _, _ = encontrar_combinacao_barras_otima(1, 1000, c_nom_mm, 0)
    phi_maior = max(phi_x_temp, phi_y_temp)
    phi_menor = min(phi_x_temp, phi_y_temp)
    d_flex_x = (H_final_mm - c_nom_mm - phi_maior/2) / 1000
    d_flex_y = (H_final_mm - c_nom_mm - phi_maior - phi_menor/2) / 1000

    ly = (B_final_m - hp_mm/1000) / 2
    M_Edy_flex_kNm_m = (sigma_Ed_kpa * ly**2) / 2 
    Asy_req_cm2_m = (M_Edy_flex_kNm_m / (0.9 * d_flex_y * f_yd_mpa * 1000)) * 10000 if d_flex_y > 0 else 0

    calculo_asy = f"Voo da sapata: l_y = ({B_final_m:.2f} - {hp_mm/1000:.2f}) / 2 = {ly:.3f} m<br>" + \
                  f"Momento por metro: M_Ed,y = ({sigma_Ed_kpa:.2f} x {ly:.3f}²) / 2 = {M_Edy_flex_kNm_m:.2f} kNm/m<br>" + \
                  f"Altura útil (d_y): {H_final_mm} - {c_nom_mm} - ø_x - ø_y/2 ≈ {d_flex_y*1000:.1f} mm<br>" + \
                  f"As,y,req ≈ {M_Edy_flex_kNm_m:.2f} / (0.9 x {d_flex_y:.3f} x {f_yd_mpa*1000:.2f}) x 10000 = {Asy_req_cm2_m:.2f} cm²/m"
    passos.append({"titulo": "3.1 Armadura na direção Y", "formula": r"l_y = \frac{B-h_p}{2} \, ; \, M_{Ed,y} = \frac{\sigma_{Ed} \cdot l_y^2}{2} \, ; \, A_{s,y} \approx \frac{M_{Ed,y}}{0.9d \cdot f_{yd}}", "calculo": calculo_asy})
    
    lx, M_Edx_flex_kNm_m = (A_final_m - bp_mm/1000)/2, (sigma_Ed_kpa * ((A_final_m - bp_mm/1000)/2)**2)/2
    Asx_req_cm2_m = (M_Edx_flex_kNm_m / (0.9 * d_flex_x * f_yd_mpa * 1000)) * 10000 if d_flex_x > 0 else 0

    calculo_asx = f"Voo da sapata: l_x = ({A_final_m:.2f} - {bp_mm/1000:.2f}) / 2 = {lx:.3f} m<br>" + \
                  f"Momento por metro: M_Ed,x = ({sigma_Ed_kpa:.2f} x {lx:.3f}²) / 2 = {M_Edx_flex_kNm_m:.2f} kNm/m<br>" + \
                  f"Altura útil (d_x): {H_final_mm} - {c_nom_mm} - ø_x/2 ≈ {d_flex_x*1000:.1f} mm<br>" + \
                  f"As,x,req ≈ {M_Edx_flex_kNm_m:.2f} / (0.9 x {d_flex_x:.3f} x {f_yd_mpa*1000:.2f}) x 10000 = {Asx_req_cm2_m:.2f} cm²/m"
    passos.append({"titulo": "3.2 Armadura na direção X", "formula": r"l_x = \frac{A-b_p}{2} \, ; \, M_{Ed,x} = \frac{\sigma_{Ed} \cdot l_x^2}{2} \, ; \, A_{s,x} \approx \frac{M_{Ed,x}}{0.9d \cdot f_{yd}}", "calculo": calculo_asx})
    
    f_ctm = 0.3 * f_ck**(2/3)
    As_min_cm2 = max(0.26 * (f_ctm/f_yk) * 1 * d_flex_x, 0.0013 * 1 * d_flex_x) * 10000
    Asy_final_cm2_m, Asx_final_cm2_m = max(Asy_req_cm2_m, As_min_cm2), max(Asx_req_cm2_m, As_min_cm2)

    calculo_as_min = f"f_ctm = 0.30 x {f_ck}^(2/3) = {f_ctm:.2f} MPa<br>" + \
                     f"As,min = max(0.26 x ({f_ctm:.2f}/{f_yk}) x 1000 x {d_flex_x*1000:.1f}; ...) = {As_min_cm2:.2f} cm²/m<br>" + \
                     f"<b>As,x final = max({Asx_req_cm2_m:.2f}, {As_min_cm2:.2f}) = {Asx_final_cm2_m:.2f} cm²/m</b><br>" + \
                     f"<b>As,y final = max({Asy_req_cm2_m:.2f}, {As_min_cm2:.2f}) = {Asy_final_cm2_m:.2f} cm²/m</b>"
    passos.append({"titulo": "3.3 Verificação da Armadura Mínima", "formula": r"A_{s,min} = max(0.26\frac{f_{ctm}}{f_{yk}} b_t d; 0.0013 b_t d)", "calculo": calculo_as_min})
    
    n_barras_y_m, phi_y, as_prov_y_m, _ = encontrar_combinacao_barras_otima(Asy_final_cm2_m, 1000, c_nom_mm, 0)
    n_barras_x_m, phi_x, as_prov_x_m, _ = encontrar_combinacao_barras_otima(Asx_final_cm2_m, 1000, c_nom_mm, 0)
    
    if n_barras_x_m == 0 or n_barras_y_m == 0: raise ValueError("Não foi possível encontrar uma combinação de armadura válida.")
    
    texto_escolha_arm = f"Para a direção X (As,final={Asx_final_cm2_m:.2f} cm²/m), a melhor solução é {n_barras_x_m}Ø{phi_x}.<br>" + \
                        f"Para a direção Y (As,final={Asy_final_cm2_m:.2f} cm²/m), a melhor solução é {n_barras_y_m}Ø{phi_y}.<br>" + \
                        "A escolha é baseada na combinação que satisfaz a área de aço com a menor área total, garantindo espaçamentos construtivos."
    passos.append({"titulo":"3.4. Escolha da Armadura Final", "calculo":texto_escolha_arm})
    
    esp_y, esp_x = 1000/n_barras_y_m if n_barras_y_m>0 else 0, 1000/n_barras_x_m if n_barras_x_m>0 else 0

    dados_desenho = {"A_m":A_final_m, "B_m":B_final_m, "H_mm":H_final_mm, "bp_mm":bp_mm, "hp_mm":hp_mm, "c_nom_mm":c_nom_mm, "phi_x":phi_x, "esp_x_mm":esp_x, "phi_y":phi_y, "esp_y_mm":esp_y}
    resultado = {"status":"Sucesso", "mensagem":"Cálculo efetuado com sucesso.", "passos":passos, "dimensoes":f"{A_final_m:.2f}m x {B_final_m:.2f}m x {H_final_mm/1000:.2f}m", "armadura_y":f"Ø{phi_y} c/ {esp_y:.0f} mm ({as_prov_y_m:.2f} cm²/m)", "armadura_x":f"Ø{phi_x} c/ {esp_x:.0f} mm ({as_prov_x_m:.2f} cm²/m)", "dados_desenho":dados_desenho}
    resultado['desenho_planta_svg'] = desenhar_sapata_planta_svg(dados_desenho)
    resultado['desenho_corte_svg'] = desenhar_sapata_corte_svg(dados_desenho)
    return resultado