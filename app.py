from dataclasses import asdict
from flask import Flask, request, jsonify
from modelos import ParametrosPensionado
from motor_financiero import liquidar_pensionado, estimar_monto_desde_cuota

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "💰 Liquidador Ban100 está corriendo correctamente."

@app.route("/liquidar", methods=["POST"])
def liquidar():
    """
    Calcula todos los valores del pensionado a partir de los parámetros enviados.
    """
    try:
        data = request.get_json(force=True)
        p = ParametrosPensionado(**data)
        resultado = liquidar_pensionado(p)
        return jsonify(asdict(resultado))
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/estimarmonto", methods=["POST"])
def estimar_monto():
    """
    Estima el monto solicitado dado un valor de cuota neta deseada.
    """
    try:
        data = request.get_json(force=True)

        edad = int(data.get("edad"))
        indice_tasa = int(data.get("indice_tasa"))
        plazo = int(data.get("plazo"))
        cuota = float(data.get("cuota"))

        resultado = estimar_monto_desde_cuota(
            edad=edad,
            indice_tasa=indice_tasa,
            plazo_meses=plazo,
            cuota_neta=cuota
        )

        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
