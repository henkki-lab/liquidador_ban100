from math import pow
from modelos import (
    ParametrosPensionado,
    ResultadoPensionado,
    CuotaDetalle,
    TASAS_MAX_PENSIONADOS,
    SEGUROS_EDAD,
)

# ---------------------------
# Utilidades idénticas a Excel
# ---------------------------

def obtener_tm_por_indice(indice: int) -> float:
    """Devuelve la tasa mensual (TM) en decimal según índice B65."""
    return round(TASAS_MAX_PENSIONADOS.get(indice, TASAS_MAX_PENSIONADOS[6])["tm"], 15)  # default 1.46% con 15 decimales


def calcular_tea_excel_desde_tm(tm: float) -> float:
    """
    La hoja hace: C19 = ROUND(((1+TM)^12)-1, 6)
    IMPORTANTE: hay redondeo a 6 decimales ANTES de usar la TEA en FV.
    """
    tea = pow(1.0 + tm, 12.0) - 1.0
    return round(tea, 6)  # EXACTO a Excel


def obtener_seguro_por_edad_con_extraprima(edad: int, extraprima: float) -> float:
    """
    B27 = Seguro por millón según edad * (1 + extraprima)
    """
    base = SEGUROS_EDAD[0]["valor"]  # fallback
    for rango in SEGUROS_EDAD:
        if rango["edad_min"] <= edad <= rango["edad_max"]:
            base = rango["valor"]
            break
    return round(base * (1.0 + (extraprima or 0.0)), 15)


def calcular_fv_excel(tea: float, dias: int, monto: float) -> float:
    """
    B22 = FV(TEA; días/360; 0; -monto) - monto
    Excel toma la TEA (ya con ROUND a 6), calcula tasa diaria (comp 360)
    y hace FV con n = días (puede ser fraccionario si aplica).
    """
    tasa_dia = pow(1.0 + tea, 1.0 / 360.0) - 1.0
    fv = monto * pow(1.0 + tasa_dia, dias)
    return round(fv - monto, 15)


def calcular_pmt_excel(tm: float, n: int, pv: float) -> float:
    """
    B26 = ROUND( PMT(TM; plazo; -MontoFinanciado); 0 )
    """
    if tm == 0:
        cuota = pv / n
    else:
        cuota = pv * (tm * pow(1.0 + tm, n)) / (pow(1.0 + tm, n) - 1.0)
    return round(cuota, 0)  # redondeo a pesos como la hoja


def calcular_monto_desde_cuota(tm: float, n: int, cuota: float) -> float:
    """
    Fórmula inversa de PMT: calcula el monto financiado (PV) a partir de la cuota.
    = PMT * ((1+TM)^n - 1) / (TM * (1+TM)^n)
    """
    if tm == 0:
        return round(cuota * n, 15)
    else:
        pv = cuota * ((pow(1 + tm, n) - 1.0) / (tm * pow(1 + tm, n)))
        return round(pv, 15)


# ---------------------------
# Motor principal idéntico a la hoja
# ---------------------------

def liquidar_pensionado(p: ParametrosPensionado) -> ResultadoPensionado:
    # 1) Tasas y seguro
    tm = obtener_tm_por_indice(p.indice_tasa)  # B19 (TM)
    tea = calcular_tea_excel_desde_tm(tm)      # C19 (ROUND a 6)
    seguro_mm = obtener_seguro_por_edad_con_extraprima(p.edad, getattr(p, "extraprima_seguro", 0.0))  # B27

    # 2) Intereses iniciales (B22)
    intereses_iniciales = calcular_fv_excel(tea, p.dias_gracia, p.monto_solicitado)

    # 3) Seguro primer mes (B23)
    seguro_primer_mes = (p.monto_solicitado / 1_000_000.0) * seguro_mm

    # 4) Monto a capitalizar (B24)
    monto_capitalizar = intereses_iniciales + seguro_primer_mes

    # 5) Monto + Capitalización (B25)
    monto_financiado = p.monto_solicitado + monto_capitalizar

    # 6) Cuota financiera (B26)
    cuota_financiera = calcular_pmt_excel(tm, p.plazo_meses, monto_financiado)

    # 7) Cuota neta (B28)
    cuota_neta = float(cuota_financiera) + seguro_primer_mes

    return ResultadoPensionado(
        cuota_financiera=float(cuota_financiera),
        cuota_neta=round(cuota_neta, 15),
        disponible_cuota=0.0,
        diferencia_disponible_vs_cuota=0.0,
        seguro_por_millon=round(seguro_mm, 15),
        monto_capitalizado=round(monto_capitalizar, 15),
        monto_financiado=round(monto_financiado, 15),
        tasa_mv=round(tm, 15),
        tasa_ea=round(tea, 15),
        plan_pagos=[],
    )
