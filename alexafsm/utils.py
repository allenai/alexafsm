import inspect
import json

from typing import Set

from alexafsm.policy import Policy
from alexafsm.session_attributes import INITIAL_STATE


def validate(policy: Policy, schema_file: str, ignore_intents: Set[str] = ()):
    """
    Check for inconsistencies in policy definition
    """
    schema = {}
    with open(schema_file, mode='r') as f:
        schema = json.loads(f.read())

    intents = [intent['intent'] for intent in schema['intents']
               if intent['intent'] not in ignore_intents]
    states = policy.machine.states
    events = []
    states_have_out_transitions = set()
    states_have_in_transitions = set()
    funcs = [func for func, _ in inspect.getmembers(type(policy), predicate=inspect.isfunction)]

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


def print_machine(policy: Policy):
    def _print_transition(tran):
        print(f"\t\t{tran.source} -> {tran.dest}", end='')
        if tran.prepare:
            print(f", prepare: {tran.prepare}", end='')
        if tran.conditions:
            print(f", conditions: {[cond.func for cond in tran.conditions]}", end='')
        print()

    print(f"Machine states:\n\t{', '.join(policy.machine.states)}")
    print("\nEvents and transitions:\n")
    for _, event in policy.machine.events.items():
        print(f"Event: {event.name}")

        for source, trans in event.transitions.items():
            print(f"\tSource: {source}")
            for transition in trans:
                _print_transition(transition)


def graph(policy_cls, png_file):
    policy = policy_cls.initialize(with_graph=True)
    policy.graph.draw(png_file, prog='dot')
