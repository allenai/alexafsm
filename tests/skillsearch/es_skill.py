"""
Representation of the Skill type in Elasticsearch
"""

from elasticsearch_dsl import DocType, Text, Keyword, Double, Integer

INDEX = 'chat_prod'


class Skill(DocType):
    """
    Representation of a skill inside ES
    """
    name = Text(fields={'raw': Keyword()})
    creator = Keyword()
    category = Keyword()
    url = Text()
    description = Text()
    short_description = Text()
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
        index = INDEX

    @classmethod
    def set_index(cls, new_index: str):
        cls._doc_type.index = new_index

    @classmethod
    def get_index(cls):
        return cls._doc_type.index

    def to_json(self):
        """
        Provide a JSON representation of this Skill
        """
        doc = self.meta.to_dict()
        doc['_source'] = self.to_dict()
        return doc
