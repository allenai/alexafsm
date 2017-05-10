"""
Handle query to elasticsearch
"""

import string
from typing import List

from elasticsearch_dsl import Search

from alexafsm.test_helpers import recordable as rec
from elasticsearch_dsl.response import Response

from tests.skillsearch.skill_settings import SkillSettings
from tests.skillsearch.es_skill import Skill, INDEX
from tests.skillsearch.dynamodb import DynamoDB

es_search: Search = Search(index=INDEX).source(excludes=['html'])


def get_es_skills(query: str, top_n: int, category: str = None, keyphrase: str = None) -> (int, List[Skill]):
    """Return the total number of hits and the top_n skills"""
    result = get_es_results(query, category, keyphrase).to_dict()
    hits = result['hits']['hits']
    return result['hits']['total'], [Skill.from_es(h) for h in hits[:top_n]]


def recordable(func):
    def _get_record_dir():
        return SkillSettings().get_record_dir()

    def _is_playback():
        return SkillSettings().playback

    def _is_record():
        return SkillSettings().record

    return rec(_get_record_dir, _is_playback, _is_record)(func)


@recordable
def get_es_results(query: str, category: str, keyphrase: str) -> Response:
    results = _get_es_results(query, category, keyphrase, strict=True)
    if len(results.hits) == 0:
        # relax constraints a little
        return _get_es_results(query, category, keyphrase, strict=False)
    else:
        return results


def _get_es_results(query: str, category: str, keyphrase: str, strict: bool) -> Response:
    skill_search = es_search
    if category:
        skill_search = skill_search.query('match',
                                          category=string.capwords(category)
                                          .replace(' And ', ' & ')
                                          .replace('Movies & Tv', 'Movies & TV'))
    if keyphrase:
        skill_search = skill_search.query('match', keyphrases=keyphrase)
    if query:
        operator = 'and' if strict else 'or'
        skill_search = skill_search.query('multi_match',
                                          query=query,
                                          fields=['name', 'description', 'usages', 'keyphrases'],
                                          minimum_should_match='50%',
                                          operator=operator) \
            .highlight('description', order='score', pre_tags=['*'], post_tags=['*']) \
            .highlight('title', order='score', pre_tags=['*'], post_tags=['*']) \
            .highlight('usages', order='score', pre_tags=['*'], post_tags=['*'])

    return skill_search.execute()


@recordable
def get_user_info(user_id: str, request_id: str) -> dict:  # NOQA
    """
    Get information of user with user_id from dynamodb. request_id is simply there so that we can
    record different responses from dynamodb for the same user during playback
    """
    return DynamoDB().get_user_info(user_id)


@recordable
def register_new_user(user_id: str):
    DynamoDB().register_new_user(user_id)
