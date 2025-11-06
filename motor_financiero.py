from math import pow
from typing import List
from modelos import ParametrosPensionado, ResultadoPensionado, CuotaDetalle
from tablas_excel import tasa_desde_indice, tasa_ea_desde_mv, seguro_por_millon

def pmt(rate: float, nper: int, pv: float) -> float:
    if rate == 0:
        return -pv / nper
    return -(rate * pv) / (1 - pow(1 + rate, -nper))

def liquidar_pensionado(p: ParametrosPensionado) -> ResultadoPensionado:
    H10 = tasa_desde_indice(p.indice_tasa)
    I10 = tasa_ea_desde_mv(H10)

    H13 = p.monto_solicitado * ((1 + I10) ** (p.dias_gracia / 360) - 1)
    H18 = seguro_por_millon(p.edad, p.extraprima_seguro)
    H14 = (p.monto_solicitado / 1_000_000) * H18
    H15 = H13 + H14
    H16 = H15 + p.monto_solicitado
    H17 = round(pmt(H10, p.plazo_meses, -H16), 0)
    H19 = H17 + (H18 * (p.monto_solicitado / 1_000_000))

    # Disponible cuota simplificado (luego se agregará la fórmula completa)
    B16 = (p.ingresos_totales / 2) - p.deducciones_totales + p.cuota_compra_cartera - 10000
    I19 = H19 - B16

    plan = []
    saldo = H16
    seguro_mes = p.monto_solicitado * (H18 / 1_000_000)

    for k in range(1, p.plazo_meses + 1):
        interes = saldo * H10
        abono = H17 - interes
        cuota_total = H17 + seguro_mes
        saldo -= abono
        plan.append(CuotaDetalle(k, round(abono, 2), round(interes, 2), round(seguro_mes, 2),
                                 round(cuota_total, 2), round(saldo, 2)))

    return ResultadoPensionado(
        cuota_financiera=H17,
        cuota_neta=H19,
        disponible_cuota=B16,
        diferencia_disponible_vs_cuota=I19,
        seguro_por_millon=H18,
        monto_capitalizado=H15,
        monto_financiado=H16,
        tasa_mv=H10,
        tasa_ea=I10,
        plan_pagos=plan
    )
