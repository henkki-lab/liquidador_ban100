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
    ingresos_totales: float = 0.0
    salud: float = 0.0
    pension_aporte: float = 0.0
    retencion_fuente: float = 0.0
    fondo_solidaridad: float = 0.0
    deducciones_totales: float = 0.0
    cuota_compra_cartera: float = 0.0
    smmlv: float = 0.0
    codigo_pagaduria: int = 0
    indice_tasa: int = 0
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
