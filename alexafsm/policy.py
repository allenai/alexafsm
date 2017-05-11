import importlib
import logging
import os
import json

from transitions import MachineError
from voicelabs import VoiceInsights

from alexafsm import response
from alexafsm.session_attributes import SessionAttributes
from alexafsm.states import States

logger = logging.getLogger(__name__)


class Policy:
    """
    Finite state machine that describes how to interact with user.
    Use a lightweight FSM library at https://github.com/tyarkoni/transitions
    """

    # "Abstract" class properties to be overwritten/set in inherited classes.
    states_cls = None

    def __init__(self, states: States, request: dict = None, with_graph: bool = False):
        self.states = states
        self.state = states.attributes.state
        state_names, transitions = type(states).get_states_transitions()
        machine_cls = \
            importlib.import_module('transitions.extensions').GraphMachine if with_graph else \
            importlib.import_module('transitions').Machine
        self.machine = machine_cls(
            model=self,
            states=state_names,
            initial=states.attributes.state,
            auto_transitions=False
        )

        for transition in transitions:
            self.machine.add_transition(**transition)

    @property
    def attributes(self) -> SessionAttributes:
        return self.states.attributes

    @classmethod
    def initialize(cls, request: dict = None, with_graph: bool = False):
        """Construct a policy in initial state"""
        states = cls.states_cls.from_request(request=request)
        return cls(states, request, with_graph)

    def get_current_state_response(self) -> response.Response:
        resp_function = getattr(type(self.states), self.state)
        return resp_function(self.states)

    def execute(self) -> response.Response:
        """Called when the user specifies an intent for this skill"""
        intent = self.attributes.intent
        previous_state = self.state

        # backup attributes in case of invalid FSM transition
        attributes_backup = self.attributes
        try:
            # trigger is added by transitions library
            self.trigger(intent)
            current_state = self.state
            logger.info(f"Changed from {previous_state} to {current_state} through {intent}")
            self.attributes.state = current_state
            return self.get_current_state_response()
        except MachineError as exception:
            logger.error(str(exception))
            # reset attributes
            self.states.attributes = attributes_backup
            return response.NOT_UNDERSTOOD

    def handle(self, request: dict, voice_insights: VoiceInsights = None,
               record_filename: str = None):
        """
        Method that handles Alexa post request in json format

        If record_dir is specified, this will record the request in the given directory for later
        playback for testing purposes
        """
        (req, session) = (request['request'], request['session'])
        logger.info(f"applicationId = {session['application']['applicationId']}")
        request_type = req['type']
        logger.info(
            f"{request_type}, requestId: {req['requestId']}, sessionId: {session['sessionId']}")

        if voice_insights:
            app_token = os.environ['VOICELABS_API_KEY']
            voice_insights.initialize(app_token, session)

        if request_type == 'LaunchRequest':
            resp = self.get_current_state_response()
        elif request_type == 'IntentRequest':
            intent = req['intent']
            self.states.attributes = type(self.states.attributes).from_request(request)
            self.state = self.attributes.state
            resp = self.execute()
            resp = resp._replace(session_attributes=self.states.attributes)
            if voice_insights:
                voice_insights.track(intent_name=intent['name'], intent_request=req,
                                     response=resp.to_json())
        elif request_type == 'SessionEndedRequest':
            resp = response.end(self.states.skill_name)
        else:
            raise Exception(f'Unknown request type {request_type}')

        if record_filename:
            with open(record_filename, 'a') as record_file:
                record_file.write(json.dumps([request, resp]) + '\n')

        return resp
