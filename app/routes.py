from app import app
from flask import request, render_template
from twilio.twiml.messaging_response import MessagingResponse
import openai
import os

# Usa tu clave API de OpenAI desde las variables de entorno
openai.api_key = os.getenv("OPENAI_API_KEY")

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

    # Si no coincide con 'quote' o 'cat', responde con GPT
    if not responded:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": incoming_msg}
                ]
            )
            reply = response['choices'][0]['message']['content'].strip()
            msg.body(reply)
        except Exception as e:
            msg.body(f"Sorry, an error occurred: {str(e)}")

    return str(resp)
