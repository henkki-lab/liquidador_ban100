from dataclasses import asdict
from flask import Flask, request, jsonify
from modelos import ParametrosPensionado
from motor_financiero import liquidar_pensionado

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "💰 Liquidador Ban100 está corriendo correctamente."

@app.route("/liquidar", methods=["POST"])
def liquidar():
    """
    Endpoint original: calcula usando parámetros completos del pensionado
    """
    data = request.get_json(force=True)
    p = ParametrosPensionado(**data)
    resultado = liquidar_pensionado(p)
    return jsonify(asdict(resultado))

@app.route("/calcular", methods=["POST"])
def calcular():
    """
    Nuevo endpoint: versión simplificada para WhatsApp
    """
    try:
        data = request.get_json(force=True)

        edad = float(data.get("edad", 0))
        monto = float(data.get("monto", 0))
        plazo_meses = int(data.get("plazo_meses", 0))
        embargado = bool(data.get("embargado", False))
        tipo = data.get("tipo", "libre_inversion")

       parametros = ParametrosPensionado(
         edad=edad,
         monto_solicitado=monto,
         plazo_meses=plazo_meses,
         embargado=embargado,
        tipo_credito=tipo
        )

        resultado = liquidar_pensionado(parametros)

        respuesta_texto = (
            f"💸 *Simulación de crédito Ban100*\n\n"
            f"Edad: {edad}\n"
            f"Monto solicitado: ${monto:,.0f}\n"
            f"Plazo: {plazo_meses} meses\n"
            f"Tipo: {tipo.replace('_', ' ').title()}\n"
            f"Cuota mensual aprox: ${resultado.cuota_neta:,.0f}\n"
            f"Disponible: ${resultado.diferencia_disponible_vs_cuota:,.0f}\n"
            f"Tasa efectiva anual: {resultado.tasa_ea:.2f}%\n"
        )

        return jsonify({"respuesta": respuesta_texto})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))

    app.run(host="0.0.0.0", port=port)



