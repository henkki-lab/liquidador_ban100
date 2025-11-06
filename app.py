from flask import Flask, request, jsonify
from motor_financiero import LiquidarPensionado, ParametrosPensionado

app = Flask(__name__)

@app.route("/")
def home():
    return "💰 Liquidador Ban100 está corriendo correctamente."

@app.route("/calcular", methods=["POST"])
def calcular():
    try:
        data = request.get_json(force=True)

        # Extraer los datos del JSON recibido
        edad = float(data.get("edad", 0))
        monto = float(data.get("monto", 0))
        plazo_meses = int(data.get("plazo_meses", 0))
        embargado = bool(data.get("embargado", False))
        tipo = data.get("tipo", "libre_inversion")

        # Crear parámetros (ajusta si tu clase tiene otros nombres)
        parametros = ParametrosPensionado(
            edad=edad,
            p_monto_solicitado=monto,
            p_plazo_meses=plazo_meses,
            embargado=embargado,
            tipo_credito=tipo
        )

        # Llamar tu función financiera
        resultado = LiquidarPensionado(parametros)

        # Preparar texto de respuesta para WhatsApp
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
    app.run(host="0.0.0.0", port=10000)
