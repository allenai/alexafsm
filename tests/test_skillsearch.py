from tests.skillsearch.policy import Policy


def test_policy():
    Policy.validate(schema_file='./tests/skillsearch/alexa-schema.json')
