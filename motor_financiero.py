from math import pow
from modelos import (
    ParametrosPensionado,
    ResultadoPensionado,
    CuotaDetalle,
    TASAS_MAX_PENSIONADOS,
    SEGUROS_EDAD,
)

# ---------------------------
# Utilidades idénticas a Excel (versión calibrada)
# ---------------------------

def obtener_tm_por_indice(indice: int) -> float:
    """Devuelve la tasa mensual (TM) en decimal según índice B65."""
    return TASAS_MAX_PENSIONADOS.get(indice, TASAS_MAX_PENSIONADOS[6])["tm"]

def calcular_tea_excel_desde_tm(tm: float) -> float:
    """
    Excel: ROUND(((1+TM)^12)-1, 6)
    La TEA se redondea a 6 decimales antes de usarla.
    """
    tea = pow(1.0 + tm, 12.0) - 1.0
    return round(tea, 6)

def obtener_seguro_por_edad_con_extraprima(edad: int, extraprima: float = 0.0) -> float:
    """
    B27 = Seguro por millón según edad * (1 + extraprima)
    """
    base = SEGUROS_EDAD[0]["valor"]
    for rango in SEGUROS_EDAD:
        if rango["edad_min"] <= edad <= rango["edad_max"]:
            base = rango["valor"]
            break
    return base * (1.0 + (extraprima or 0.0))

def calcular_fv_excel(tea: float, dias: int, monto: float) -> float:
    """
    Excel: =FV(TEA; días/360; 0; -monto) - monto
    Con TEA redondeada a 6 decimales y conversión diaria exacta (360 días).
    """
    tasa_dia = pow(1.0 + tea, 1.0 / 360.0) - 1.0
    tasa_dia = round(tasa_dia, 15)  # Excel guarda hasta 15 decimales
    fv = monto * pow(1.0 + tasa_dia, dias)
    return fv - monto

def calcular_pmt_excel(tm: float, n: int, pv: float) -> float:
    """
    Excel: =ROUND(PMT(TM; plazo; -PV); 0)
    """
    if tm == 0:
        cuota = pv / n
    else:
        cuota = pv * (tm * pow(1.0 + tm, n)) / (pow(1.0 + tm, n) - 1.0)
    return round(cuota, 0)

def calcular_monto_desde_cuota(tm: float, n: int, cuota: float) -> float:
    """
    Inversión de PMT: devuelve PV (monto financiado) a partir de la cuota.
    Excel: PV = cuota * ((1 - (1 + TM)^-n) / TM)
    """
    if tm == 0:
        return cuota * n
    factor = (1 - pow(1.0 + tm, -n)) / tm
    return round(cuota * factor, 0)

# ---------------------------
# Motor principal
# ---------------------------

def liquidar_pensionado(p: ParametrosPensionado) -> ResultadoPensionado:
    tm = obtener_tm_por_indice(p.indice_tasa)
    tea = calcular_tea_excel_desde_tm(tm)
    seguro_mm = obtener_seguro_por_edad_con_extraprima(p.edad, getattr(p, "extraprima_seguro", 0.0))

    intereses_iniciales = calcular_fv_excel(tea, p.dias_gracia, p.monto_solicitado)
    seguro_primer_mes = (p.monto_solicitado / 1_000_000.0) * seguro_mm
    monto_capitalizar = intereses_iniciales + seguro_primer_mes
    monto_financiado = p.monto_solicitado + monto_capitalizar

    cuota_financiera = calcular_pmt_excel(tm, p.plazo_meses, monto_financiado)
    cuota_neta = float(cuota_financiera) + seguro_primer_mes

    return ResultadoPensionado(
        cuota_financiera=float(cuota_financiera),
        cuota_neta=cuota_neta,
        disponible_cuota=0.0,
        diferencia_disponible_vs_cuota=0.0,
        seguro_por_millon=seguro_mm,
        monto_capitalizado=monto_capitalizar,
        monto_financiado=monto_financiado,
        tasa_mv=tm,
        tasa_ea=tea,
        plan_pagos=[],
    )
