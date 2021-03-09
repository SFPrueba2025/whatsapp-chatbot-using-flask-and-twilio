from app import app
from flask import request
from twilio.twiml.message_response import MessageResponse
import requests


@app.route('/bot', methods=['POST'])
def bot():
    incoming_msg = request.values.get('Body', '').lower()
    resp = MessageResponse()
    msg = resp.message()
    responded = False
    if 'quote' in incoming_msg:
        r = requests.get('https://api.quotable.io/random')
        if r.status_code == 200:
            data = r.json()
            quote = f'{data["content"] - {data["author"]}}'
        else:
            quote = 'I could not retrieve a quote at this time, sorry.'
        msg.body(quote)
        responded = True
    if 'cat' in incoming_msg:
        msg.media('https://cataas.com/cat')
        responded = True
    if not responded:
        msg.body('Apologies, I do not understand what you really asked.')
    return str(resp)
