# calculos/services/pilar_service.py
import math

# ==============================================================================
# FUNÇÕES AUXILIARES PARA ENCONTRAR COMBINAÇÃO DE BARRAS OTIMIZADAS
# ==============================================================================

def encontrar_combinacao_barras_pilar(As_req_cm2, b_mm, h_mm, c_nom_mm, phi_estribo_mm):
    vergalhoes_padrao = {25: 4.909, 20: 3.142, 16: 2.011, 12: 1.131, 10: 0.785}
    solucoes_validas = []
    for diametro, area_varao in vergalhoes_padrao.items():
        n_barras = math.ceil(As_req_cm2 / area_varao) if area_varao > 0 else 0
        if n_barras == 0: continue
        if n_barras < 4: n_barras = 4
        if n_barras % 2 != 0: n_barras += 1
        
        n_barras_por_face_maior = math.ceil(n_barras / 2)
        largura_disponivel = h_mm - 2 * c_nom_mm - 2 * phi_estribo_mm
        espacamento_min = max(diametro, 20, 27)
        largura_necessaria = n_barras_por_face_maior * diametro + (n_barras_por_face_maior - 1) * espacamento_min if n_barras_por_face_maior > 1 else n_barras_por_face_maior * diametro
        
        if largura_necessaria <= largura_disponivel:
            area_total = n_barras * area_varao
            solucoes_validas.append({"n_barras": int(n_barras), "diametro": diametro, "area_total": area_total})
    if not solucoes_validas: return (0, 0, 0)
    solucao_otima = min(solucoes_validas, key=lambda x: x['area_total'])
    return (solucao_otima['n_barras'], solucao_otima['diametro'], solucao_otima['area_total'])

def _dimensionar_pilar_rigoroso(b_mm, h_mm, f_cd_mpa, f_yd_mpa, N_Ed_N, M_Ed_total_Nm, c_nom_mm, passos_ref):
    lambda_val, eta, Es_mpa = 0.8, 1.0, 200000
    d_linha_mm = c_nom_mm + 8 + 16/2
    d_mm = h_mm - d_linha_mm
    epsilon_cu3, epsilon_s_ced = 0.0035, f_yd_mpa / Es_mpa
    Ac_mm2 = b_mm * h_mm
    As_total_req_mm2 = max(0.10 * N_Ed_N / f_yd_mpa, 0.002 * Ac_mm2)
    
    calculo_iterativo_str = ""
    
    for i in range(100):
        As_face_mm2 = As_total_req_mm2 / 2
        x_min, x_max = 0.001, h_mm * 2
        x = (x_min + x_max) / 2
        
        for j in range(50):
            epsilon_sc = epsilon_cu3 * (x - d_linha_mm) / x if x > 0 else 0
            epsilon_st = epsilon_cu3 * (d_mm - x) / x if x > 0 else 0
            sigma_sc = max(-f_yd_mpa, min(Es_mpa * epsilon_sc, f_yd_mpa))
            sigma_st = max(-f_yd_mpa, min(Es_mpa * epsilon_st, f_yd_mpa))
            Fc = eta * f_cd_mpa * b_mm * (lambda_val * x) if x > 0 else 0
            Fsc = As_face_mm2 * sigma_sc
            Fst = As_face_mm2 * sigma_st
            NRd = Fc + Fsc - Fst
            if abs(NRd - N_Ed_N) < 0.001 * abs(N_Ed_N): break
            if NRd < N_Ed_N: x_min = x
            else: x_max = x
            x = (x_min + x_max) / 2
        
        z_c = h_mm / 2 - (lambda_val * x) / 2
        z_s = h_mm / 2 - d_linha_mm
        MRd_Nmm = (Fc * z_c + Fsc * z_s + Fst * z_s)
        
        if i == 0:
             calculo_iterativo_str += f"<b>Início da Iteração:</b><br>Começa-se com a armadura mínima (As,req = {As_total_req_mm2/100:.2f} cm²).<br>"
             calculo_iterativo_str += f"Verifica-se qual o momento que esta armadura resiste (MRd).<br>"
             calculo_iterativo_str += f"Para As = {As_total_req_mm2/100:.2f} cm² e NEd = {N_Ed_N/1000:.1f} kN, o equilíbrio de forças é atingido para x = {x:.1f} mm.<br>"
             calculo_iterativo_str += f"Com este x, o momento resistente é MRd = {MRd_Nmm/1000000:.2f} kNm.<br>"

        if MRd_Nmm >= M_Ed_total_Nm * 1000:
            calculo_iterativo_str += (
                f"<b>Conclusão:</b> O momento resistente (MRd = {MRd_Nmm/1000000:.2f} kNm) é superior ao momento de cálculo (MEd = {M_Ed_total_Nm/1000:.2f} kNm).<br>"
                f"A armadura é, portanto, suficiente."
            )
            passos_ref.append({
                "titulo": "6. Área de Aço Calculada (Método Iterativo)",
                "formula": r"N_{Rd} = F_c + F_{sc} - F_{st} \implies M_{Rd} \ge M_{Ed}",
                "calculo": calculo_iterativo_str
            })
            return As_total_req_mm2

        As_total_req_mm2 *= 1.05

    raise ValueError("O algoritmo de dimensionamento do pilar não convergiu.")

# ==============================================================================
# FUNÇÃO PRINCIPAL DE DIMENSIONAMENTO 
# ==============================================================================
def dimensionar_pilar(b_mm, h_mm, l_m, lig_topo, lig_base, f_ck, f_yk, N_Ed_kN, M0_Ed_kNm, c_nom_mm, phi_ef):
    passos = []
    
    casos_beta = {"encab-encab": 0.7, "encab-artic": 0.85, "encab-livre": 2.2, "artic-encab": 0.85, "artic-artic": 1.0, "livre-encab": 2.2}
    caso = f"{lig_topo}-{lig_base}"
    beta = casos_beta.get(caso, 1.0)
    if lig_base == 'livre' or (lig_topo == 'livre' and not lig_base == 'encab'): raise ValueError("Combinação de ligações instável.")
    l0_m = beta * l_m
    calculo_l0 = f"Para ligação {lig_topo}-{lig_base}, β = {beta}<br>l₀ = {beta} x {l_m} = {l0_m:.2f} m"
    passos.append({"titulo": "1. Comprimento de Encurvadura (l₀)", "formula": r"l_0 = \beta \cdot l", "calculo": calculo_l0})

    gamma_c, gamma_s, Es_mpa = 1.5, 1.15, 200000
    f_cd_mpa = f_ck / gamma_c
    f_yd_mpa = f_yk / gamma_s
    N_Ed_N = N_Ed_kN * 1000
    M0_Ed_Nm = M0_Ed_kNm * 1000
    Ac_mm2 = b_mm * h_mm
    passos.append({"titulo": "2. Parâmetros de Cálculo", "calculo": f"f_cd = {f_ck:.0f} / {gamma_c} = {f_cd_mpa:.2f} MPa<br>f_yd = {f_yk:.0f} / {gamma_s} = {f_yd_mpa:.2f} MPa"})
    
    i_mm = h_mm / math.sqrt(12)
    esbelteza = (l0_m * 1000) / i_mm if i_mm > 0 else 0
    calculo_lambda = f"i = {h_mm:.0f} / √12 = {i_mm:.1f} mm<br>λ = {l0_m * 1000:.0f} / {i_mm:.1f} = {esbelteza:.2f}"
    passos.append({"titulo": "3. Verificação de Esbelteza (λ)", "formula": r"i = \frac{h}{\sqrt{12}} \, ; \, \lambda = \frac{l_0}{i}", "calculo": calculo_lambda})
    
    n = N_Ed_N / (Ac_mm2 * f_cd_mpa) if (Ac_mm2 * f_cd_mpa) > 0 else 0
    A = 1 / (1 + 0.2 * phi_ef)
    B, C = 1.1, 0.7 
    lambda_lim = 20 * A * B * C / math.sqrt(n) if n > 0 else float('inf')
    calculo_lambda_lim = f"n = {N_Ed_N:.0f} / (({b_mm:.0f} x {h_mm:.0f}) x {f_cd_mpa:.2f}) = {n:.3f}<br>A = 1 / (1 + 0.2 x {phi_ef:.1f}) = {A:.3f}<br>λ_lim = (20 x {A:.3f} x {B:.1f} x {C:.1f}) / √n = {lambda_lim:.2f}"
    passos.append({"titulo": "3.1. Esbelteza Limite (λ_lim)", "formula": r"n = \frac{N_{Ed}}{A_c×f_{cd}} \, ; \, \lambda_{lim} = \frac{20 × A ×B × C}{\sqrt{n}}", "calculo": calculo_lambda_lim})

    M_Ed_total_Nm = M0_Ed_Nm
    
    if esbelteza > lambda_lim:
        passos.append({"titulo": "3.2. Conclusão", "calculo": "Pilar esbelto. A considerar efeitos de 2ª ordem."})
        
        As_est_mm2 = max(0.10 * N_Ed_N / f_yd_mpa, 0.002 * Ac_mm2)
        omega = (As_est_mm2 * f_yd_mpa) / (Ac_mm2 * f_cd_mpa)
        n_u = 1 + omega
        n_bal = 0.4
        K_r = (n_u - n) / (n_u - n_bal) if (n_u - n_bal) > 0 else 1.0
        K_r = min(K_r, 1.0)
        
        beta_creep = 0.35 + f_ck/200 - esbelteza/150
        K_phi = 1 + beta_creep * phi_ef if (1 + beta_creep * phi_ef) > 1 else 1.0
        
        d_estimado_mm = h_mm - c_nom_mm - 8 - 16 / 2
        inv_r0 = (f_yd_mpa / Es_mpa) / (0.45 * d_estimado_mm) if d_estimado_mm > 0 else 0
        inv_r = K_r * K_phi * inv_r0
        
        e2_mm = inv_r * (l0_m * 1000)**2 / 10
        M2_Ed_Nm = N_Ed_N * (e2_mm / 1000)
        M_Ed_total_Nm = M0_Ed_Nm + M2_Ed_Nm
        
        formula_m2 = (r"\displaylines{"
            r"\frac{1}{r_0} = \frac{\epsilon_{yd}}{0.45d} \ ; \ "
            r"\omega = \frac{A_s f_{yd}}{A_c f_{cd}} \ ; \ K_r = \frac{n_u - n}{n_u - n_{bal}} \ ; \\ "
            r"\beta = 0.35 + \frac{f_{ck}}{200} - \frac{\lambda}{150} \ ; \ K_\phi = 1 + \beta \cdot \phi_{ef} \ ; \ "
            r"\frac{1}{r} = K_r K_\phi \frac{1}{r_0} \ ; \ e_2 = \frac{(1/r) l_0^2}{c} \ ; \ M_2 = N_{Ed} \cdot e_2"
            r"}"
        )
       
        calculo_m2 =  f"<b>a) Curvatura (1/r) - (EC2, exp. 5.34)</b><br>"
        calculo_m2 += f"1/r₀ = ({f_yd_mpa:.2f} / {Es_mpa:.0f}) / (0.45 x {d_estimado_mm:.1f}) = {inv_r0:.8f} mm⁻¹<br>"
        calculo_m2 += f"ω (com As,min) = ({As_est_mm2:.0f} · {f_yd_mpa:.2f}) / ({Ac_mm2:.0f} · {f_cd_mpa:.2f}) ≈ {omega:.3f}<br>"
        calculo_m2 += f"K_r = (1 + {omega:.3f} - {n:.3f}) / (1 + {omega:.3f} - {n_bal:.1f}) ≈ {K_r:.3f}<br>"
        calculo_m2 += f"β = 0.35 + {f_ck:.0f}/200 - {esbelteza:.2f}/150 ≈ {beta_creep:.3f}<br>"
        calculo_m2 += f"K_φ = 1 + {beta_creep:.3f} · {phi_ef:.1f} ≈ {K_phi:.3f}<br>"
        calculo_m2 += f"1/r = {K_r:.3f} x {K_phi:.3f} x {inv_r0:.8f} = {inv_r:.8f} mm⁻¹<br>"
        calculo_m2 += f"<b>b) Momento de 2ª Ordem (M₂)</b><br>"
        calculo_m2 += f"e₂ = {inv_r:.8f} x ({l0_m*1000:.0f})² / 10 = {e2_mm:.1f} mm<br>"
        calculo_m2 += f"M₂ = {N_Ed_kN:.1f} kN x {e2_mm / 1000:.3f} m = {M2_Ed_Nm/1000:.2f} kNm"
        passos.append({"titulo": "4. Efeitos de 2ª Ordem (M₂)", "formula": formula_m2, "calculo": calculo_m2})
    else:
        passos.append({"titulo": "3.2. Conclusão", "calculo": "Pilar não esbelto."})
    
    momento_2a_ordem = M_Ed_total_Nm - M0_Ed_Nm
    calculo_m_final = f"M_Ed,total = {M0_Ed_kNm:.2f} + {momento_2a_ordem/1000:.2f} = {M_Ed_total_Nm/1000:.2f} kNm"
    passos.append({"titulo": "5. Esforços Finais de Dimensionamento", "formula": r"M_{Ed,total} = M_{0Ed} + M_{2}", "calculo": calculo_m_final})
    
    As_req_mm2_final = _dimensionar_pilar_rigoroso(b_mm, h_mm, f_cd_mpa, f_yd_mpa, N_Ed_N, M_Ed_total_Nm, c_nom_mm, passos)

    As_min_cm2_1 = 0.10 * N_Ed_N / f_yd_mpa / 100
    As_min_cm2_2 = 0.002 * Ac_mm2 / 100
    As_min_cm2 = max(As_min_cm2_1, As_min_cm2_2)
    As_final_req_cm2 = max(As_req_mm2_final/100, As_min_cm2)
    calculo_as_min = f"As,min₁ = 0.10 x {N_Ed_N:.0f} / {f_yd_mpa:.2f} / 100 = {As_min_cm2_1:.2f} cm²<br>As,min₂ = 0.002 x {Ac_mm2:.0f} / 100 = {As_min_cm2_2:.2f} cm²<br>As,min = max({As_min_cm2_1:.2f}, {As_min_cm2_2:.2f}) = {As_min_cm2:.2f} cm²<br>Adotar As,req = max({As_req_mm2_final/100:.2f}, {As_min_cm2:.2f}) = {As_final_req_cm2:.2f} cm²"
    passos.append({"titulo": "7. Verificação de Mínimos", "formula": r"A_{s,min} = max(0.10\frac{N_{Ed}}{f_{yd}} ; 0.002 A_c)", "calculo": calculo_as_min})

    n_barras, phi_long, As_prov_cm2 = encontrar_combinacao_barras_pilar(As_final_req_cm2, b_mm, h_mm, c_nom_mm, 8.0)
    if n_barras == 0: raise ValueError("Não foi encontrada uma combinação de armadura válida.")

    calculo_final = (
        f"O programa procura a combinação de varões mais económica que satisfaz a área de aço necessária ({As_final_req_cm2:.2f} cm²)<br>"
        f"e as regras construtivas (mínimo 4 varões, número par).<br>"
        f"A solução ótima encontrada foi <b>{n_barras} Ø {phi_long}</b>, que fornece uma área de <b>{As_prov_cm2:.2f} cm²</b>."
    )
    passos.append({ "titulo": "8. Escolha da Armadura Final", "calculo": calculo_final })
    
    dados_desenho = {"b": b_mm, "h": h_mm, "c_nom": c_nom_mm, "phi_estribo": 8.0, "n_barras": n_barras, "phi_long": phi_long}
    resultado = {'status': 'Sucesso', 'mensagem': 'Cálculo efetuado com sucesso.', 'combinacao_final': f"{n_barras} Ø {phi_long}", 'As_final_cm2': f"{As_prov_cm2:.2f}", 'passos': passos, 'dados_desenho': dados_desenho}
    return resultado