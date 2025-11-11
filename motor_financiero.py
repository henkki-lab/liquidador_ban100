from math import pow
from modelos import ParametrosPensionado, ResultadoPensionado, CuotaDetalle, TASAS_MAX_PENSIONADOS, SEGUROS_EDAD


# === Utilidades ===

def obtener_tasa_por_indice(indice: int) -> dict:
    """Devuelve la tasa mensual (TM) y efectiva anual (TEA) según el índice elegido."""
    return TASAS_MAX_PENSIONADOS.get(indice, TASAS_MAX_PENSIONADOS[6])  # por defecto 1.46%


def obtener_seguro_por_edad(edad: int) -> float:
    """Devuelve el valor del seguro por millón según el rango de edad."""
    for rango in SEGUROS_EDAD:
        if rango["edad_min"] <= edad <= rango["edad_max"]:
            return rango["valor"]
    # valor máximo si la edad excede el rango
    return SEGUROS_EDAD[-1]["valor"]


def calcular_fv(tasa_ea: float, dias_gracia: int, monto: float) -> float:
    """Simula la fórmula FV de Excel para calcular los intereses iniciales."""
    # tasa diaria equivalente con 15 decimales
    tasa_dia = pow(1 + tasa_ea, 1 / 360) - 1
    fv = monto * pow(1 + tasa_dia, dias_gracia)
    intereses_iniciales = fv - monto
    return intereses_iniciales


def calcular_pmt(tasa_mensual: float, plazo: int, monto: float) -> float:
    """Simula la fórmula PMT de Excel, devuelve el valor de la cuota financiera."""
    if tasa_mensual == 0:
        return monto / plazo
    pmt = monto * (tasa_mensual * pow(1 + tasa_mensual, plazo)) / (pow(1 + tasa_mensual, plazo) - 1)
    return pmt


# === Función principal ===

def liquidar_pensionado(p: ParametrosPensionado) -> ResultadoPensionado:
    """Calcula la cuota del pensionado con la misma lógica del Excel Ban100."""

    # 1. Obtener tasas y seguro
    tasas = obtener_tasa_por_indice(p.indice_tasa)
    tasa_mv = tasas["tm"]  # tasa mensual (decimal)
    tasa_ea = tasas["tea"]  # tasa efectiva anual (decimal)
    seguro_mm = obtener_seguro_por_edad(p.edad)

    # 2. Calcular intereses iniciales (por días de gracia)
    intereses_iniciales = calcular_fv(tasa_ea, p.dias_gracia, p.monto_solicitado)

    # 3. Calcular seguro primer mes
    seguro_primer_mes = (p.monto_solicitado / 1_000_000) * seguro_mm

    # 4. Calcular monto a capitalizar
    monto_capitalizar = intereses_iniciales + seguro_primer_mes

    # 5. Calcular monto total financiado
    monto_mas_capitalizacion = p.monto_solicitado + monto_capitalizar

    # 6. Calcular cuota financiera
    cuota_financiera = calcular_pmt(tasa_mv, p.plazo_meses, monto_mas_capitalizacion)

    # 7. Calcular cuota neta (cuota financiera + seguro mensual)
    seguro_mensual = seguro_mm
    cuota_neta = cuota_financiera + seguro_mensual

    # 8. Crear resultado
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
