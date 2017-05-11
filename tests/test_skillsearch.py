import pytest
import json

from tests.skillsearch.policy import Policy
from alexafsm.utils import validate, events_states_transitions, unused_events_states_transitions
from alexafsm.test_helpers import get_requests_responses
from tests.skillsearch.skill_settings import SkillSettings


def test_validate_policy():
    policy = Policy.initialize()
    validate(policy=policy,
             schema_file='./tests/skillsearch/speech/alexa-schema.json',
             ignore_intents={'DontUnderstand'})

    policy_states = policy.machine.states
    policy_stop_states = \
        policy.states.EXIT_ON_STOP_STATES + \
        policy.states.CONTINUE_ON_STOP_STATES + \
        policy.states.PROMPT_ON_STOP_STATES
    # "exiting" state does not need any outgoing transitions
    missing = set(policy_states) - set(policy_stop_states) - {'exiting'}
    assert not missing, f'Some states do not handle STOP/CANCEL intents: {missing}'


def the_test_playback(measure_coverage: bool = False):
    """Play back recorded responses to check that the system is still behaving the same
    Change to test_playback to actually run this test once a recording is made."""
    policy = Policy.initialize()
    SkillSettings().playback = True
    record_file = SkillSettings().get_record_file()
    for request, expected_response in get_requests_responses(record_file):
        actual_response = json.loads(json.dumps(policy.handle(request)))
        assert expected_response == actual_response

    if measure_coverage:
        policy = SkillSettings().get_policy()
        all_events, all_states, all_transitions = events_states_transitions(policy)
        unused_events, unused_states, unused_transitions = \
            unused_events_states_transitions(policy, get_requests_responses(record_file))

        print(f"Summary: "
              f"{len(unused_events)}/{len(all_events)} unused events, "
              f"{len(unused_states)}/{len(all_states)} unused states, "
              f"{len(unused_transitions)}/{len(all_transitions)} unused transitions ")
        print(f"Unused events: {unused_events}")
        print(f"Unused states: {unused_states}")
        print(f"Unused transitions: {unused_transitions}")


if __name__ == '__main__':
    pytest.main([__file__])
