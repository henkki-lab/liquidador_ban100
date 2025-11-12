from decimal import Decimal, getcontext, ROUND_HALF_UP
from math import pow  # solo para exponentes enteros en PMT
from modelos import (
    ParametrosPensionado,
    ResultadoPensionado,
    CuotaDetalle,
    TASAS_MAX_PENSIONADOS,
    SEGUROS_EDAD,
)

# ---------------------------------------------------
# Config Decimal y utilidades de redondeo "estilo Excel"
# ---------------------------------------------------
getcontext().prec = 34  # alta precisión interna; controlamos con quantize

Q6   = Decimal("0.000001")               # 6 decimales
Q15  = Decimal("0.000000000000001")      # 15 decimales
Q0   = Decimal("1")                      # redondeo a enteros (pesos)

def d(x) -> Decimal:
    """Convierte a Decimal sin errores binarios (usando str cuando llegue float)."""
    if isinstance(x, Decimal):
        return x
    if isinstance(x, (float, int)):
        return Decimal(str(x))
    return Decimal(x)

def round_excel(x: Decimal, places: int) -> Decimal:
    """ROUND de Excel (ROUND_HALF_UP) a 'places' decimales."""
    if places == 0:
        return x.quantize(Q0, rounding=ROUND_HALF_UP)
    q = Decimal("1").scaleb(-places)  # 10^-places
    return x.quantize(q, rounding=ROUND_HALF_UP)

# ---------------------------------------------------
# Tablas (TM y seguros) en Decimal
# ---------------------------------------------------
def _tm_por_indice(indice: int) -> Decimal:
    fila = TASAS_MAX_PENSIONADOS.get(indice, TASAS_MAX_PENSIONADOS[6])
    return d(fila["tm"])

def _tea_por_tm_excel(tm: Decimal) -> Decimal:
    """
    Excel: =ROUND( (1+TM)^12 - 1 , 6 )
    *Se redondea a 6 decimales ANTES de usar en FV.
    """
    tea = (Decimal("1") + tm) ** Decimal("12") - Decimal("1")
    return round_excel(tea, 6)

def _seguro_por_edad(edad: int, extraprima: Decimal = Decimal("0")) -> Decimal:
    """Valor por millón; aplica (1 + extraprima)."""
    base = d(SEGUROS_EDAD[0]["valor"])
    for r in SEGUROS_EDAD:
        if r["edad_min"] <= edad <= r["edad_max"]:
            base = d(r["valor"])
            break
    return base * (Decimal("1") + extraprima)

def _tasa_dia_desde_tea_excel(tea_6dec: Decimal) -> Decimal:
    """
    Excel: tasa_día = (1+TEA)^(1/360) - 1, redondeada a 15 decimales.
    """
    tasa_dia = (Decimal("1") + tea_6dec) ** (Decimal("1") / Decimal("360")) - Decimal("1")
    return tasa_dia.quantize(Q15, rounding=ROUND_HALF_UP)

def _interes_inicial_por_peso(tea_6dec: Decimal, dias: int) -> Decimal:
    """
    Interés inicial por cada peso solicitado (independiente del monto):
    = (1+tasa_día)^días - 1   con tasa_día redondeada a 15 dec.
    """
    td = _tasa_dia_desde_tea_excel(tea_6dec)
    return ( (Decimal("1") + td) ** d(dias) ) - Decimal("1")

def _pmt_excel(tm: Decimal, n: int, pv: Decimal) -> Decimal:
    """
    Excel: =ROUND(PMT(TM; n; -PV); 0)
    """
    if tm == 0:
        cuo = pv / d(n)
    else:
        uno_mas_tm = Decimal("1") + tm
        num = pv * tm * (uno_mas_tm ** d(n))
        den = (uno_mas_tm ** d(n)) - Decimal("1")
        cuo = num / den
    return round_excel(cuo, 0)

def calcular_monto_financiado(monto_solicitado: Decimal,
                              interes_por_peso: Decimal,
                              seguro_por_millon: Decimal) -> Decimal:
    """
    Monto financiado = monto + intereses_iniciales + seguro_primer_mes
    intereses = monto * interes_por_peso
    seguro_1er_mes = monto * (seguro_por_millon / 1_000_000)
    """
    seguro_1mm = seguro_por_millon / Decimal("1000000")
    return monto_solicitado * (Decimal("1") + interes_por_peso + seguro_1mm)

def calcular_pv_desde_cuota_financiera(tm: Decimal, n: int, cuota_fin: Decimal) -> Decimal:
    """PV exacto desde cuota financiera (inversa de PMT)."""
    if tm == 0:
        pv = cuota_fin * d(n)
    else:
        factor = (Decimal("1") - ( (Decimal("1") + tm) ** (-d(n)) )) / tm
        pv = cuota_fin * factor
    return round_excel(pv, 0)

# ---------------------------------------------------
# Cálculo principal (idéntico a Excel)
# ---------------------------------------------------
def liquidar_pensionado(p: ParametrosPensionado) -> ResultadoPensionado:
    tm = _tm_por_indice(p.indice_tasa)                                # TM
    tea6 = _tea_por_tm_excel(tm)                                      # TEA (6 dec)
    interes_por_peso = _interes_inicial_por_peso(tea6, p.dias_gracia) # k
    seguro_mm = _seguro_por_edad(p.edad, d(getattr(p, "extraprima_seguro", 0.0)))

    monto = d(p.monto_solicitado)

    intereses_iniciales = monto * interes_por_peso
    seguro_primer_mes  = monto * (seguro_mm / Decimal("1000000"))
    monto_capitalizar  = intereses_iniciales + seguro_primer_mes
    monto_financiado   = monto + monto_capitalizar

    cuota_financiera   = _pmt_excel(tm, p.plazo_meses, monto_financiado)
    cuota_neta         = d(cuota_financiera) + seguro_mm  # Seguro $/MM es fijo mensual

    # Construcción del resultado con valores "naturales" (no redondeamos a 0 salvo PMT)
    res = ResultadoPensionado(
        cuota_financiera=float(cuota_financiera),
        cuota_neta=float(round_excel(cuota_neta, 0)),
        disponible_cuota=0.0,
        diferencia_disponible_vs_cuota=0.0,
        seguro_por_millon=float(seguro_mm),
        monto_capitalizado=float(monto_capitalizar),
        monto_financiado=float(monto_financiado),
        tasa_mv=float(tm),
        tasa_ea=float(tea6),
        plan_pagos=[],
    )
    return res

# ---------------------------------------------------
# Cálculo inverso: cuota (neta) → monto solicitado (idéntico a Excel)
# ---------------------------------------------------
def estimar_monto_desde_cuota(edad: int,
                              indice_tasa: int,
                              plazo_meses: int,
                              cuota_neta: float,
                              dias_gracia: int = 30,
                              extraprima: float = 0.0) -> dict:
    """
    Dada la cuota NETA, calcula:
      - cuota_financiera (= cuota - seguro mensual)
      - PV (monto financiado) vía inversa de PMT
      - monto_solicitado despejando capitalización (k + seguro primer mes)
    Todo con el mismo redondeo y pasos que Excel.
    """
    tm   = _tm_por_indice(indice_tasa)
    tea6 = _tea_por_tm_excel(tm)
    k    = _interes_inicial_por_peso(tea6, dias_gracia)        # interés por peso
    seg_mm = _seguro_por_edad(edad, d(extraprima))             # $/MM mensual

    cuota_neta_d = d(cuota_neta)
    cuota_fin = cuota_neta_d - seg_mm                          # cuota financiera

    pv = calcular_pv_desde_cuota_financiera(tm, plazo_meses, cuota_fin)

    # despeje: PV = monto * (1 + k + seg_mm/1e6)  ⇒  monto = PV / (1 + k + s)
    s = seg_mm / Decimal("1000000")
    divisor = Decimal("1") + k + s
    monto_solicitado = (pv / divisor).quantize(Q0, rounding=ROUND_HALF_UP)

    # Recalcular componentes con ese monto para reportar celdas (auditoría)
    intereses_iniciales = d(monto_solicitado) * k
    seguro_primer_mes  = d(monto_solicitado) * s
    monto_capitalizar  = intereses_iniciales + seguro_primer_mes
    monto_financiado   = d(monto_solicitado) + monto_capitalizar
    cuota_financiera   = _pmt_excel(tm, plazo_meses, monto_financiado)
    cuota_neta_chk     = cuota_financiera + seg_mm

    return {
        "tasa_mv": float(tm),
        "tasa_ea": float(tea6),
        "tasa_dia": float(_tasa_dia_desde_tea_excel(tea6)),
        "plazo_meses": plazo_meses,
        "seguro_por_millon": float(seg_mm),

        "cuota_neta_input": float(cuota_neta_d),
        "cuota_financiera": float(cuota_financiera),
        "pv_monto_financiado": float(pv),

        "intereses_iniciales": float(intereses_iniciales),
        "seguro_primer_mes": float(seguro_primer_mes),
        "monto_capitalizar": float(monto_capitalizar),
        "monto_financiado": float(monto_financiado),

        "monto_solicitado": float(monto_solicitado),
        "cuota_neta_recalculada": float(round_excel(cuota_neta_chk, 0)),
    }
