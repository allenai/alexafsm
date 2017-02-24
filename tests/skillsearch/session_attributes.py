"""
SessionAttributes for V1
"""
from collections import namedtuple
from elasticsearch_dsl.result import Response
from alexafsm.session_attributes import SessionAttributes as ISessionAttributes
from tests.skillsearch.skill import Skill

Slots = namedtuple('Slots', ['query'])


class SessionAttributes(ISessionAttributes):
    """
    Session attributes store information about the context of a conversation so far
    """

    not_sent_fields = ['skill', 'result']
    slots_cls = Slots

    def __init__(self,  # pylint: disable=too-many-arguments
                 intent: str = None,
                 slots: Slots = None,
                 state: str = None,
                 skill_id: str = None,
                 skill: Skill = None,
                 result: Response = None):
        super().__init__(intent, slots, state)
        self.skill_id = skill_id
        self.skill = skill
        self.result = result
