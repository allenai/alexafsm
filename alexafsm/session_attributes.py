INITIAL_STATE = 'initial'


class SessionAttributes:
    """
    Base class for all session attributes that keep track of the state of conversation
    """

    # "Abstract" class properties to be overwritten/set in inherited classes
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
            res = cls()
            res.slots = _slots_from_dict(slots_cls)
            return res

        intent = request['request']['intent']
        res = cls(**(request['session'].get('attributes', {})))
        res.intent = intent['name']
        res.set_slots(_slots_from_dict(slots_cls, intent.get('slots', {})))
        if res.state is None:
            res.state = INITIAL_STATE
        return res

    def json_to_alexa(self) -> dict:
        """
        When sending the payload to Alexa, do not send fields that are too big.
        """
        res = {k: v for k, v in self.__dict__.items() if k not in self.not_sent_fields and v}
        if 'slots' not in res:
            return res

        slots_kwargs = {k: v for k, v in res['slots']._asdict().items() if v}
        if slots_kwargs:
            res['slots'] = slots_kwargs
        else:
            res.pop('slots', None)
        return res

    def _get_val(self, slots, prop: str):
        """
        Get the value for this property from slots, if exists
        """
        val = getattr(slots, prop)
        if val:
            return val
        elif self.slots:
            return self.slots.get(prop, None)

        return None

    def set_slots(self, slots) -> None:
        """
        Update conversational context with information from query slots, if non_empty
        """
        self.slots = type(slots)(**{f: self._get_val(slots, f) for f in slots._fields})


def _value_of(some_dict: dict) -> str:
    return some_dict['value'] if some_dict and 'value' in some_dict else None


def _slots_kwargs(slots: dict) -> dict:
    return dict((k.lower(), _value_of(v)) for k, v in slots.items()) if slots else {}


def _slots_from_dict(slots_cls, slots: dict = None):
    """
    Given the definition for Slots that Amazon gives us, return the Slots tuple.
    """
    kwargs = _slots_kwargs(slots)
    return slots_cls(**{field: kwargs.get(field, None) for field in slots_cls._fields})
