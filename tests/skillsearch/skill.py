"""
Representation of the Skill type in Elasticsearch
"""

# Double and Integer are dynamically generated, so static analysis will not detect them
# see http://stackoverflow.com/a/33766518/257583
from elasticsearch_dsl import DocType, Text, Keyword, Double, Integer

CATEGORIES = (
    'Education and Reference',
    'Utilities',
    'Travel and Transportation',
    'Games, Trivia and Accessories',
    'Productivity',
    'Weather',
    'Movies and TV',
    'Connected Car',
    'Music and Audio',
    'Novelty and Humor',
    'Sports',
    'Lifestyle',
    'News',
    'Health and Fitness',
    'Smart Home',
    'Social',
    'Communication',
    'Shopping',
    'Business and Finance',
    'Local',
    'Food and Drink',
)

# For use in Alexa card
CARD_CATEGORIES = "\n  - ".join(CATEGORIES)


class Skill(DocType):
    """
    Representation of a skill inside ES
    """
    name = Text(fields={'raw': Keyword()})
    creator = Keyword()
    category = Keyword()
    url = Text()
    description = Text()
    avg_rating = Double()
    num_ratings = Integer()
    html = Text()
    usages = Text(fields={'raw': Keyword()})
    image_url = Text()
    keyphrases = Text(fields={'raw': Keyword()})

    class Meta:
        """
        Metadata about where this data type resides
        """
        index = 'es_index'

    @classmethod
    def from_es_hit(cls, es_hit):
        """
        Convert an search hit into a Skill.
        """
        return Skill(meta=es_hit.meta.to_dict(), **es_hit.to_dict())
