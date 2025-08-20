import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import google.generativeai as genai

# Configurar la API Key de Gemini desde las variables de entorno de Render
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Seleccionamos el modelo de Gemini (chat)
MODEL_NAME = "gemini-1.5-flash"

# Inicializar la app Flask
app = Flask(__name__)

# Función para conversar con Gemini
def chat_with_gemini(message: str) -> str:
    try:
        response = genai.chat(
            model=MODEL_NAME,
            messages=[{"author": "user", "content": message}]
        )
        # Gemini devuelve la respuesta principal en 'response.last'
        return response.last
    except Exception as e:
        return f"Ocurrió un error al procesar tu mensaje: {e}"

# Ruta que recibe los mensajes de WhatsApp vía Twilio
@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    user_message = request.values.get("Body", "") or ""
    reply_text = chat_with_gemini(user_message)
    
    twiml = MessagingResponse()
    twiml.message(reply_text)
    return str(twiml)

# Para pruebas locales
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
