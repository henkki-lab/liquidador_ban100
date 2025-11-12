from dataclasses import asdict
from flask import Flask, request, jsonify
from modelos import ParametrosPensionado
from motor_financiero import (
    liquidar_pensionado,
    estimar_monto_desde_cuota,
)

app = Flask(__name__)

# ------------------------------------------
@app.route("/", methods=["GET"])
def home():
    return "💰 Liquidador Ban100 activo (v2.0 precisión Excel: 15 decimales / redondeos idénticos)."

# ------------------------------------------
@app.route("/liquidar", methods=["POST"])
def liquidar():
    """Cálculo completo (mismo flujo que Excel)."""
    try:
        data = request.get_json(force=True)
        p = ParametrosPensionado(**data)
        resultado = liquidar_pensionado(p)
        return jsonify(asdict(resultado))
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ------------------------------------------
@app.route("/calcular", methods=["POST"])
def calcular():
    """
    Versión simplificada: edad, plazo, monto, indice_tasa.
    Devuelve también todas las celdas intermedias para auditoría.
    """
    try:
        data = request.get_json(force=True)
        edad   = int(data.get("edad", 0))
        plazo  = int(data.get("plazo", 0))
        monto  = float(data.get("monto", 0))
        indice = int(data.get("indice_tasa", 5))  # 1.46% por defecto

        p = ParametrosPensionado(
            edad=edad,
            plazo_meses=plazo,
            monto_solicitado=monto,
            indice_tasa=indice
        )
        r = liquidar_pensionado(p)

        # Extiende respuesta con campos intermedios (ya vienen en r)
        return jsonify({
            "tasa_mv": r.tasa_mv,
            "tasa_ea": r.tasa_ea,
            "seguro_por_millon": r.seguro_por_millon,

            "intereses_iniciales": round(r.monto_capitalizado - (monto * r.seguro_por_millon / 1_000_000), 3),
            "seguro_primer_mes": round(monto * r.seguro_por_millon / 1_000_000, 3),
            "monto_capitalizar": round(r.monto_capitalizado, 3),
            "monto_financiado": round(r.monto_financiado, 3),

            "cuota_financiera": round(r.cuota_financiera, 3),
            "seguro_s_mm": r.seguro_por_millon,
            "cuota_neta": round(r.cuota_neta, 3),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ------------------------------------------
@app.route("/estimarmonto", methods=["POST"])
def estimar_monto():
    """
    Cálculo inverso: desde cuota NETA (con seguro incluido) → monto solicitado.
    Devuelve también todas las celdas intermedias para verificar contra Excel.
    """
    try:
        data = request.get_json(force=True)
        cuota  = float(data.get("cuota", 0))
        plazo  = int(data.get("plazo", 0))
        indice = int(data.get("indice_tasa", 5))  # 1.46% por defecto
        edad   = int(data.get("edad", 70))

        out = estimar_monto_desde_cuota(
            edad=edad,
            indice_tasa=indice,
            plazo_meses=plazo,
            cuota_neta=cuota,
            dias_gracia=30,
            extraprima=0.0
        )
        return jsonify(out)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
