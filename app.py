from dataclasses import asdict
from flask import Flask, request, jsonify
from modelos import ParametrosPensionado
from motor_financiero import (
    liquidar_pensionado,
    obtener_tm_por_indice,
    calcular_monto_desde_cuota
)

app = Flask(__name__)

# -----------------------------------------------------
# Página principal (verificación)
# -----------------------------------------------------
@app.route("/", methods=["GET"])
def home():
    return "💰 Liquidador Ban100 está corriendo correctamente (v1.1 con precisión de 15 decimales)."


# -----------------------------------------------------
# Endpoint completo con todos los parámetros
# -----------------------------------------------------
@app.route("/liquidar", methods=["POST"])
def liquidar():
    """Endpoint completo para cálculo total."""
    try:
        data = request.get_json(force=True)
        p = ParametrosPensionado(**data)
        resultado = liquidar_pensionado(p)
        return jsonify(asdict(resultado))
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# -----------------------------------------------------
# Endpoint simplificado (para WhatsApp / n8n)
# -----------------------------------------------------
@app.route("/calcular", methods=["POST"])
def calcular():
    """Versión simplificada: calcula valores principales con pocos datos."""
    try:
        data = request.get_json(force=True)
        edad = int(data.get("edad", 0))
        plazo = int(data.get("plazo", 0))
        monto = float(data.get("monto", 0))
        indice = int(data.get("indice_tasa", 5))  # 1.46% por defecto

        p = ParametrosPensionado(
            edad=edad,
            plazo_meses=plazo,
            monto_solicitado=monto,
            indice_tasa=indice
        )

        resultado = liquidar_pensionado(p)

        return jsonify({
            "cuota_financiera": round(resultado.cuota_financiera, 3),
            "cuota_neta": round(resultado.cuota_neta, 3),
            "monto_capitalizado": round(resultado.monto_capitalizado, 3),
            "monto_financiado": round(resultado.monto_financiado, 3),
            "seguro_por_millon": resultado.seguro_por_millon,
            "tasa_mv": resultado.tasa_mv,
            "tasa_ea": resultado.tasa_ea
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# -----------------------------------------------------
# NUEVO ENDPOINT: cálculo inverso (desde cuota → monto)
# -----------------------------------------------------
@app.route("/invertir", methods=["POST"])
def invertir():
    """
    Calcula el monto aproximado solicitado a partir de una cuota mensual,
    plazo y tasa mensual (índice). Usa la fórmula inversa de PMT.
    """
    try:
        data = request.get_json(force=True)
        cuota = float(data.get("cuota", 0))
        plazo = int(data.get("plazo", 0))
        indice = int(data.get("indice_tasa", 6))  # 1.46% por defecto
        edad = int(data.get("edad", 70))

        # Obtener tasa mensual (TM)
        tm = obtener_tm_por_indice(indice)

        # Calcular monto financiado (aproximado)
        monto_financiado = calcular_monto_desde_cuota(tm, plazo, cuota)

        return jsonify({
            "tasa_mv": round(tm, 15),
            "plazo_meses": plazo,
            "cuota_mensual": cuota,
            "monto_aprox_financiado": round(monto_financiado, 0)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# -----------------------------------------------------
# Ejecución local / Render
# -----------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
