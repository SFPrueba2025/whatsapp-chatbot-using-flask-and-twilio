import os
import logging
import threading
import json
from flask import Flask, request, Response
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
import google.generativeai as genai

# --- Configuración Inicial ---
logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

# --- Claves y Clientes de API (desde Variables de Entorno) ---

# Gemini
try:
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        raise ValueError("La variable de entorno GEMINI_API_KEY no está definida")
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    logging.info("✅ Modelo de Gemini configurado correctamente.")
except Exception as e:
    logging.error(f"❌ Error configurando Gemini: {e}")
    model = None

# Twilio
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

# --- Funciones de Lógica ---

def chat_with_gemini(message: str) -> str:
    """Genera una respuesta usando el modelo de Gemini."""
    if not model:
        return "Error: El modelo de IA no está disponible."
    if not message.strip():
        return "Por favor, envíame una pregunta o algo de contexto para poder responder."
    try:
        response = model.generate_content(message)
        return response.text
    except Exception as e:
        logging.error(f"❌ Error al generar contenido con Gemini: {e}")
        return "Lo siento, ocurrió un error al procesar tu mensaje."

def process_and_reply(incoming_msg: str, from_number: str, debug_data: str):
    """
    Función en segundo plano que procesa con Gemini y envía la respuesta
    final, además de un mensaje de depuración.
    """
    logging.info(f"Procesando en segundo plano para {from_number}...")
    
    # 1. Obtener la respuesta de Gemini
    reply_text = chat_with_gemini(incoming_msg)
    
    # 2. Enviar la respuesta final y el mensaje de depuración
    if twilio_client:
        try:
            # Mensaje con la respuesta de Gemini
            twilio_client.messages.create(
                body=reply_text,
                from_=TWILIO_WHATSAPP_NUMBER,
                to=from_number
            )
            logging.info(f"Respuesta de Gemini enviada a {from_number}")

            # Mensaje de depuración con los datos de Twilio
            twilio_client.messages.create(
                body=f"DEBUG DATA:\n{debug_data}",
                from_=TWILIO_WHATSAPP_NUMBER,
                to=from_number
            )
            logging.info(f"Mensaje de depuración enviado a {from_number}")

        except Exception as e:
            logging.error(f"❌ Error enviando mensaje con la API de Twilio: {e}")

# --- Webhook Principal de la Aplicación ---

@app.route("/bot", methods=["POST"])
def whatsapp_webhook():
    """
    Recibe el mensaje de Twilio, responde inmediatamente y lanza el
    procesamiento en segundo plano.
    """
    # Capturamos todos los datos recibidos para depuración
    all_data = request.values.to_dict()
    debug_string = json.dumps(all_data, indent=2) # Lo formateamos para que sea legible

    incoming_msg = request.values.get("Body", "").strip()
    from_number = request.values.get("From", "")
    
    # Iniciamos el procesamiento en segundo plano, pasando los datos de depuración
    if from_number:
        thread = threading.Thread(
            target=process_and_reply,
            args=(incoming_msg, from_number, debug_string)
        )
        thread.start()

    # Respondemos a Twilio inmediatamente
    twiml = MessagingResponse()
    twiml.message("Procesando tu solicitud... 🤔")
    
    return Response(str(twiml), mimetype="application/xml")

# --- Iniciar la Aplicación ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
