from decimal import Decimal, getcontext, ROUND_HALF_UP
from modelos import (
    ParametrosPensionado,
    ResultadoPensionado,
    CuotaDetalle,
    TASAS_MAX_PENSIONADOS,
    SEGUROS_EDAD,
)

# ==============================
# Configuración Decimal y helpers
# ==============================
getcontext().prec = 34  # precisión interna amplia; controlamos con quantize

Q0   = Decimal("1")                       # 0 decimales
Q6   = Decimal("0.000001")               # 6 decimales
Q15  = Decimal("0.000000000000001")      # 15 decimales

def D(x) -> Decimal:
    """Conversión segura a Decimal (evita binarios)."""
    if isinstance(x, Decimal):
        return x
    if isinstance(x, (float, int)):
        return Decimal(str(x))
    return Decimal(x)

def round_excel(x: Decimal, places: int) -> Decimal:
    """ROUND de Excel (mitad hacia arriba)."""
    if places == 0:
        return x.quantize(Q0, rounding=ROUND_HALF_UP)
    q = Decimal("1").scaleb(-places)  # 10^-places
    return x.quantize(q, rounding=ROUND_HALF_UP)

# ==============================
# Tablas y parámetros
# ==============================
def _tm_por_indice(indice: int) -> Decimal:
    fila = TASAS_MAX_PENSIONADOS.get(indice, TASAS_MAX_PENSIONADOS[6])  # por defecto 1.46%
    return D(fila["tm"])

def _tea_por_tm_excel(tm: Decimal) -> Decimal:
    """
    Excel: =ROUND((1+TM)^12 - 1, 6)
    Se usa esta TEA redondeada para todo lo que sigue.
    """
    tea = (Decimal("1") + tm) ** Decimal("12") - Decimal("1")
    return round_excel(tea, 6)

def _seguro_por_edad(edad: int, extraprima: Decimal = Decimal("0")) -> Decimal:
    base = D(SEGUROS_EDAD[0]["valor"])
    for r in SEGUROS_EDAD:
        if r["edad_min"] <= edad <= r["edad_max"]:
            base = D(r["valor"])
            break
    return base * (Decimal("1") + extraprima)

# ==============================
# Construcción de tasas y factores
# ==============================
def _tasa_dia_desde_tea(tea6: Decimal) -> Decimal:
    """
    tasa_día = (1+TEA)^(1/360) - 1  con redondeo a 15 decimales.
    """
    td = (Decimal("1") + tea6) ** (Decimal("1") / Decimal("360")) - Decimal("1")
    return td.quantize(Q15, rounding=ROUND_HALF_UP)

def _interes_inicial_por_peso(tea6: Decimal, dias: int) -> Decimal:
    """
    k = (1+tasa_día)^días - 1
    Donde:
      - tasa_día redondeada a 15 decimales
      - también se redondea el factor (1+tasa_día)^días a 15 decimales
        ANTES de restar 1 (comportamiento observado en Excel).
    """
    td = _tasa_dia_desde_tea(tea6)
    factor = (Decimal("1") + td) ** D(dias)
    factor = factor.quantize(Q15, rounding=ROUND_HALF_UP)
    k = factor - Decimal("1")
    return k

# ==============================
# PMT con redondeos tipo Excel
# ==============================
def _pmt_excel(tm: Decimal, n: int, pv: Decimal) -> Decimal:
    """
    Excel: =ROUND(PMT(TM; n; -PV); 0)
    Con redondeos intermedios:
      - TM a 15 decimales
      - (1+TM)^n a 15 decimales
    """
    tm15 = tm.quantize(Q15, rounding=ROUND_HALF_UP)
    if tm15 == 0:
        cuo = pv / D(n)
    else:
        uno_mas_tm = (Decimal("1") + tm15).quantize(Q15, rounding=ROUND_HALF_UP)
        pot = (uno_mas_tm ** D(n)).quantize(Q15, rounding=ROUND_HALF_UP)
        num = pv * tm15 * pot
        den = pot - Decimal("1")
        cuo = num / den
    return round_excel(cuo, 0)  # pesos

# ==============================
# Cálculos compuestos del Excel
# ==============================
def _monto_financiado_desde_monto(monto_solicitado: Decimal,
                                  k_interes_por_peso: Decimal,
                                  seguro_por_millon: Decimal) -> Decimal:
    """
    Monto financiado = monto + intereses_iniciales + seguro_1er_mes
                     = monto * (1 + k + s)
      con s = seguro_por_millon / 1e6
    """
    s = seguro_por_millon / Decimal("1000000")
    return monto_solicitado * (Decimal("1") + k_interes_por_peso + s)

def _pv_desde_cuota_financiera(tm: Decimal, n: int, cuota_fin: Decimal) -> Decimal:
    """
    PV exacto desde cuota financiera (inversa de PMT).
    Incluye redondeos intermedios a 15 decimales.
    """
    tm15 = tm.quantize(Q15, rounding=ROUND_HALF_UP)
    if tm15 == 0:
        pv = cuota_fin * D(n)
    else:
        uno_mas_tm = (Decimal("1") + tm15).quantize(Q15, rounding=ROUND_HALF_UP)
        pot_neg = (uno_mas_tm ** (-D(n))).quantize(Q15, rounding=ROUND_HALF_UP)
        factor = (Decimal("1") - pot_neg) / tm15
        pv = cuota_fin * factor
    return round_excel(pv, 0)

# ==============================
# API principal (mismo flujo que Excel)
# ==============================
def liquidar_pensionado(p: ParametrosPensionado) -> ResultadoPensionado:
    tm   = _tm_por_indice(p.indice_tasa)
    tea6 = _tea_por_tm_excel(tm)

    k    = _interes_inicial_por_peso(tea6, p.dias_gracia)  # interés por peso
    seg_mm = _seguro_por_edad(p.edad, D(getattr(p, "extraprima_seguro", 0.0)))

    monto = D(p.monto_solicitado)

    intereses_iniciales = (monto * k)
    seguro_primer_mes   = monto * (seg_mm / Decimal("1000000"))
    monto_capitalizar   = intereses_iniciales + seguro_primer_mes
    monto_financiado    = monto + monto_capitalizar

    cuota_financiera    = _pmt_excel(tm, p.plazo_meses, monto_financiado)
    cuota_neta          = D(cuota_financiera) + seg_mm  # seguro $/MM fijo/mes

    return ResultadoPensionado(
        cuota_financiera=float(round_excel(cuota_financiera, 0)),
        cuota_neta=float(round_excel(cuota_neta, 0)),
        disponible_cuota=0.0,
        diferencia_disponible_vs_cuota=0.0,
        seguro_por_millon=float(seg_mm),
        monto_capitalizado=float(monto_capitalizar),
        monto_financiado=float(monto_financiado),
        tasa_mv=float(tm),
        tasa_ea=float(tea6),
        plan_pagos=[],
    )

# ==============================
# Inverso: cuota neta → monto solicitado
# ==============================
def estimar_monto_desde_cuota(edad: int,
                              indice_tasa: int,
                              plazo_meses: int,
                              cuota_neta: float,
                              dias_gracia: int = 30,
                              extraprima: float = 0.0) -> dict:
    tm   = _tm_por_indice(indice_tasa)
    tea6 = _tea_por_tm_excel(tm)
    k    = _interes_inicial_por_peso(tea6, dias_gracia)
    seg_mm = _seguro_por_edad(edad, D(extraprima))

    cuota_neta_d = D(cuota_neta)
    cuota_fin    = cuota_neta_d - seg_mm

    pv = _pv_desde_cuota_financiera(tm, plazo_meses, cuota_fin)

    # PV = monto * (1 + k + s)  ⇒  monto = PV / (1 + k + s)
    s = seg_mm / Decimal("1000000")
    divisor = (Decimal("1") + k + s)
    monto_solicitado = (pv / divisor)
    monto_solicitado = round_excel(monto_solicitado, 0)

    # Recalcular intermedios con ese monto para reportar celdas
    intereses_iniciales = (monto_solicitado * k)
    seguro_primer_mes   = (monto_solicitado * s)
    monto_capitalizar   = intereses_iniciales + seguro_primer_mes
    monto_financiado    = monto_solicitado + monto_capitalizar
    cuota_financiera    = _pmt_excel(tm, plazo_meses, monto_financiado)
    cuota_neta_chk      = cuota_financiera + seg_mm

    return {
        # Tasas
        "tasa_mv": float(tm),
        "tasa_ea": float(tea6),
        "tasa_dia": float(_tasa_dia_desde_tea(tea6)),

        # Inputs y auditoría
        "plazo_meses": plazo_meses,
        "seguro_por_millon": float(seg_mm),

        # Cálculo inverso
        "cuota_neta_input": float(round_excel(cuota_neta_d, 0)),
        "cuota_financiera": float(round_excel(cuota_financiera, 0)),
        "pv_monto_financiado": float(pv),

        "intereses_iniciales": float(intereses_iniciales),
        "seguro_primer_mes": float(seguro_primer_mes),
        "monto_capitalizar": float(monto_capitalizar),
        "monto_financiado": float(monto_financiado),

        "monto_solicitado": float(monto_solicitado),
        "cuota_neta_recalculada": float(round_excel(cuota_neta_chk, 0)),
    }
