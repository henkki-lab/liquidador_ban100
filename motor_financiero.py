# motor_financiero.py
from decimal import Decimal, getcontext, ROUND_HALF_UP, DivisionUndefined
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
# Precisión alta interna; aplicamos los redondeos "tipo Excel" explícitamente.
getcontext().prec = 34

Q0   = Decimal("1")                  # 0 decimales
Q6   = Decimal("0.000001")           # 6 decimales
Q15  = Decimal("0.000000000000001")  # 15 decimales

def D(x) -> Decimal:
    """Conversión segura a Decimal evitando binarios."""
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
    (Se usa la TEA redondeada a 6 para FV/diario).
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
    tasa_día = (1+TEA)^(1/360) - 1   con redondeo a 15 decimales.
    """
    td = (Decimal("1") + tea6) ** (Decimal("1") / Decimal("360")) - Decimal("1")
    return td.quantize(Q15, rounding=ROUND_HALF_UP)

def _interes_inicial_por_peso(tea6: Decimal, dias: int) -> Decimal:
    """
    k = (1+tasa_día)^días - 1
    - tasa_día a 15 decimales
    - (1+tasa_día)^días redondeado a 15 ANTES de restar 1 (comportamiento Excel).
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
    Redondeos intermedios:
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
        # Evitar DivisionUndefined si n=0 o den=0 (caso límite)
        if den == 0:
            cuo = pv / D(max(n, 1))
        else:
            cuo = num / den
    return round_excel(cuo, 0)  # pesos (0 decimales)

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
    PV exacto desde cuota financiera (inversa de PMT) con redondeos a 15 dec.
    """
    tm15 = tm.quantize(Q15, rounding=ROUND_HALF_UP)
    if tm15 == 0:
        pv = cuota_fin * D(n)
    else:
        uno_mas_tm = (Decimal("1") + tm15).quantize(Q15, rounding=ROUND_HALF_UP)
        pot_neg = (uno_mas_tm ** (-D(n))).quantize(Q15, rounding=ROUND_HALF_UP)
        # (1 - (1+tm)^(-n)) / tm
        den = tm15
        if den == 0:
            pv = cuota_fin * D(n)
        else:
            factor = (Decimal("1") - pot_neg) / den
            pv = cuota_fin * factor
    return round_excel(pv, 0)

# ==============================
# API principal (mismo flujo que Excel)
# ==============================
def liquidar_pensionado(p: ParametrosPensionado) -> ResultadoPensionado:
    tm   = _tm_por_indice(p.indice_tasa)
    tea6 = _tea_por_tm_excel(tm)

    k      = _interes_inicial_por_peso(tea6, p.dias_gracia)
    seg_mm = _seguro_por_edad(p.edad, D(getattr(p, "extraprima_seguro", 0.0)))

    monto = D(p.monto_solicitado)

    # Intermedios Excel
    intereses_iniciales = (monto * k)
    seguro_primer_mes   = monto * (seg_mm / Decimal("1000000"))
    monto_capitalizar   = intereses_iniciales + seguro_primer_mes
    monto_financiado    = monto + monto_capitalizar

    # B26 (ROUND PMT(...), 0)
    cuota_financiera    = _pmt_excel(tm, p.plazo_meses, monto_financiado)

    # *** B28 EXACTA ***
    # = B26 + (B27 * (B20/1e6))
    cuota_neta = D(cuota_financiera) + (seg_mm * (monto / Decimal("1000000")))

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
# Inverso EXACTO (cuota neta → monto solicitado)
# ==============================
def _cuota_neta_from_monto(tm: Decimal, n: int, k: Decimal, seg_mm: Decimal, monto: Decimal) -> Decimal:
    """
    Implementa exactamente:  B28 = ROUND(PMT(TM; n; - monto*(1+k+s)), 0) + s*monto
    con s = seg_mm / 1e6
    """
    s  = seg_mm / Decimal("1000000")
    pv = monto * (Decimal("1") + k + s)
    cuota_fin = _pmt_excel(tm, n, pv)               # B26 (ya redondeada a 0)
    return D(cuota_fin) + (s * monto)               # B28

def estimar_monto_desde_cuota(edad: int,
                              indice_tasa: int,
                              plazo_meses: int,
                              cuota_neta: float,
                              dias_gracia: int = 30,
                              extraprima: float = 0.0) -> dict:
    """
    Resuelve por bisección el monto 'm' tal que:
      cuota_neta = ROUND(PMT(tm, n, -m*(1+k+s)), 0) + s*m
    con s = seg_mm/1e6, k = interés por peso de días de gracia.
    Tolerancia: 0.5 pesos.
    """
    tm   = _tm_por_indice(indice_tasa)
    tea6 = _tea_por_tm_excel(tm)
    k    = _interes_inicial_por_peso(tea6, dias_gracia)
    seg_mm = _seguro_por_edad(edad, D(extraprima))

    target = D(cuota_neta)

    # Cotas iniciales: empezamos bajos y subimos exponencialmente hasta cubrir el target.
    low  = D(0)
    high = D(1)
    # Asegurar que f(high) >= target
    for _ in range(64):
        f_high = _cuota_neta_from_monto(tm, plazo_meses, k, seg_mm, high)
        if f_high >= target:
            break
        high *= 2
    # Si incluso con high grande no llegamos (caso extremo), seguimos agrandando un poco más
    for _ in range(16):
        f_high = _cuota_neta_from_monto(tm, plazo_meses, k, seg_mm, high)
        if f_high >= target:
            break
        high *= 2

    # Bisección
    tol = D("0.5")  # precisión de 50 centavos (antes de ROUND final)
    for _ in range(120):
        mid = (low + high) / D(2)
        f_mid = _cuota_neta_from_monto(tm, plazo_meses, k, seg_mm, mid)
        if abs(f_mid - target) <= tol:
            monto_sol = round_excel(mid, 0)
            break
        if f_mid < target:
            low = mid
        else:
            high = mid
    else:
        monto_sol = round_excel((low + high) / D(2), 0)

    # Recalcular intermedios exactamente como Excel para reportar
    s = seg_mm / Decimal("1000000")
    intereses_iniciales = (monto_sol * k)
    seguro_primer_mes   = (monto_sol * s)
    monto_capitalizar   = intereses_iniciales + seguro_primer_mes
    monto_financiado    = monto_sol + monto_capitalizar
    cuota_financiera    = _pmt_excel(tm, plazo_meses, monto_financiado)
    cuota_neta_chk      = D(cuota_financiera) + (s * monto_sol)

    return {
        # Tasas (para auditoría)
        "tasa_mv": float(tm),
        "tasa_ea": float(tea6),
        "tasa_dia": float(_tasa_dia_desde_tea(tea6)),

        # Inputs
        "plazo_meses": plazo_meses,
        "seguro_por_millon": float(seg_mm),

        # Auditoría de cálculo inverso
        "cuota_neta_input": float(round_excel(target, 0)),
        "cuota_financiera": float(round_excel(cuota_financiera, 0)),
        "pv_monto_financiado": float(round_excel(monto_financiado, 0)),

        "intereses_iniciales": float(intereses_iniciales),
        "seguro_primer_mes": float(seguro_primer_mes),
        "monto_capitalizar": float(monto_capitalizar),
        "monto_financiado": float(monto_financiado),

        "monto_solicitado": float(monto_sol),
        "cuota_neta_recalculada": float(round_excel(cuota_neta_chk, 0)),
    }
