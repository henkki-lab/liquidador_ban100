# 💰 Liquidador Ban100

Motor financiero en **Python** que replica los cálculos del archivo Excel  
**“Liquidador Cuota Ban100 Abr 2025 — Campaña Compra y Retanqueo tasa 1,46%”**  
utilizando la misma lógica de fórmulas, tasas y precisión de 15 decimales que maneja Excel.

---

## 🧩 Estructura del Proyecto

/liquidador_ban100/
│
├── app.py → Microservicio Flask: define los endpoints / y /liquidar
├── modelos.py → Dataclasses, tasas y constantes base (seguro por edad, TM ↔ TEA, etc.)
├── motor_financiero.py → Lógica principal de cálculo (idéntica al Excel)
├── tablas_excel.py → Tasas y equivalencias TM ↔ TEA según Ley 1527
├── requirements.txt → Dependencias necesarias para Render
├── test_motor.py → Pruebas unitarias y verificación de precisión
└── README.md → Este archivo
---

## ⚙️ Ejemplo de Uso Local

Ejemplo para ejecutar el cálculo de un pensionado:

```python
from modelos import ParametrosPensionado
from motor_financiero import liquidar_pensionado

p = ParametrosPensionado(
    edad = 75,
    plazo_meses = 156,
    monto_solicitado = 15000000,
    ingresos_totales = 7000000,
    salud = 400000,
    pension_aporte = 0,
    retencion_fuente = 0,
    fondo_solidaridad = 0,
    deducciones_totales = 2000000,
    cuota_compra_cartera = 100000,
    smmlv = 1435000,
    codigo_pagaduría = 1,
    indice_tasa = 6
)

resultado = liquidar_pensionado(p)
print(resultado.cuota_neta)
