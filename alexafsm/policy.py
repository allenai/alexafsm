import inspect
import json
import logging
import os
from abc import abstractmethod
from functools import lru_cache

from typing import TypeVar, List, Set

from transitions import Machine, MachineError
from voicelabs import VoiceInsights

from alexafsm import response
from alexafsm.session_attributes import INITIAL_STATE, SessionAttributes
from alexafsm.states import States

logger = logging.getLogger(__name__)


class Policy:
    """
    Finite state machine that describes how to interact with user.
    Use a lightweight FSM library at https://github.com/tyarkoni/transitions
    """

    # "Abstract" class properties to be overwritten/set in inherited classes.
    states_cls = None

    def __init__(self, states: States):
        self.states = states
        self.state = states.attributes.state
        state_names, transitions = type(states).get_states_transitions()
        self.machine = Machine(
            model=self,
            states=state_names,
            initial=states.attributes.state,
            auto_transitions=False
        )

        for transition in transitions:
            self.machine.add_transition(**transition)

        self.add_extra_transitions()

    @abstractmethod
    def add_extra_transitions(self):
        """
        Add any extra transitions that are not encoded in decorators in States class
        """
        pass

    def add_conditional_transition(self,
                                   trigger: str,
                                   source: TypeVar('T', str, List),
                                   prepare: str,
                                   dest: str) -> None:
        """
        Add conditional transition with a condition function following a naming convention
        """
        self.machine.add_transition(
            trigger=trigger,
            source=source,
            dest=dest,
            prepare=prepare,
            conditions=Policy._condition_function(dest)
        )

    @staticmethod
    def _condition_function(dest):
        return f"m_{dest}"

    @classmethod
    def initialize(cls):
        """
        Construct a policy in initial state
        """
        states = cls.states_cls.from_request(request=None)
        return cls(states)

    @classmethod
    @lru_cache(maxsize=32)
    def get_policy(cls, session_id: str):
        """
        Manage a pool of policies that handles multiple sessions at the same time
        Simple override this method to use a different maxsize value
        """
        return cls.initialize()

    def update_with_request(self, request):
        """
        Update the session attributes with a request
        """
        self.states.attributes = type(self.states.attributes).from_request(request)
        self.state = self.attributes.state

    @property
    def attributes(self) -> SessionAttributes:
        return self.states.attributes

    def execute(self) -> response.Response:
        """
        Called when the user specifies an intent for this skill
        """
        intent = self.attributes.intent
        previous_state = self.state
        try:
            # trigger is added by transitions library
            self.trigger(intent)
            current_state = self.state
            logger.info(f"Changed states {previous_state} -> {current_state} "
                        f"through intent {intent}")
            self.attributes.state = current_state
            resp_function = getattr(type(self.states), current_state)
            return resp_function(self.states)
        except MachineError as exception:
            logger.error(str(exception))
            return response.NOT_UNDERSTOOD

    def handle(self, request: dict, voice_insights: VoiceInsights = None):
        """
        Method that handles Alexa post request in json format
        """
        (req, session) = (request['request'], request['session'])
        logger.info(f"applicationId = {session['application']['applicationId']}")
        request_type = req['type']
        logger.info(f"{request_type}, requestId: {req['requestId']}, sessionId: {session['sessionId']}")

        if voice_insights:
            app_token = os.environ['VOICELABS_API_KEY']
            voice_insights.initialize(app_token, session)

        if request_type == 'LaunchRequest':
            resp = response.welcome(self.states.skill_name, self.states.default_prompt)
        elif request_type == 'IntentRequest':
            intent = req['intent']
            self.update_with_request(request)
            logger.info(f"Policy id: {id(self)}, cache info: {Policy.get_policy.cache_info()}")
            resp = self.execute()
            resp = resp._replace(session_attributes=self.states.attributes)
            if voice_insights:
                voice_insights.track(intent_name=intent['name'], intent_request=req,
                                     response=resp.build_alexa_response())
        elif request_type == 'SessionEndedRequest':
            resp = response.end(self.states.skill_name)

        return resp

    @classmethod
    def validate(cls, schema_file: str, ignore_intents: Set[str] = ()):
        """
        Check for inconsistencies in policy definition
        """
        schema = {}
        with open(schema_file, mode='r') as f:
            schema = json.loads(f.read())

        intents = [intent['intent'] for intent in schema['intents']
                   if intent['intent'] not in ignore_intents]
        policy = cls.initialize()
        states = policy.machine.states
        events = []
        states_have_out_transitions = set()
        states_have_in_transitions = set()
        funcs = [func for func, _ in inspect.getmembers(cls, predicate=inspect.isfunction)]

        def _validate_transition(tran):
            assert tran.source in states, f"Invalid source state: {tran.source}!!"
            assert tran.dest in states, f"Invalid dest state: {tran.dest}!!"
            assert all(prep in funcs for prep in tran.prepare), \
                f"Invalid prepare function: {tran.prepare}!!"
            assert all(cond.func in funcs for cond in tran.conditions), \
                f"Invalid conditions function: {tran.conditions}!!"

            states_have_in_transitions.add(tran.dest)
            states_have_out_transitions.add(tran.source)

        for _, event in policy.machine.events.items():
            assert event.name in intents, f"Invalid event/trigger: {event.name}!"
            events.append(event.name)

            for source, trans in event.transitions.items():
                for transition in trans:
                    assert source in states, f"Invalid source state: {source}!!"
                    _validate_transition(transition)

        intent_diff = set(intents) - set(events)
        assert not intent_diff, f"Some intents are not handled: {intent_diff}"

        in_diff = set(states) - states_have_in_transitions - {INITIAL_STATE}
        out_diff = set(states) - states_have_out_transitions - set('exiting')

        assert not in_diff, f"Some states have no inbound transitions: {in_diff}"
        assert not out_diff, f"Some states have no outbound transitions: {out_diff}"
