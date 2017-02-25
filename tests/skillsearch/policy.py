import logging

from elasticsearch_dsl import Search
from alexafsm.policy import Policy as IPolicy
from tests.skillsearch.skill import Skill
from tests.skillsearch.states import States

logger = logging.getLogger(__name__)
SEARCH = 'Search'

es_search: Search = Search(index='replace_with_real_es_index').source(excludes=['html'])


class Policy(IPolicy):

    states_cls = States

    def add_extra_transitions(self):
        for dest in ['no_results', 'one_result', 'many_results']:
            self.add_conditional_transition(
                trigger=SEARCH,
                source='*',
                prepare='m_search',
                dest=dest)

    def m_search(self) -> None:
        attributes = self.attributes
        if attributes.result:
            return  # don't search more than once

        result = es_search.query('multi_match',
                                 query=attributes.slots.query,
                                 fields=['name', 'description', 'usages'],
                                 operator='and') \
            .highlight('description', order='score', pre_tags=['*'], post_tags=['*']) \
            .highlight('title', order='score', pre_tags=['*'], post_tags=['*']) \
            .highlight('usages', order='score', pre_tags=['*'], post_tags=['*']).execute()
        attributes.result = result
        if not self.m_no_results():
            top_res = result[0]
            attributes.skill_id = top_res.meta.id
            attributes.skill = Skill.from_es_hit(top_res)

    def m_retrieve_skill_with_id(self) -> None:
        self.attributes.skill = Skill.from_es_hit(
            es_search.query('ids', values=[self.attributes.skill_id]).execute()[0])

    def _number_of_hits(self):
        return self.attributes.result.hits.total

    def m_no_results(self) -> bool:
        return self._number_of_hits == 0

    def m_one_result(self) -> bool:
        return self._number_of_hits == 1

    def m_many_results(self) -> bool:
        return self._number_of_hits > 1
