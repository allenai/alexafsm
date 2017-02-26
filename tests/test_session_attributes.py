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
            'slots': {
                'love': 'loving'
            }
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
    js = s.json_to_alexa()
    assert 'intent' not in js
    assert js['state'] == 'blissful'
    assert js['slots'] == {'love': 'loving', 'money': 'lots'}
