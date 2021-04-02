from app import app
from flask import request, render_template, url_for, request
from twilio.twiml.messaging_response import MessagingResponse
import requests
import folium


def get_traffic_data(lat, lon):
    params = {'point': f'{lat},{lon}', 'unit': 'mph', 'thickness': 14, 'key': os.environ['TOMTOM_API_KEY']}
    base_url = 'https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json'
    data = requests.get(base_url, params=params).json()
    return data


def create_reply(lat, lon):
    data = get_traffic_data(lat, lon)

    road_types = {'FRC0': 'Motorway', 'FRC1': 'Major road', 'FRC2': 'Other major road', 'FRC3': 'Secondary road',
                  'FRC4': 'Local connecting road', 'FRC5': 'Local road of high importance', 'FRC6': 'Local road'}

    if data['flowSegmentData']['roadClosure']:
        reply = 'Unfortunately this road is closed!'
    else:
        reply = (f"Your nearest road is classified as a _{road_types[data['flowSegmentData']['frc']]}_.  "
                 f"The current average speed is *{data['flowSegmentData']['currentSpeed']} mph* and "
                 f"would take *{data['flowSegmentData']['currentTravelTime']} seconds* to pass this section of road.  "
                 f"With no traffic, the speed would be *{data['flowSegmentData']['freeFlowSpeed']} mph* and would "
                 f"take *{data['flowSegmentData']['freeFlowTravelTime']} seconds*.")
    return reply


@app.route('/map')
def create_map():
    lat = request.args.get('lat')
    lon = request.args.get('lon')

    data = get_traffic_data(lat, lon)

    points = [(i['latitude'], i['longitude']) for i in data['flowSegmentData']['coordinates']['coordinate']]

    m = folium.Map(location=(lat, lon), zoom_start=15)
    folium.PolyLine(points, color='green', weight=10).add_to(m)

    return m._repr_html_()


@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html', title='Home')


@app.route('/bot', methods=['POST'])
def bot():
    incoming_msg = request.values.get('Body', '').lower()
    resp = MessagingResponse()
    msg = resp.message()
    responded = False
    if 'quote' in incoming_msg:
        r = requests.get('https://api.quotable.io/random')
        if r.status_code == 200:
            data = r.json()
            quote = f'{data["content"]} ({data["author"]})'
        else:
            quote = 'I could not retrieve a quote at this time, sorry.'
        msg.body(quote)
        responded = True
    if 'cat' in incoming_msg:
        msg.media('https://cataas.com/cat')
        responded = True
    if 'Latitude' in request.values.get() and "Longitude" in request.values.keys():
        lat = request.values.get('Latitude')
        lon = request.values.get('Longitude')

        reply = create_reply(lat, lon)
        url = f'{request.url_root}map?lat={lat}&lon={lon}'
        msg.body(f'{reply}\n\nCheck out the interactive map here:\n{url}')
        responded = True

    if not responded:
        msg.body('Apologies, I do not understand what you really asked.')

    return str(resp)
