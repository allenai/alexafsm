from collections import namedtuple
from elasticsearch_dsl.result import Response
from alexafsm.session_attributes import SessionAttributes as ISessionAttributes
from tests.skillsearch.skill import Skill

Slots = namedtuple('Slots', ['query'])


class SessionAttributes(ISessionAttributes):
    slots_cls = Slots
    not_sent_fields = ['skill', 'result']

    def __init__(self,
                 intent: str = None,
                 slots: Slots = None,
                 state: str = None,
                 skill_id: str = None,
                 skill: Skill = None,
                 result: Response = None):
        super().__init__(intent, slots, state)

        # specific state/session info kept in the fields below
        self.skill_id = skill_id
        self.skill = skill
        self.result = result
