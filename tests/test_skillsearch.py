from alexafsm.utils import validate
from tests.skillsearch.policy import Policy


def test_policy():
    policy = Policy.initialize()
    validate(policy, schema_file='./tests/skillsearch/alexa-schema.json')
