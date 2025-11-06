def tasa_desde_indice(indice: int) -> float:
    """Equivalente a la celda H10 en Excel."""
    TASAS_MAX_PENSIONADOS = {
        1: 0.0179,
        2: 0.0173,
        3: 0.0182,
        4: 0.0176,
        5: 0.0160,
        6: 0.0146,
    }
    return TASAS_MAX_PENSIONADOS.get(indice, 0.0146)

def tasa_ea_desde_mv(tasa_mv: float) -> float:
    """I10 = ROUND(((1+H10)^12)-1,6)"""
    return round(((1 + tasa_mv) ** 12) - 1, 6)

def seguro_por_millon(edad: int, extraprima: float = 0.0) -> float:
    """Replica la lógica de H18 en Excel."""
    if edad <= 75:
        base = 1032
    elif edad <= 78:
        base = 5272
    elif edad <= 81:
        base = 8071
    elif edad <= 84:
        base = 13421
    else:
        raise ValueError("Edad fuera de rango (No viable en el Excel)")
    return base * (1 + extraprima)
