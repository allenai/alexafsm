"""
Base class for States
"""
import inspect

from alexafsm.session_attributes import SessionAttributes, INITIAL_STATE

TRANSITIONS = 'transitions'


def with_transitions(*transitions):
    """
    Add the provided in-bound transitions to the state
    """

    def decorate(state):
        def transition_enabled_state(*args):
            return state(*args)

        full_transitions = []
        for transition in transitions:
            if 'dest' in transition:
                assert 'source' not in transition, f"Expected no source to be specified:" \
                                                   f" {transition['source']}"
                transition['source'] = state.__name__
            else:
                assert 'dest' not in transition, f"Expected no dest to be specified: " \
                                                 f"{transition['dest']}"
                transition['dest'] = state.__name__

            full_transitions.append(transition)
        setattr(transition_enabled_state, TRANSITIONS, full_transitions)
        return transition_enabled_state

    return decorate


class States:
    """
    A collection of static methods that generate responses based on the current session attributes.
    Each method corresponds to a state of the FSM.
    """

    # "Abstract" class property to be overwritten/set in inherited classes.
    session_attributes_cls = None
    skill_name = "Allen A.I."
    default_prompt = "How can I help?"

    def __init__(self, attributes: SessionAttributes):
        self.attributes = attributes

    @classmethod
    def from_request(cls, request):
        """
        Factory constructor from intent and session.
        """
        attributes = cls.session_attributes_cls.from_request(request)
        return cls(attributes)

    @classmethod
    def get_states_transitions(cls):
        """
        Get all states & transitions specified in the states via with_transitions decoration.
        """
        states = []
        transitions = []
        for state, method in inspect.getmembers(cls, predicate=inspect.isfunction):
            if state != '__init__':
                states.append(state)
                transitions += getattr(method, TRANSITIONS, [])
        states.append(INITIAL_STATE)
        return states, transitions
