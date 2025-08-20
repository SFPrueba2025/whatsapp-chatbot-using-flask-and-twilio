import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import google.generativeai as genai

# Configurar la API Key de Gemini desde las variables de entorno de Render
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Seleccionamos el modelo de Gemini
model = genai.GenerativeModel("gemini-1.5-flash")

# Inicializar la app Flask
app = Flask(__name__)

# Función para conversar con Gemini
def chat_with_gemini(message: str) -> str:
    try:
        response = model.generate_content(message)
        return response.text
    except Exception as e:
        return f"Ocurrió un error al procesar tu mensaje: {e}"

# Ruta que recibe los mensajes de WhatsApp vía Twilio
@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    # Mensaje del usuario en WhatsApp
    user_message = request.values.get("Body", "") or ""
    
    # Obtener respuesta de Gemini
    reply_text = chat_with_gemini(user_message)
    
    # Crear respuesta para Twilio
    twiml = MessagingResponse()
    twiml.message(reply_text)
    
    return str(twiml)

# Para pruebas locales (no necesario en Render, porque usará gunicorn)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
