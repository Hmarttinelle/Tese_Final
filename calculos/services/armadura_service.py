# calculos/services/armadura_service.py
import math
from itertools import combinations_with_replacement

# Diâmetros de varão padrão [mm] e respetivas áreas [cm²]
VERGALHOES_PADRAO = {
    10: 0.785,
    12: 1.131,
    16: 2.011,
    20: 3.142,
    25: 4.909,
    32: 8.042,
    40: 12.566,
    50: 19.635,
    55: 23.758,
    60: 28.274,

}

def _verificar_espacamento(combinacao, largura_disponivel):
    """Verifica se uma dada combinação de diâmetros de varão respeita o espaçamento mínimo."""
    num_barras = len(combinacao)
    if num_barras <= 1:
        return True
    espacamento_minimo_horizontal = max(max(combinacao), 20)
    largura_necessaria = sum(combinacao) + (num_barras - 1) * espacamento_minimo_horizontal
    return largura_necessaria <= largura_disponivel

def encontrar_combinacoes_otimas(As_req_cm2, largura_disponivel_mm, tipo_elemento="viga"):
    """
    Encontra a melhor combinação de diâmetro único e a melhor combinação mista que
    satisfazem a área de aço e os espaçamentos.
    """
    solucoes_unicas = []
    solucoes_mistas = []
    diametros = sorted(list(VERGALHOES_PADRAO.keys()))

    max_barras = 8 
    todas_as_combinacoes = []

    for num_barras in range(2, max_barras + 1):
        # 1. Combinações de diâmetro único (ex: [12, 12, 12])
        for diametro in diametros:
            todas_as_combinacoes.append(tuple([diametro] * num_barras))
        
        # 2. Combinações de diâmetros mistos (simétricas)
        if num_barras >= 4 and num_barras % 2 == 0:
            pares_de_diametros = list(combinations_with_replacement(diametros, 2))
            for d1, d2 in pares_de_diametros:
                if d1 == d2: continue
                # Gera splits simétricos (ex: para 6 barras, testa 2+4; para 8, testa 2+6 e 4+4)
                for i in range(1, num_barras // 2):
                    if (num_barras - 2*i) == i * 2: # Evita duplicar o split 50/50
                        break
                    comb = tuple(sorted([d1]*(i*2) + [d2]*(num_barras - i*2)))
                    todas_as_combinacoes.append(comb)


    # Remove duplicados
    todas_as_combinacoes = sorted(list(set(todas_as_combinacoes)), key=lambda x: (len(x), sum(x)))

    # 3. Verifica cada combinação e guarda as válidas
    for comb in todas_as_combinacoes:
        if _verificar_espacamento(comb, largura_disponivel_mm):
            area_total_cm2 = sum(VERGALHOES_PADRAO[d] for d in comb)
            if area_total_cm2 >= As_req_cm2:
                counts = {d: comb.count(d) for d in set(comb)}
                # CORREÇÃO DE FORMATAÇÃO: Adicionado espaço antes do Ø
                combinacao_str = " + ".join([f"{count} Ø {diam}" for diam, count in sorted(counts.items())])
                
                if len(counts) > 1:
                    solucoes_mistas.append({"combinacao_str": combinacao_str, "area_total_cm2": area_total_cm2})
                else:
                    solucoes_unicas.append({"combinacao_str": combinacao_str, "area_total_cm2": area_total_cm2})

    # 4. Encontra a melhor solução de cada categoria
    melhor_unica = min(solucoes_unicas, key=lambda x: x["area_total_cm2"]) if solucoes_unicas else None
    melhor_mista = min(solucoes_mistas, key=lambda x: x["area_total_cm2"]) if solucoes_mistas else None

    # NOVO PASSO: Prioridade a soluções de diâmetro único em vigas quando As_prov <= 1.10 As_req
    if tipo_elemento == "viga":
        solucoes_diametro_unico_boas = [s for s in solucoes_unicas if s["area_total_cm2"] <= 1.10 * As_req_cm2]
        
        if solucoes_diametro_unico_boas:
            # Restringe o conjunto a apenas essas soluções de diâmetro único e escolhe a de menor As_prov
            melhor_unica = min(solucoes_diametro_unico_boas, key=lambda x: x["area_total_cm2"])
            
            # Se a opção mista for globalmente mais económica, anulamo-la para forçar 
            # a escolha da opção de diâmetro único (que já cumpre a tolerância de 10%).
            if melhor_mista and melhor_mista["area_total_cm2"] < melhor_unica["area_total_cm2"]:
                melhor_mista = None

    if melhor_unica:
        melhor_unica["As_final_cm2"] = round(melhor_unica["area_total_cm2"], 2)
    if melhor_mista:
        melhor_mista["As_final_cm2"] = round(melhor_mista["area_total_cm2"], 2)

    return {
        "unica": melhor_unica,
        "mista": melhor_mista
    }

# ==============================================================================
# NOVA FUNÇÃO, ESPECÍFICA PARA PILARES
# ==============================================================================

def encontrar_combinacoes_otimas_pilar(As_req_cm2, largura_disponivel_mm, b_mm=None, h_mm=None):
    """
    Encontra a melhor combinação de armadura para PILARES, garantindo um número
    par de varões para manter a simetria (mínimo de 4 varões).
    Se a secção for quadrada (b ~= h), dá preferência a soluções de diâmetro único ou perfeitamente simétricas.
    """
    solucoes_unicas = []
    solucoes_mistas = []
    diametros = sorted(list(VERGALHOES_PADRAO.keys()))

    max_barras = 8 
    
    # A ALTERAÇÃO PRINCIPAL ESTÁ AQUI: O loop agora só itera sobre números pares (4, 6, 8)
    for num_barras in range(4, max_barras + 1, 2):
        
        # 1. Combinações de diâmetro único (ex: 4Ø12, 6Ø12, etc.)
        for diametro in diametros:
            comb = tuple([diametro] * num_barras)
            if _verificar_espacamento(comb, largura_disponivel_mm):
                area_total_cm2 = sum(VERGALHOES_PADRAO[d] for d in comb)
                if area_total_cm2 >= As_req_cm2:
                    combinacao_str = f"{num_barras} Ø {diametro}"
                    solucoes_unicas.append({"combinacao_str": combinacao_str, "area_total_cm2": area_total_cm2})

        # 2. Combinações de diâmetros mistos (simétricas)
        # Ex: 2ØD1 + 2ØD2 (para 4 varões), 2ØD1 + 4ØD2 (para 6 varões), etc.
        import itertools
        pares_de_diametros = list(itertools.permutations(diametros, 2))
        for d1, d2 in pares_de_diametros:
            # Gera splits simétricos. Ex: para 6 barras -> 2+4; para 8 barras -> 2+6 e 4+4
            for i in range(1, num_barras // 2 + 1):
                n1 = i * 2
                n2 = num_barras - n1
                if n2 == 0: continue
                if n1 > n2: continue # Evita duplicados como 6+2 depois de 2+6
                
                comb = tuple(sorted([d1]*n1 + [d2]*n2))
                if _verificar_espacamento(comb, largura_disponivel_mm):
                    area_total_cm2 = sum(VERGALHOES_PADRAO[d] for d in comb)
                    if area_total_cm2 >= As_req_cm2:
                        counts = {d: comb.count(d) for d in set(comb)}
                        combinacao_str = " + ".join([f"{count} Ø {diam}" for diam, count in sorted(counts.items())])
                        solucoes_mistas.append({"combinacao_str": combinacao_str, "area_total_cm2": area_total_cm2, "counts": counts})

    # -------------------------------------------------------------------------
    # Regras Construtivas de Pilares: Simetria em 4 varões e Cantos iguais
    # -------------------------------------------------------------------------
    mistas_filtradas = []
    for m in solucoes_mistas:
        counts = m.get("counts", {})
        total_barras = sum(counts.values())
        
        # Regra de simetria para 4 varões:
        # Se n_barras_total == 4, rejeita misturas (só permite 4 varões do mesmo diâmetro)
        if total_barras == 4:
            continue
            
        # 4 cantos com mesmo diâmetro quando há mais varões:
        # Quando há >4 varões, pelo menos um dos diâmetros deve ter 4 ou mais varões para ocupar os 4 cantos.
        if total_barras > 4:
            if not any(c >= 4 for c in counts.values()):
                continue
                
        mistas_filtradas.append(m)
        
    solucoes_mistas = mistas_filtradas

    # Regra específica para secções quadradas:
    # Se abs(b - h) <= 5 mm, dá preferência a soluções de diâmetro único.
    # As mistas só são aceites se forem simétricas em todas as direções (quantidades múltiplas de 4).
    is_quadrado = False
    if b_mm is not None and h_mm is not None:
        if abs(b_mm - h_mm) <= 5:
            is_quadrado = True

    if is_quadrado:
        if solucoes_unicas:
            # Se houver opções de diâmetro único viáveis, descartar as opções mistas
            solucoes_mistas = []
        else:
            # Se não houver, filtrar as mistas para garantir simetria total (múltiplos de 4 em cada diâmetro)
            mistas_simetricas = []
            for m in solucoes_mistas:
                if all(c % 4 == 0 for c in m["counts"].values()):
                    mistas_simetricas.append(m)
            solucoes_mistas = mistas_simetricas

    # Encontra a melhor solução de cada categoria
    melhor_unica = min(solucoes_unicas, key=lambda x: x["area_total_cm2"]) if solucoes_unicas else None
    melhor_mista = min(solucoes_mistas, key=lambda x: x["area_total_cm2"]) if solucoes_mistas else None

    if melhor_unica:
        melhor_unica["As_final_cm2"] = round(melhor_unica["area_total_cm2"], 2)
    if melhor_mista:
        melhor_mista["As_final_cm2"] = round(melhor_mista["area_total_cm2"], 2)

    return {
        "unica": melhor_unica,
        "mista": melhor_mista
    }