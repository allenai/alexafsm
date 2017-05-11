import logging

from alexafsm.policy import Policy as PolicyBase

from tests.skillsearch.clients import get_es_skills, get_user_info, register_new_user
from tests.skillsearch.states import States, MAX_SKILLS

logger = logging.getLogger(__name__)


class Policy(PolicyBase):
    def __init__(self, states: States, request: dict, with_graph: bool = False):
        super().__init__(states, request, with_graph)

        if request:
            user_id = request['session']['user']['userId']
            user_info = get_user_info(user_id, request['request']['requestId'])
            self.states.attributes.first_time = not bool(user_info)
            if self.attributes.first_time:
                register_new_user(user_id)

    states_cls = States

    def _valid_search(self) -> bool:
        if not self.attributes.slots.query:
            return False

        current_query = self.attributes.slots.query
        if current_query == 'find':
            self.states.attributes.slots = self.states.attributes.slots._replace(query='')
        elif current_query.startswith('find '):
            self.states.attributes.slots = \
                self.states.attributes.slots._replace(query=current_query[5:])

        return self.attributes.slots.query and not self.m_searching_for_exit()

    def m_searching_for_exit(self) -> bool:
        # sometimes Amazon misinterprets "exit" as a search intent for the term "exit" instead of
        # the exit intent. Let's take care of that on behalf of the user
        return self.attributes.slots.query == 'exit'

    def m_search(self) -> None:
        """Search for skills matching user's query"""
        attributes = self.states.attributes
        if attributes.searched:
            return  # don't search more than once

        if not self._valid_search():
            return
        self.states.attributes.query = attributes.slots.query
        es_query = self.states.attributes.query
        if self.states.attributes.query == 'skills':
            es_query = 'search for skills'  # get our own skill

        number_of_hits, skills = get_es_skills(es_query, MAX_SKILLS)
        logger.info(f"Searching for {self.attributes.query}, got {number_of_hits} hits.")
        attributes.skills = skills
        attributes.number_of_hits = number_of_hits
        attributes.skill_cursor = 0 if skills else None
        attributes.searched = True
        attributes.first_time_presenting_results = True

    def m_no_query_search(self) -> bool:
        """Amazon sent us a search intent without a query
        or maybe the user said "I want to find ..." and took too long to finish"""
        return not self.attributes.slots.query or self.attributes.slots.query == 'find'

    def m_no_result(self) -> bool:
        return self.attributes.query and not self.m_has_result()

    def m_has_result(self) -> bool:
        return self.attributes.query is not None and self.attributes.skills is not None and len(
            self.attributes.skills) > 0

    def m_has_result_and_query(self) -> bool:
        return self.m_has_result() and not self.m_no_query_search()

    def m_has_nth(self) -> bool:
        return self.m_has_result() and \
            len(self.attributes.skills) > self.attributes.nth_as_index >= 0

    def m_set_nth(self) -> None:
        self.attributes.skill_cursor = self.attributes.nth_as_index
        self.attributes.first_time_presenting_results = False

    def m_set_next(self) -> None:
        """Go to next skill"""
        self.attributes.skill_cursor += 1
        self.attributes.first_time_presenting_results = False

    def m_has_next(self) -> bool:
        return self.m_has_result() and \
            self.attributes.skill_cursor + 1 < len(self.attributes.skills)

    def m_set_previous(self) -> None:
        """Go to previous skill"""
        self.attributes.skill_cursor -= 1
        self.attributes.first_time_presenting_results = False

    def m_has_previous(self) -> bool:
        return self.m_has_result() and self.attributes.skill_cursor > 0
