"""Settings for Alexa skills app"""


class SkillSettings:
    """Singleton settings for app"""
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
            """Get the directory where replays should be saved"""
            return f'tests/skillsearch/playback'

        def get_record_file(self):
            """Get the file where replays should be saved"""
            return f'{self.get_record_dir()}/recordings.json'

    def __init__(self):
        if not SkillSettings.settings:
            SkillSettings.settings = SkillSettings.SkillSettingsImpl()

    def __getattr__(self, name):
        return getattr(self.settings, name)

    def __setattr__(self, key, value):
        return setattr(self.settings, key, value)
