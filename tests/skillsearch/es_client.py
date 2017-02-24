"""
Handle query to elasticsearch
"""

import string
from elasticsearch_dsl import Search
from elasticsearch_dsl.result import Response
from tests.skillsearch.skill import Skill

es_search: Search = Search(index='replace_with_real_es_index').source(excludes=['html'])


def get_skill(skill_id: int) -> Skill:
    """
    Get the skill with a certain ID from Elasticsearch
    """
    # Search objects definitely have the execute() function
    return Skill.from_es_hit(es_search.query('ids', values=[skill_id]).execute()[0])


def get_es_results(category: str, query: str) -> Response:
    """
    Get back results from Elasticsearch
    """
    skill_search = es_search
    if category:
        skill_search = skill_search.query('match',
                                          category=string.capwords(category)
                                          .replace(' And ', ' & ')
                                          .replace('Movies & Tv', 'Movies & TV'))
    if query:
        skill_search = skill_search.query('multi_match',
                                          query=query,
                                          fields=['name', 'description', 'usages'],
                                          operator='and') \
            .highlight('description', order='score', pre_tags=['*'], post_tags=['*']) \
            .highlight('title', order='score', pre_tags=['*'], post_tags=['*']) \
            .highlight('usages', order='score', pre_tags=['*'], post_tags=['*'])

    return skill_search.execute()
