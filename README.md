# Liquidador Ban100

Motor financiero en Python que replica los cálculos del archivo Excel
**“Liquidador Cuota Ban100 Abr 2025 Campaña Compra y Retanqueo tasa 1,46%”**.

## Estructura
- `modelos.py` → Estructuras de datos y clases base  
- `tablas_excel.py` → Tablas, tasas y funciones auxiliares  
- `motor_financiero.py` → Motor principal de cálculo  

## Ejemplo de uso
```python
from modelos import ParametrosPensionado
from motor_financiero import liquidar_pensionado

p = ParametrosPensionado(
    edad=75,
    plazo_meses=156,
    monto_solicitado=15000000,
    ingresos_totales=7000000,
    salud=400000,
    pension_aporte=0,
    retencion_fuente=0,
    fondo_solidaridad=0,
    deducciones_totales=2000000,
    cuota_compra_cartera=100000,
    smmlv=1423500,
    codigo_pagaduria=1,
    indice_tasa=6
)

resultado = liquidar_pensionado(p)
print(resultado.cuota_neta)
