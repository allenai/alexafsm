"""This demonstrates a Flask server that uses alexafsm-based skill search"""

import getopt
import json
import logging
import sys
from elasticsearch_dsl.connections import connections
from flask import Flask, request as flask_request
from livereload import Server

from voicelabs.voicelabs import VoiceInsights

from tests.skillsearch.policy import Policy
from tests.skillsearch.skill_settings import SkillSettings

app = Flask(__name__)

logger = logging.getLogger(__name__)
settings = SkillSettings()
port = 8888


@app.route('/', methods=['POST'])
def main():
    req = flask_request.json
    policy = Policy.initialize()
    return json.dumps(policy.handle(req, settings.vi)).encode('utf-8')


def _usage():
    print(f"Usage: alexa-listener.py"
          f" -s --es-server <ES cluster address [your.es_server]>"
          f" -i --use-voice-insight <use-voice-insight? (y/[N])>")


if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h:s:i",
                                   ["help", "es-server=", "use-voice-insight"])
    except getopt.GetoptError:
        _usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            _usage()
            sys.exit()
        if opt in ('-s', '--es-server'):
            settings.es_server = arg
        if opt in ('-i', '--voice-insight'):
            print("Activating VoiceInsight")
            settings.vi = VoiceInsights()

    log_file = f"alexa.log"
    print(f"Logging to {log_file} (append)")
    logging.basicConfig(format='%(asctime)s %(levelname)s %(name)s %(message)s',
                        filename=log_file,
                        filemode='a',
                        level=logging.INFO)
    print(f"Connecting to elasticsearch server on {settings.es_server}")
    connections.create_connection(hosts=[settings.es_server])
    print(f"Now listening for Alexa requests on port #: {port}")
    server = Server(app.wsgi_app)
    server.serve(host='0.0.0.0', port=port)
