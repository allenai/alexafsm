"""
Settings for Alexa skills app
"""

import importlib


class SkillSettings:
    """
    Singleton settings for app
    """
    settings = None

    class SkillSettingsImpl:
        # how far back in time a request can be, in seconds; cannot be greater than 150 according to
        # https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/developing-an-alexa-skill-as-a-web-service#timestamp
        REQUEST_TIMEOUT = 100
        es_server = 'ES_SERVER'
        dynamodb = 'chat-dev'
        vi = None
        record = False
        playback = False

        def get_record_dir(self):
            """
            Get the file where replays should be saved
            """
            return f'src/test/resources/playback/skillsearch'

        def get_record_file(self):
            """
            Get the file where replays should be saved
            """
            return f'{self.get_record_dir()}/recordings.json'

        def get_policy(self, request: dict = None):
            policy_module = importlib.import_module(f"tests.skillsearch.policy")
            return policy_module.Policy.initialize(request)

    def __init__(self):
        if not SkillSettings.settings:
            SkillSettings.settings = SkillSettings.SkillSettingsImpl()

    def __getattr__(self, name):
        return getattr(self.settings, name)

    def __setattr__(self, key, value):
        return setattr(self.settings, key, value)
