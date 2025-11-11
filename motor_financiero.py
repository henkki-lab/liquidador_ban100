from math import pow
from modelos import (
    ParametrosPensionado,
    ResultadoPensionado,
    CuotaDetalle,
    TASAS_MAX_PENSIONADOS,
    SEGUROS_EDAD
)


# === Funciones auxiliares ===

def obtener_tasa_por_indice(indice: int) -> dict:
    """
    Devuelve la tasa mensual (TM) y efectiva anual (TEA) según el índice de tasa.
    Si no se encuentra el índice, usa la tasa más baja (1.46% mensual).
    """
    return TASAS_MAX_PENSIONADOS.get(indice, TASAS_MAX_PENSIONADOS[6])


def obtener_seguro_por_edad(edad: int) -> float:
    """
    Devuelve el valor del seguro por millón según el rango de edad.
    """
    for rango in SEGUROS_EDAD:
        if rango["edad_min"] <= edad <= rango["edad_max"]:
            return rango["valor"]
    return SEGUROS_EDAD[-1]["valor"]  # valor más alto si excede el rango


def calcular_fv(tasa_ea: float, dias_gracia: int, monto: float) -> float:
    """
    Calcula los intereses iniciales (como FV en Excel).
    Usa precisión de 15 decimales sin redondeos prematuros.
    """
    tasa_dia = pow(1 + tasa_ea, 1 / 360) - 1
    fv = monto * pow(1 + tasa_dia, dias_gracia)
    intereses = fv - monto
    return intereses


def calcular_pmt(tasa_mensual: float, plazo_meses: int, monto: float) -> float:
    """
    Calcula la cuota financiera (PMT de Excel).
    Usa la fórmula: PMT = monto * (r*(1+r)^n) / ((1+r)^n - 1)
    """
    if tasa_mensual == 0:
        return monto / plazo_meses
    pmt = monto * (tasa_mensual * pow(1 + tasa_mensual, plazo_meses)) / (pow(1 + tasa_mensual, plazo_meses) - 1)
    return pmt


# === Motor principal ===

def liquidar_pensionado(p: ParametrosPensionado) -> ResultadoPensionado:
    """
    Replica los cálculos del Excel Ban100 con precisión de 15 decimales.
    """

    # 1️⃣ Obtener tasas y seguros
    tasas = obtener_tasa_por_indice(p.indice_tasa)
    tasa_mv = tasas["tm"]
    tasa_ea = tasas["tea"]
    seguro_mm = obtener_seguro_por_edad(p.edad)

    # 2️⃣ Intereses iniciales
    intereses_iniciales = calcular_fv(tasa_ea, p.dias_gracia, p.monto_solicitado)

    # 3️⃣ Seguro primer mes
    seguro_primer_mes = (p.monto_solicitado / 1_000_000) * seguro_mm

    # 4️⃣ Monto a capitalizar
    monto_capitalizar = intereses_iniciales + seguro_primer_mes

    # 5️⃣ Monto total financiado
    monto_mas_capitalizacion = p.monto_solicitado + monto_capitalizar

    # 6️⃣ Cuota financiera (PMT)
    cuota_financiera = calcular_pmt(tasa_mv, p.plazo_meses, monto_mas_capitalizacion)

    # 7️⃣ Cuota neta
    cuota_neta = cuota_financiera + seguro_mm

    # 8️⃣ Resultado estructurado
    resultado = ResultadoPensionado(
        cuota_financiera=round(cuota_financiera, 3),
        cuota_neta=round(cuota_neta, 3),
        disponible_cuota=0.0,
        diferencia_disponible_vs_cuota=0.0,
        seguro_por_millon=seguro_mm,
        monto_capitalizado=round(monto_capitalizar, 3),
        monto_financiado=round(monto_mas_capitalizacion, 3),
        tasa_mv=tasa_mv,
        tasa_ea=tasa_ea,
        plan_pagos=[]
    )

    return resultado
