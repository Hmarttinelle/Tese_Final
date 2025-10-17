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
}

def _verificar_espacamento(combinacao, largura_disponivel):
    """Verifica se uma dada combinação de diâmetros de varão respeita o espaçamento mínimo."""
    num_barras = len(combinacao)
    if num_barras <= 1:
        return True
    espacamento_minimo_horizontal = max(max(combinacao), 20)
    largura_necessaria = sum(combinacao) + (num_barras - 1) * espacamento_minimo_horizontal
    return largura_necessaria <= largura_disponivel

def encontrar_combinacoes_otimas(As_req_cm2, largura_disponivel_mm):
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

    if melhor_unica:
        melhor_unica["As_final_cm2"] = round(melhor_unica["area_total_cm2"], 2)
    if melhor_mista:
        melhor_mista["As_final_cm2"] = round(melhor_mista["area_total_cm2"], 2)

    return {
        "unica": melhor_unica,
        "mista": melhor_mista
    }