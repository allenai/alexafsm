"""
Representation of response returned to user
"""

from collections import namedtuple

from alexafsm.session_attributes import SessionAttributes


class Response(namedtuple('Response', ['speech', 'card', 'card_content', 'reprompt', 'should_end',
                                       'image', 'session_attributes'])):
    """
    Pythonic representation of the response to be sent to Alexa
    """
    def __new__(cls, speech: str, reprompt: str, card: str = None, should_end: bool = False,
                card_content: str = None, image: str = None,
                session_attributes: SessionAttributes = SessionAttributes()):
        if not card_content:
            card_content = speech
        return super(Response, cls) \
            .__new__(cls, speech=speech, card=card, reprompt=reprompt, should_end=should_end,
                     card_content=card_content.strip(), image=image,
                     session_attributes=session_attributes)

    def to_json(self):
        """
        Build entire Alexa response as a JSON-serializable dictionary
        """
        card = None

        if self.card:
            if self.image:
                card = {
                    'type': 'Standard',
                    'image': {
                        'largeImageUrl': self.image
                    },
                    'title': self.card,
                    'text': self.card_content
                }
            else:
                card = {
                    'type': 'Simple',
                    'title': self.card,
                    'content': self.card_content
                }

        resp = {
            'outputSpeech': {
                'type': 'PlainText',
                'text': self.speech
            },
            'card': card,
            'reprompt': {
                'outputSpeech': {
                    'type': 'PlainText',
                    'text': self.reprompt
                }
            },
            'shouldEndSession': self.should_end
        }

        if not resp['card']:
            del resp['card']

        return {
            'version': '1.0',
            'sessionAttributes': self.session_attributes,
            'response': resp
        }


def welcome(skill_name: str, default_prompt: str) -> Response:
    return Response(
        speech=f"Welcome to {skill_name}, {default_prompt}",
        reprompt=default_prompt)


def end(skill_name: str) -> Response:
    return Response(
        speech=f"Thank you for using {skill_name}",
        reprompt="",
        should_end=True)


NOT_UNDERSTOOD = Response(
    speech="I did not understand your response, please say it differently.",
    reprompt="Please respond in a different way."
)
