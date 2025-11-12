from dataclasses import asdict
from flask import Flask, request, jsonify
from modelos import ParametrosPensionado
from motor_financiero import (
    liquidar_pensionado,
    estimar_monto_desde_cuota,
)
from decimal import Decimal, DivisionUndefined, InvalidOperation

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "💰 Liquidador Ban100 activo (v2.2 robusta — entrada flexible y precisión Excel)."

# ==============================
# 1️⃣ Endpoint clásico: Monto → Cuota
# ==============================
@app.route("/liquidar", methods=["POST"])
def liquidar():
    """Cálculo completo de cuota financiera y neta."""
    try:
        data = request.get_json(force=True)
        p = ParametrosPensionado(**data)
        resultado = liquidar_pensionado(p)
        return jsonify(asdict(resultado))
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ==============================
# 2️⃣ Endpoint simple: Monto → Cuota (para WhatsApp o n8n)
# ==============================
@app.route("/calcular", methods=["POST"])
def calcular():
    """Versión simplificada para WhatsApp/n8n."""
    try:
        data = request.get_json(force=True)
        edad = int(data.get("edad", 0))
        plazo = int(data.get("plazo", data.get("plazo_meses", 0)))
        monto = float(data.get("monto", data.get("monto_solicitado", 0)))
        indice = int(data.get("indice_tasa", 5))  # 1.46% por defecto

        p = ParametrosPensionado(
            edad=edad,
            plazo_meses=plazo,
            monto_solicitado=monto,
            indice_tasa=indice
        )
        r = liquidar_pensionado(p)

        seguro_s_mm = r.seguro_por_millon
        seguro_primer_mes = round(monto * seguro_s_mm / 1_000_000, 0)
        intereses_iniciales = round(r.monto_capitalizado - seguro_primer_mes, 0)

        return jsonify({
            "tasa_mv": r.tasa_mv,
            "tasa_ea": r.tasa_ea,
            "seguro_por_millon": r.seguro_por_millon,
            "intereses_iniciales": intereses_iniciales,
            "seguro_primer_mes": seguro_primer_mes,
            "monto_capitalizar": round(r.monto_capitalizado, 0),
            "monto_financiado": round(r.monto_financiado, 0),
            "cuota_financiera": round(r.cuota_financiera, 0),
            "cuota_neta": round(r.cuota_neta, 0),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ==============================
# 3️⃣ Nuevo endpoint: Cuota → Monto
# ==============================
@app.route("/estimarmonto", methods=["POST"])
def estimar_monto():
    """
    Estima el monto solicitado a partir de la cuota mensual.
    Acepta formatos flexibles como:
      {
        "cuota": 303428,
        "plazo": 156,
        "indice_tasa": 5,
        "edad": 75
      }
    o bien:
      {
        "perfil": "monto_por_cuota",
        "cuota_deseada": 350000,
        "plazo_meses": 96
      }
    """
    try:
        data = request.get_json(force=True)

        # 🔄 Detección flexible de nombres
        cuota = float(data.get("cuota", data.get("cuota_deseada", 0)))
        plazo = int(data.get("plazo", data.get("plazo_meses", 0)))
        indice = int(data.get("indice_tasa", 5))
        edad = int(data.get("edad", 70))
        dias_gracia = int(data.get("dias_gracia", 30))
        extraprima = float(data.get("extraprima", 0))

        # Validación mínima
        if cuota <= 0 or plazo <= 0:
            return jsonify({"error": "Faltan datos válidos (cuota > 0 y plazo > 0 requeridos)."}), 400

        # Llamar función principal del motor
        try:
            out = estimar_monto_desde_cuota(
                edad=edad,
                indice_tasa=indice,
                plazo_meses=plazo,
                cuota_neta=cuota,
                dias_gracia=dias_gracia,
                extraprima=extraprima
            )
        except (DivisionUndefined, InvalidOperation):
            return jsonify({"error": "Error matemático: división indefinida o tasa inválida."}), 400

        return jsonify(out)

    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ==============================
# 🚀 Inicialización
# ==============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
