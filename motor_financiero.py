from math import pow

# ==============================================
# MOTOR FINANCIERO BAN100 — v2.0
# ==============================================
# Soporta múltiples perfiles:
#   - pensionado_especial
#   - docente
#   - monto_por_cuota
#   - generico (por defecto)
# ==============================================


# ----------------------------------------------------
# Funciones base
# ----------------------------------------------------
def calcular_cuota(monto, tasa_mensual, meses):
    """Calcula la cuota mensual estándar de un crédito."""
    if tasa_mensual == 0:
        return monto / meses
    return monto * (tasa_mensual * pow(1 + tasa_mensual, meses)) / (pow(1 + tasa_mensual, meses) - 1)


def calcular_monto(cuota, tasa_mensual, meses):
    """Calcula el monto máximo posible dado una cuota y plazo."""
    if tasa_mensual == 0:
        return cuota * meses
    return cuota * ((pow(1 + tasa_mensual, meses) - 1) / (tasa_mensual * pow(1 + tasa_mensual, meses)))


# ----------------------------------------------------
# Router general por perfil
# ----------------------------------------------------
def simular_por_perfil(datos: dict) -> dict:
    """
    Decide qué 'hoja' (perfil) usar según el tipo de cliente:
      - pensionado_especial
      - docente
      - monto_por_cuota
      - generico
    """
    perfil = datos.get("perfil", "generico").lower()

    if perfil == "pensionado_especial":
        return simular_pensionado_especial(datos)

    elif perfil == "docente":
        return simular_docente(datos)

    elif perfil == "monto_por_cuota":
        return simular_monto_por_cuota(datos)

    # Por defecto, usamos la simulación genérica
    return simular_generico(datos)


# ----------------------------------------------------
# PERFIL 1: Pensionados Especiales
# ----------------------------------------------------
def simular_pensionado_especial(datos: dict) -> dict:
    """
    Lógica para 'Pensionados Especiales' (hoja 1).
    Usa tasa EA del 19% como base. Puede ajustarse según tabla en modelos.py.
    """
    try:
        edad = datos.get("edad", None)
        monto = float(datos["monto"])
        plazo = int(datos["plazo_meses"])

        tasa_efectiva_anual = 0.19
        tasa_mensual = pow(1 + tasa_efectiva_anual, 1 / 12) - 1

        cuota = calcular_cuota(monto, tasa_mensual, plazo)
        total = cuota * plazo
        intereses = total - monto

        return {
            "perfil": "pensionado_especial",
            "edad": edad,
            "monto": monto,
            "plazo_meses": plazo,
            "cuota_mensual": round(cuota),
            "total_a_pagar": round(total),
            "intereses": round(intereses),
            "tasa_efectiva_anual": round(tasa_efectiva_anual, 4)
        }

    except Exception as e:
        return {"error": str(e)}


# ----------------------------------------------------
# PERFIL 2: Docentes
# ----------------------------------------------------
def simular_docente(datos: dict) -> dict:
    """
    Lógica para 'Docentes' (hoja 2).
    De momento usa misma tasa que pensionados, pero puede ajustarse.
    """
    try:
        monto = float(datos["monto"])
        plazo = int(datos["plazo_meses"])
        tasa_efectiva_anual = 0.185  # Ejemplo: Docentes tienen una tasa un poco menor
        tasa_mensual = pow(1 + tasa_efectiva_anual, 1 / 12) - 1

        cuota = calcular_cuota(monto, tasa_mensual, plazo)
        total = cuota * plazo
        intereses = total - monto

        return {
            "perfil": "docente",
            "monto": monto,
            "plazo_meses": plazo,
            "cuota_mensual": round(cuota),
            "total_a_pagar": round(total),
            "intereses": round(intereses),
            "tasa_efectiva_anual": round(tasa_efectiva_anual, 4)
        }

    except Exception as e:
        return {"error": str(e)}


# ----------------------------------------------------
# PERFIL 3: Monto por valor cuota
# ----------------------------------------------------
def simular_monto_por_cuota(datos: dict) -> dict:
    """
    Caso en el que el usuario define la cuota deseada y el plazo,
    y queremos calcular el monto máximo posible que puede solicitar.
    """
    try:
        cuota = float(datos["cuota_deseada"])
        plazo = int(datos["plazo_meses"])

        tasa_efectiva_anual = 0.19
        tasa_mensual = pow(1 + tasa_efectiva_anual, 1 / 12) - 1

        # Validación: evitar división por cero
        if tasa_mensual == 0:
            monto = cuota * plazo
        else:
            monto = calcular_monto(cuota, tasa_mensual, plazo)

        total = cuota * plazo
        intereses = total - monto

        return {
            "perfil": "monto_por_cuota",
            "monto_maximo": round(monto),
            "plazo_meses": plazo,
            "cuota_mensual": round(cuota),
            "total_a_pagar": round(total),
            "intereses": round(intereses),
            "tasa_efectiva_anual": round(tasa_efectiva_anual, 4)
        }

    except Exception as e:
        return {"error": str(e)}


# ----------------------------------------------------
# PERFIL 4: Genérico (default)
# ----------------------------------------------------
def simular_generico(datos: dict) -> dict:
    """
    Simulación estándar (monto + plazo).
    """
    try:
        monto = float(datos["monto"])
        plazo = int(datos["plazo_meses"])
        tasa_efectiva_anual = 0.19
        tasa_mensual = pow(1 + tasa_efectiva_anual, 1 / 12) - 1

        cuota = calcular_cuota(monto, tasa_mensual, plazo)
        total = cuota * plazo
        intereses = total - monto

        return {
            "perfil": "generico",
            "monto": monto,
            "plazo_meses": plazo,
            "cuota_mensual": round(cuota),
            "total_a_pagar": round(total),
            "intereses": round(intereses),
            "tasa_efectiva_anual": round(tasa_efectiva_anual, 4)
        }

    except Exception as e:
        return {"error": str(e)}
