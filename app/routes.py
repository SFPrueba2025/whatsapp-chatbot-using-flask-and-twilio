from app import app
from flask import request, render_template
from twilio.twiml.messaging_response import MessagingResponse
import os
import requests
import google.generativeai as genai

# Configurar Gemini con tu API Key desde variables de entorno
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")


# Función para responder con Gemini
def chat_with_gemini(message: str) -> str:
    try:
        response = model.generate_content(message)
        return response.text
    except Exception as e:
        return f"Sorry, an error occurred: {str(e)}"


@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html', title='Home')


@app.route('/bot', methods=['POST'])
def bot():
    incoming_msg = request.values.get('Body', '').strip()
    resp = MessagingResponse()
    msg = resp.message()
    responded = False

    # Respuesta para 'quote'
    if 'quote' in incoming_msg.lower():
        r = requests.get('https://api.quotable.io/random')
        if r.status_code == 200:
            data = r.json()
            quote = f'{data["content"]} ({data["author"]})'
        else:
            quote = 'I could not retrieve a quote at this time, sorry.'
        msg.body(quote)
        responded = True

    # Respuesta para 'cat'
    elif 'cat' in incoming_msg.lower():
        msg.media('https://cataas.com/cat')
        responded = True

    # Si no coincide con 'quote' o 'cat', responde con Gemini
    if not responded:
        reply = chat_with_gemini(incoming_msg)
        msg.body(reply)

    return str(resp)
