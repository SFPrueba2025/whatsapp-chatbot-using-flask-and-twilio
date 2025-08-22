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
        raise ValueError("GEMINI_API_KEY no está definida")
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    logging.info("✅ Modelo de Gemini configurado.")
except Exception as e:
    logging.error(f"❌ Error configurando Gemini: {e}")
    model = None

# Twilio
try:
    TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_NUMBER = os.environ.get("TWILIO_WHATSAPP_NUMBER")
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER]):
        raise ValueError("Faltan variables de entorno de Twilio")
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    logging.info("✅ Cliente de Twilio configurado.")
except Exception as e:
    logging.error(f"❌ Error configurando Twilio: {e}")
    twilio_client = None

# --- Funciones de Lógica ---
def get_message_body(data: dict) -> str:
    """Extrae el texto del mensaje del diccionario de datos de Twilio."""
    return data.get("Body", "") or data.get("ButtonText", "")

def chat_with_gemini(message: str) -> str:
    """Genera una respuesta usando el modelo de Gemini."""
    if not model:
        return "Error: El modelo de IA no está disponible."
    if not message.strip():
        return "Por favor, envíame una pregunta para poder responder."
    try:
        response = model.generate_content(message)
        return response.text
    except Exception as e:
        logging.error(f"❌ Error al generar contenido con Gemini: {e}")
        return "Lo siento, ocurrió un error al procesar tu mensaje."

def split_message(text: str, chunk_size: int = 1500) -> list:
    """Divide un texto largo en trozos más pequeños."""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    while len(text) > 0:
        if len(text) > chunk_size:
            split_point = text.rfind(' ', 0, chunk_size)
            if split_point == -1:  # No se encontraron espacios, forzar corte
                split_point = chunk_size
        else:
            split_point = len(text)
            
        chunks.append(text[:split_point])
        text = text[split_point:].lstrip()
    return chunks

def process_and_reply(data: dict):
    """
    Función en segundo plano para procesar con Gemini y enviar la respuesta final.
    Si la respuesta es muy larga, la divide en varios mensajes.
    """
    from_number = data.get("From")
    incoming_msg = get_message_body(data)
    
    logging.info(f"Procesando en segundo plano para {from_number}...")
    
    reply_text = chat_with_gemini(incoming_msg)
    
    if twilio_client and from_number:
        try:
            # Dividir el mensaje en trozos si es necesario
            message_chunks = split_message(reply_text)
            
            for i, chunk in enumerate(message_chunks):
                # Añadir un indicador si hay múltiples partes (ej: 1/3)
                part_indicator = f"({i+1}/{len(message_chunks)}) " if len(message_chunks) > 1 else ""
                
                twilio_client.messages.create(
                    body=part_indicator + chunk,
                    from_=TWILIO_WHATSAPP_NUMBER,
                    to=from_number
                )
            
            logging.info(f"Respuesta final de {len(message_chunks)} parte(s) enviada a {from_number}")

        except Exception as e:
            logging.error(f"❌ Error enviando mensaje con la API de Twilio: {e}")

# --- Webhook Principal de la Aplicación ---
@app.route("/bot", methods=["POST"])
def whatsapp_webhook():
    """
    Recibe el mensaje de Twilio, responde inmediatamente y lanza el
    procesamiento de Gemini en segundo plano.
    """
    all_data = request.values.to_dict()
    logging.info(f"Datos recibidos de Twilio: {json.dumps(all_data)}")

    # Iniciar el procesamiento en un hilo separado
    thread = threading.Thread(target=process_and_reply, args=(all_data,))
    thread.start()

    # Responder a Twilio INMEDIATAMENTE para evitar el timeout
    twiml = MessagingResponse()
    twiml.message("Estoy pensando... 🤔")
    
    return Response(str(twiml), mimetype="application/xml")

# --- Iniciar la Aplicación ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
