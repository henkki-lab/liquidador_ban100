import unittest
from modelos import ParametrosPensionado
from motor_financiero import liquidar_pensionado

class TestMotorFinanciero(unittest.TestCase):
    def test_cuota_neta_basica(self):
        p = ParametrosPensionado(
            edad=75,
            plazo_meses=156,
            monto_solicitado=15000000,
            ingresos_totales=7000000,
            salud=400000,
            pension_aporte=0,
            retencion_fuente=0,
            fondo_solidaridad=0,
            deducciones_totales=2000000,
            cuota_compra_cartera=100000,
            smmlv=1423500,
            codigo_pagaduria=1,
            indice_tasa=6
        )
        resultado = liquidar_pensionado(p)
        self.assertGreater(resultado.cuota_neta, 0)
        self.assertLess(resultado.cuota_neta, 5000000)

if __name__ == "__main__":
    unittest.main()
