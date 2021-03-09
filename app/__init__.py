from flask import Flask
from config import Config

app = Flask(__name__)
app.config.from_object(Config)


def start_ngrok():
    from pyngrok import ngrok

    url = ngrok.connect(500)
    print('* Tunnel: ', url)


if app.config.get("ENV") == "development" and app.config["START_NGROK"]:
    start_ngrok()

from app import routes