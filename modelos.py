from dataclasses import dataclass
from typing import List, Dict

# === Tasas Máximas Pensionados (Ley 1527) con precisión de 15 decimales ===
# Estas tasas corresponden a las TM (tasa mensual) y su TEA asociada, calculadas
# con 15 decimales exactos según la fórmula (1 + TM)^12 - 1.
# Nunca redondees antes de los cálculos: Excel usa doble precisión IEEE-754.

TASAS_MAX_PENSIONADOS: Dict[int, Dict[str, float]] = {
    1: {"tm": 0.0179},  # 1,79% MV
    2: {"tm": 0.0173},  # 1,73% MV
    3: {"tm": 0.0182},  # 1,82% MV
    4: {"tm": 0.0176},  # 1,76% MV
    5: {"tm": 0.0160},  # 1,60% MV
    6: {"tm": 0.0146},  # 1,46% MV
}
# Nota: La hoja usa TEA = ROUND(((1+TM)^12)-1, 6). Para ser idénticos al Excel,
# la TEA se recalcula con ese redondeo antes de FV (ver motor_financiero.py).


# === Tabla de seguros por edad (en pesos por millón) ===
# Estos valores son fijos y se usan según el rango de edad del cliente.
SEGUROS_EDAD: List[Dict[str, float]] = [
    {"edad_min": 18, "edad_max": 75, "valor": 1032.00},
    {"edad_min": 76, "edad_max": 78, "valor": 5272.00},
    {"edad_min": 79, "edad_max": 81, "valor": 8071.00},
    {"edad_min": 82, "edad_max": 84, "valor": 13421.00},
]

# === Clases de datos principales ===

@dataclass
class ParametrosPensionado:
    edad: int
    plazo_meses: int
    monto_solicitado: float
    ingresos_totales: float = 0.0
    salud: float = 0.0
    pension_aporte: float = 0.0
    retencion_fuente: float = 0.0
    fondo_solidaridad: float = 0.0
    deducciones_totales: float = 0.0
    cuota_compra_cartera: float = 0.0
    smmlv: float = 0.0
    codigo_pagaduría: int = 0
    indice_tasa: int = 6
    dias_gracia: int = 30
    extraprima_seguro: float = 0.0
    embargado: bool = False
    tipo_credito: str = "libre_inversion"


@dataclass
class CuotaDetalle:
    numero: int
    abono_capital: float
    interes: float
    seguro: float
    cuota_total: float
    saldo_final: float


@dataclass
class ResultadoPensionado:
    cuota_financiera: float
    cuota_neta: float
    disponible_cuota: float
    diferencia_disponible_vs_cuota: float
    seguro_por_millon: float
    monto_capitalizado: float
    monto_financiado: float
    tasa_mv: float
    tasa_ea: float
    plan_pagos: List[CuotaDetalle]
