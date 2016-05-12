import logging
import os
import re

from flask import Flask, Response, request
from kik import Configuration, KikApi
from kik.messages import TextMessage, messages_from_json
from yahoo_finance import Share

BOT_USERNAME = os.environ.get('BOT_USERNAME', '')
BOT_API_KEY = os.environ.get('BOT_API_KEY', '')
BOT_WEBHOOK = os.environ.get('BOT_WEBHOOK', '')

kik = KikApi(BOT_USERNAME, BOT_API_KEY)
kik.set_configuration(Configuration(webhook=BOT_WEBHOOK))

app = Flask(__name__)

DEBUG = True


def send_text(user, chat_id, body):
    """Send text."""
    kik.send_messages([TextMessage(to=user, chat_id=chat_id, body=body)])


@app.route('/', methods=['GET'])
def hello():
    """Hello world."""
    return 'Hello world'


@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook."""
    if not kik.verify_signature(request.headers.get('X-Kik-Signature'), request.get_data()):
        return Response(status=403)

    messages = messages_from_json(request.json['messages'])

    for message in messages:
        if isinstance(message, TextMessage):
            logging.info(message)

            if '$' not in message.body:
                text = 'Hi {}! For live stock quotes type "$" followed by a ticker symbol.'.format(message.from_user)
                send_text(message.from_user, message.chat_id, text)
                text = 'For example, type "$aapl" for Apple.'
                send_text(message.from_user, message.chat_id, text)
            else:
                send_text(message.from_user, message.chat_id, 'Looking up...')
                for symbol in re.findall(r'\$\w(?:\w)*(?:\.\w+)?', message.body):
                    yahoo = Share(symbol[1:])
                    if yahoo.get_price():
                        text = 'Price of {} is {}'.format(symbol[1:], yahoo.get_price())
                        send_text(message.from_user, message.chat_id, text)
                    else:
                        text = 'We couldn\'t find a ticker with that name.'
                        send_text(message.from_user, message.chat_id, text)

    return Response(status=200)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=DEBUG)
