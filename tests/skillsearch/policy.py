"""
Conversational logic
"""

import logging
from typing import TypeVar, List
from transitions import MachineError

from alexafsm import response
from alexafsm.policy import Policy as IPolicy
from tests.skillsearch.es_client import get_es_results, get_skill
from tests.skillsearch.intent import NEW_SEARCH
from tests.skillsearch.skill import Skill
from tests.skillsearch.states import States

logger = logging.getLogger(__name__)


class Policy(IPolicy):
    """
    Finite state machine that describes how to interact with user
    """

    states_cls = States

    def add_extra_transitions(self):
        self._generate_search_transitions(trigger=NEW_SEARCH, source='no_results_search')
        self._generate_search_transitions(trigger=NEW_SEARCH, source='*')

    def _generate_search_transitions(self,
                                     trigger: str,
                                     source: TypeVar('T', str, List),
                                     prepare: str = 'm_search') -> None:
        """
        Generate conditional search transitions. The resulting state of the conversation will
        depend on how many results there are
        """
        for dest in ['no_results_search',
                     'one_result_search',
                     'many_results_search']:
            self.add_conditional_transition(trigger=trigger, source=source, prepare=prepare, dest=dest)

    def m_search(self) -> None:
        """
        Tell user the highest-rated skill in a category
        """
        attributes = self.states.attributes
        if attributes.result:
            return  # don't search more than once

        slots = attributes.slots
        logger.info(f"Searching for {slots.query} ... ")
        result = get_es_results(None, slots.query)
        logger.info(f"Got {result.hits.total} hits.")
        if result.hits.total > 0:
            top_res = result[0]
            attributes.skill_id = top_res.meta.id
            attributes.skill = Skill.from_es_hit(top_res)

        attributes.result = result

    def m_retrieve_skill_with_id(self) -> None:
        """
        Retrieve a skill from ES given its id.
        """
        self.states.attributes.skill = get_skill(
            self.states.attributes.skill_id)

    def m_no_results_search(self) -> bool:
        """
        See if there are no results from the search query
        """
        return self.states.attributes.result.hits.total == 0

    def m_one_result_search(self) -> bool:
        """
        See if there is exactly one result from the search query
        """
        return self.states.attributes.result.hits.total == 1

    def m_many_results_search(self) -> bool:
        """
        See if there is exactly one result from the search query
        """
        return self.states.attributes.result.hits.total > 1

    def execute(self) -> response.Response:
        """
        Called when the user specifies an intent for this skill
        """
        states = self.states
        attributes = states.attributes

        previous_state = self.state
        try:
            # trigger is added by transitions library
            self.trigger(attributes.intent)
            current_state = self.state
            logger.info(f"Changed states {previous_state} -> {current_state} "
                        f"through intent {attributes.intent}")
            states.attributes.state = current_state
            resp_function = getattr(type(self.states), current_state)
            return resp_function(states)
        except MachineError as exception:
            logger.error(str(exception))
            return response.NOT_UNDERSTOOD
