from dataclasses import dataclass
from typing import List

# === Tabla de tasas (A100:A105 y "Ley 1527 6") ===
TASAS_MAX_PENSIONADOS = {
    1: 0.0179,
    2: 0.0173,
    3: 0.0182,
    4: 0.0176,
    5: 0.0160,
    6: 0.0146,   # La que estás usando en el archivo (Ley 1527 6)
}

@dataclass
class ParametrosPensionado:
    edad: int
    plazo_meses: int
    monto_solicitado: float
    ingresos_totales: float
    salud: float
    pension_aporte: float
    retencion_fuente: float
    fondo_solidaridad: float
    deducciones_totales: float
    cuota_compra_cartera: float
    smmlv: float
    codigo_pagaduria: int
    indice_tasa: int
    dias_gracia: int = 30
    extraprima_seguro: float = 0.0

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
