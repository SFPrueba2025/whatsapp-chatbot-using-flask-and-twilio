import os
import logging
import threading
import json
from flask import Flask, request, Response
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
# No importamos Gemini en esta versión de diagnóstico

# --- Configuración Inicial ---
logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

# --- Clientes de API (solo Twilio por ahora) ---
try:
    TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_NUMBER = os.environ.get("TWILIO_WHATSAPP_NUMBER")
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER]):
        raise ValueError("Faltan una o más variables de entorno de Twilio")
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    logging.info("✅ Cliente de Twilio configurado correctamente.")
except Exception as e:
    logging.error(f"❌ Error configurando Twilio: {e}")
    twilio_client = None

# --- Función de Lógica de Diagnóstico ---

def send_debug_message(from_number: str, debug_data: str):
    """
    Función en segundo plano que envía únicamente un mensaje de depuración.
    """
    logging.info(f"Enviando datos de depuración a {from_number}...")
    
    if twilio_client:
        try:
            # Mensaje de depuración con los datos de Twilio
            twilio_client.messages.create(
                body=f"DEBUG DATA:\n\n{debug_data}",
                from_=TWILIO_WHATSAPP_NUMBER,
                to=from_number
            )
            logging.info(f"Mensaje de depuración enviado a {from_number}")
        except Exception as e:
            logging.error(f"❌ Error enviando mensaje de depuración: {e}")

# --- Webhook Principal de la Aplicación ---

@app.route("/bot", methods=["POST"])
def whatsapp_webhook():
    """
    Recibe el mensaje de Twilio, responde inmediatamente y envía los datos
    recibidos de vuelta al usuario para depuración.
    """
    all_data = request.values.to_dict()
    debug_string = json.dumps(all_data, indent=2) # Lo formateamos para que sea legible
    from_number = request.values.get("From", "")
    
    # Iniciamos el envío del mensaje de depuración en segundo plano
    if from_number:
        thread = threading.Thread(
            target=send_debug_message,
            args=(from_number, debug_string)
        )
        thread.start()

    # Respondemos a Twilio inmediatamente para que no haya timeout
    twiml = MessagingResponse()
    # No enviamos ningún texto aquí para no confundir.
    
    return Response(str(twiml), mimetype="application/xml")

# --- Iniciar la Aplicación ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
