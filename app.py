from dataclasses import asdict
from flask import Flask, request, jsonify
from modelos import ParametrosPensionado
from motor_financiero import liquidar_pensionado

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "💰 Liquidador Ban100 está corriendo correctamente (v1.0 con precisión de 15 decimales)."

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

@app.route("/calcular", methods=["POST"])
def calcular():
    """Endpoint simplificado para WhatsApp/n8n."""
    try:
        data = request.get_json(force=True)
        edad = int(data.get("edad", 0))
        plazo = int(data.get("plazo", 0))
        monto = float(data.get("monto", 0))
        indice = int(data.get("indice_tasa", 5))  # 1,60% por defecto

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

