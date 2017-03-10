INITIAL_STATE = 'initial'


class SessionAttributes:
    """
    Base class for all session attributes that keep track of the state of conversation
    """

    # "Abstract" class properties to be overridden/set in inherited classes
    # Inherited classes should override this like so:
    # Slots = namedtuple('Slots', ['foo', 'bar'])
    #
    # slots_cls = Slots
    slots_cls = None

    # List of (big) fields we don't want to send back to Alexa
    not_sent_fields = []

    def __init__(self, intent: str = None, slots=None, state: str = INITIAL_STATE):
        self.intent = intent
        self.slots = slots
        self.state = state

    @classmethod
    def from_request(cls, request: dict) -> 'SessionAttributes':
        """
        Construct session attributes object from request
        """
        slots_cls = cls.slots_cls
        if not request:
            return cls(slots=_slots_from_dict(slots_cls, slots=None))

        intent = request['request']['intent']
        res = cls(**(request['session'].get('attributes', {})))
        res.intent = intent['name']
        if res.state is None:
            res.state = INITIAL_STATE

        # namedtuple deserialization from list of values
        old_slots = slots_cls._make(res.slots)

        # Construct new slots from the request
        new_slots = _slots_from_dict(slots_cls, intent.get('slots'))

        # Update the slots attribute, using new slot values when exist
        def _extract(f):
            v = getattr(new_slots, f)
            return v if v else getattr(old_slots, f)

        res.slots = slots_cls(**{f: _extract(f) for f in old_slots._fields})

        return res

    def to_json(self) -> dict:
        """
        When sending the payload to Alexa, do not send fields that are too big.
        """
        return {k: v for k, v in self.__dict__.items() if k not in self.not_sent_fields and v}


def _slots_from_dict(slots_cls, slots: dict):
    """
    Given the definition for Slots that Amazon gives us, return the Slots tuple
    >>> from collections import namedtuple
    >>> Slots = namedtuple('Slots', ['love', 'money'])
    >>> slots = {'Love': {'name': 'Love'}, 'Money': {'name': 'Money', 'value': 'lots'}}
    >>> _slots_from_dict(Slots, slots)
    Slots(love=None, money='lots')
    >>> _slots_from_dict(Slots, None)
    Slots(love=None, money=None)
    >>> _slots_from_dict(Slots, {})
    Slots(love=None, money=None)
    """

    def _value_of(some_dict: dict) -> str:
        return some_dict['value'] if some_dict and 'value' in some_dict else None

    # Construct a dict with lower-cased slotnames as keys and values as values
    kwargs = dict((k.lower(), _value_of(v)) for k, v in slots.items()) if slots else {}

    # Construct a not-None namedtuple Slot object where attributes can be None
    return slots_cls(**{field: kwargs.get(field, None) for field in slots_cls._fields})
