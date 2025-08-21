import os
import logging
import json
from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse

# --- Configuración Inicial ---
logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

# --- Webhook Principal de la Aplicación ---
@app.route("/bot", methods=["POST"])
def whatsapp_webhook():
    """
    Esta función solo hace dos cosas:
    1. Registra los datos recibidos en los logs de Render.
    2. Responde con un mensaje fijo para confirmar que el nuevo código está activo.
    """
    # Usamos logging.error para asegurarnos de que el mensaje aparezca en los logs
    all_data = request.values.to_dict()
    logging.error(f"DIAGNOSTICO FINAL - DATOS RECIBIDOS: {json.dumps(all_data)}")

    # Respondemos con un mensaje de prueba fijo
    twiml = MessagingResponse()
    twiml.message("Prueba final exitosa. El nuevo código está funcionando.")
    
    return Response(str(twiml), mimetype="application/xml")

# --- Iniciar la Aplicación ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
