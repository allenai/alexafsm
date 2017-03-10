from collections import namedtuple

from alexafsm.session_attributes import SessionAttributes as ISessionAttributes, INITIAL_STATE

Slots = namedtuple('Slots', ['love', 'money'])


class SessionAttributes(ISessionAttributes):
    slots_cls = Slots
    not_sent_fields = ['intent']


request = {
    'session': {
        'attributes': {
            'state': 'blissful',
            'slots': ['loving', 'null']
        },
    },
    'request': {
        'type': 'IntentRequest',
        'intent': {
            'name': 'Search',
            'slots': {
                'Love': {
                    'name': 'Love'
                },
                'Money': {
                    'name': 'Money',
                    'value': 'lots'
                }
            }
        }
    }
}


def test_none_request():
    s = SessionAttributes.from_request(None)
    assert s.intent is None
    assert s.state == INITIAL_STATE
    assert s.slots == Slots(love=None, money=None)


def test_request():
    s = SessionAttributes.from_request(request)
    assert s.intent == 'Search'
    assert s.slots == Slots(love='loving', money='lots')
    assert s.state == 'blissful'


def test_json_to_alexa():
    s = SessionAttributes.from_request(request)
    js = s.to_json()
    assert 'intent' not in js
    assert js['state'] == 'blissful'
    assert js['slots'] == Slots(love='loving', money='lots')


def test_json_to_alexa_and_back():
    import json
    s = SessionAttributes.from_request(request)
    js = json.dumps(s.to_json())
    request2 = {
        'request': {'intent': {'name': 'foo'}},
        'session': {'attributes': json.loads(js)}
    }

    s2 = SessionAttributes.from_request(request2)
    assert s2.intent == 'foo'
    assert s2.state == s.state
    assert s2.slots == s.slots


def test_empty_attributes():
    import json

    empty_attrs_request = {
        'session': {
            'attributes': {},
        },
        'request': {
            'type': 'IntentRequest',
            'intent': {
                'name': 'Search',
                'slots': {
                    'Love': {
                        'name': 'Love'
                    },
                    'Money': {
                        'name': 'Money',
                        'value': 'lots'
                    }
                }
            }
        }
    }

    s = SessionAttributes.from_request(empty_attrs_request)
    js = json.dumps(s.to_json())
    request2 = {
        'request': {'intent': {'name': 'foo'}},
        'session': {'attributes': json.loads(js)}
    }

    s2 = SessionAttributes.from_request(request2)
    assert s2.intent == 'foo'
    assert s2.state == s.state
    assert s2.slots == s.slots
