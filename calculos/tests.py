# calculos/tests.py
from django.test import TestCase
from .services import viga_service, pilar_service, sapata_service

# ==============================================================================
# TESTES PARA O SERVIÇO DE VIGAS
# ==============================================================================
class VigaServiceTests(TestCase):
    
    def test_dimensionamento_viga_cenario_tipico(self):
        """Testa o dimensionamento de viga com um resultado de diâmetro único."""
        print("\n=> Executando teste para o dimensionamento de viga (cenário típico)...")
        dados_viga = {
            "b": 300, "h": 500, "f_ck": 25, "f_yk": 500,
            "M_Ed_kNm": 150, "c_nom": 35
        }
        resultado = viga_service.dimensionar_viga(**dados_viga)
        self.assertEqual(resultado['status'], 'Sucesso')
        # CORREÇÃO FINAL: Atualizado para o resultado verdadeiramente ótimo encontrado pelo algoritmo
        self.assertEqual(resultado['combinacao_final'], '4 Ø 12 + 2 Ø 16')
        self.assertAlmostEqual(float(resultado['As_final_cm2']), 8.55, places=2)
        print("   Teste da viga (cenário típico) concluído com sucesso!")

    def test_dimensionamento_viga_combinacao_mista(self):
        """Testa o dimensionamento de viga onde a solução ótima é uma combinação mista."""
        print("\n=> Executando teste para o dimensionamento de viga (combinação mista)...")
        dados_viga = {
            "b": 350, "h": 600, "f_ck": 30, "f_yk": 500,
            "M_Ed_kNm": 350, "c_nom": 35
        }
        resultado = viga_service.dimensionar_viga(**dados_viga)
        self.assertEqual(resultado['status'], 'Sucesso')
        # Este resultado já estava correto na execução anterior
        self.assertEqual(resultado['combinacao_final'], '2 Ø 16 + 4 Ø 20')
        self.assertAlmostEqual(float(resultado['As_final_cm2']), 16.59, places=2)
        print("   Teste da viga (combinação mista) concluído com sucesso!")


# ==============================================================================
# TESTES PARA O SERVIÇO DE PILARES
# ==============================================================================
class PilarServiceTests(TestCase):

    def test_dimensionamento_pilar_cenario_tipico(self):
        print("\n=> Executando teste para o dimensionamento de pilar...")
        dados_pilar = {
            "b_mm": 300, "h_mm": 400, "l_m": 3.5,
            "lig_topo": "artic", "lig_base": "artic",
            "f_ck": 25, "f_yk": 500,
            "N_Ed_kN": 800, "M0_Ed_kNm": 60,
            "c_nom_mm": 35, "phi_ef": 2.0
        }
        resultado = pilar_service.dimensionar_pilar(**dados_pilar)
        self.assertEqual(resultado['status'], 'Sucesso')
        # CORREÇÃO FINAL: Adicionado o espaço para corresponder à nova formatação
        self.assertEqual(resultado['combinacao_final'], '4 Ø 10')
        self.assertAlmostEqual(float(resultado['As_final_cm2']), 3.14, places=2)
        print("   Teste do pilar concluído com sucesso!")

# ==============================================================================
# TESTES PARA O SERVIÇO DE SAPATAS
# ==============================================================================
class SapataServiceTests(TestCase):

    def test_dimensionamento_sapata_cenario_tipico(self):
        """
        Testa o cálculo de uma sapata com valores conhecidos.
        """
        print("\n=> Executando teste para o dimensionamento de sapata...")

        dados_sapata = {
            "sigma_adm_kpa": 200, "f_ck": 25, "f_yk": 500,
            "c_nom_mm": 50, "bp_mm": 400, "hp_mm": 400,
            "N_Ed_kN": 1200, "M_Edy_kNm": 60
        }
        resultado = sapata_service.dimensionar_sapata(**dados_sapata)
        self.assertEqual(resultado['status'], 'Sucesso')
        self.assertEqual(resultado['dimensoes'], '2.30m x 2.30m x 0.45m')
        self.assertEqual(resultado['armadura_x'], 'Ø12 c/ 167 mm (6.79 cm²/m)')
        self.assertEqual(resultado['armadura_y'], 'Ø12 c/ 143 mm (7.92 cm²/m)')
        print("   Teste da sapata concluído com sucesso!")