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
    Espera un JSON con los campos de ParametrosPensionado.
    Ejemplo mínimo:

    {
      "edad": 75,
      "plazo_meses": 156,
      "monto_solicitado": 15000000,
      "ingresos_totales": 7000000,
      "salud": 400000,
      "pension_aporte": 0,
      "retencion_fuente": 0,
      "fondo_solidaridad": 0,
      "deducciones_totales": 2000000,
      "cuota_compra_cartera": 100000,
      "smmlv": 1423500,
      "codigo_pagaduria": 1,
      "indice_tasa": 6
    }
    """
    data = request.get_json(force=True)
    p = ParametrosPensionado(**data)
    resultado = liquidar_pensionado(p)
    return jsonify(asdict(resultado))


if __name__ == "__main__":
    # Para correrlo localmente si quieres probar en tu PC
    import os

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
