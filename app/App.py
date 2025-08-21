import os
from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
import google.generativeai as genai
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)

# Configurar la API Key de Gemini desde las variables de entorno de Render
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("La variable de entorno GEMINI_API_KEY no está definida")
genai.configure(api_key=API_KEY)

# Seleccionamos el modelo de Gemini (chat)
MODEL_NAME = "gemini-1.5-flash"

# Inicializar la app Flask
app = Flask(__name__)

# Función para conversar con Gemini
def chat_with_gemini(message: str) -> str:
    if not message.strip():
        return "Por favor, envía un mensaje válido."
    try:
        response = genai.chat(
            model=MODEL_NAME,
            messages=[{"author": "user", "content": message}],
            max_output_tokens=300
        )
        return response.last or "Gemini no pudo generar una respuesta."
    except Exception as e:
        logging.error(f"Error Gemini: {e}")
        return "Ocurrió un error al procesar tu mensaje. Intenta nuevamente más tarde."

# Función principal del webhook de WhatsApp
@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    incoming_msg = request.values.get("Body", "").strip()
    media_count = int(request.values.get("NumMedia", 0))
    
    logging.info(f"Mensaje recibido: {incoming_msg}, Media count: {media_count}")
    
    twiml = MessagingResponse()
    
    # Si hay medios (imagen, audio, sticker)
    if media_count > 0:
        media_urls = [request.values.get(f"MediaUrl{i}") for i in range(media_count)]
        twiml.message(f"Recibí {media_count} archivo(s). Procesando...")
        logging.info(f"URLs de media: {media_urls}")
        # Aquí podrías integrar reconocimiento de imagen, audio, etc.
    else:
        # Procesar solo texto con Gemini
        reply_text = chat_with_gemini(incoming_msg)
        twiml.message(reply_text)
        logging.info(f"Respuesta enviada: {reply_text}")
    
    return Response(str(twiml), mimetype="application/xml")

# Para pruebas locales
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
