from app import app
from flask import request, render_template
from twilio.twiml.messaging_response import MessagingResponse
import openai
import os

# Configura la clave de API de OpenAI
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
    
    # Respuesta fija para 'quote' (mantener si quieres esa opción)
    if 'quote' in incoming_msg:
        r = requests.get('https://api.quotable.io/random')
        if r.status_code == 200:
            data = r.json()
            quote = f'{data["content"]} ({data["author"]})'
        else:
            quote = 'I could not retrieve a quote at this time, sorry.'
        msg.body(quote)
        responded = True

    # Respuesta fija para 'cat' (mantener si quieres esa opción)
    elif 'cat' in incoming_msg:
        msg.media('https://cataas.com/cat')
        responded = True

    # Si no se entiende el mensaje, se usa OpenAI
    if not responded:
        try:
            # Solicita una respuesta a OpenAI
            response = openai.Completion.create(
                model="text-davinci-003",  # O usa otro modelo que prefieras
                prompt=incoming_msg,
                max_tokens=150,
                temperature=0.7
            )
            reply = response.choices[0].text.strip()
            msg.body(reply)
        except Exception as e:
            msg.body(f"Sorry, I encountered an error: {str(e)}")
    
    return str(resp)
