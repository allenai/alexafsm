from alexafsm.states import with_transitions, States as StatesBase
from alexafsm import response
from alexafsm import amazon_intent

from tests.skillsearch.es_skill import Skill
from tests.skillsearch.intent import NTH_SKILL, PREVIOUS_SKILL, NEXT_SKILL, NEW_SEARCH, \
    DESCRIBE_RATINGS
from tests.skillsearch.session_attributes import SessionAttributes, ENGLISH_NUMBERS

MAX_SKILLS = 6
SKILL_NAME = "Skill Search"
DEFAULT_PROMPT = "What skill would you like to find?"
HELP = f"{SKILL_NAME} helps you search for skills. You can ask questions such as:" \
       f" how do i order pizza, or, I want to meditate." \
       f" For each question, {SKILL_NAME} only retrieves the most relevant skills." \
       f" In order to use a skill you find, you must first exit {SKILL_NAME} and then tell Alexa" \
       f" to open that skill." \
       f" {DEFAULT_PROMPT}"
HEAR_MORE = "Would you like to hear more about it?"
IS_THAT_ALL = "Will that be all?"


def _you_asked_for(query: str):
    return f"You asked for {query}. "


def _get_verbal_skill(skill: Skill) -> str:
    """Get the natural language representation of a skill """
    return skill.name


def _get_verbal_ratings(skill: Skill, say_no_reviews: bool = True) -> str:
    """Get a verbal description of the rating for a skill
    say_no_reviews: if there are no reviews, this will mention that explicitly
    """
    if skill.num_ratings > 0:
        return f"has an average rating of {skill.avg_rating} from {skill.num_ratings} reviews"
    if say_no_reviews:  # there are no reviews, and we want to tell the user that explicitly
        return "has no reviews at this time"
    return ""  # there are no reviews, but we don't need to tell the user that


def _get_highlights(skill: Skill):
    """Get highlights for a skill"""
    if 'highlight' in skill.meta:
        return '\n'.join([h for _, hs in skill.meta.highlight.to_dict().items() for h in hs])

    return skill.description


class States(StatesBase):
    """
    A collection of static methods that generate responses based on the current session attributes.
    Each method corresponds to a state of the FSM.
    """

    session_attributes_cls = SessionAttributes
    skill_name = SKILL_NAME
    default_prompt = DEFAULT_PROMPT
    # states to exit on when user requests Alexa to stop talking
    EXIT_ON_STOP_STATES = ['no_result', 'search_prompt', 'is_that_all', 'bad_navigate',
                           'no_query_search']
    # states to continue on when user requests Alexa to stop talking
    CONTINUE_ON_STOP_STATES = ['describing', 'has_result', 'describe_ratings']
    # states to prompt user for new search when user requests Alexa to stop talking
    PROMPT_ON_STOP_STATES = ['initial', 'helping']
    # initial is its own special thing -- don't exit when interrupting the initial help message

    def initial(self) -> response.Response:
        if self.attributes.first_time:
            welcome_speech = f"Welcome to {self.skill_name}. {HELP}"
        else:
            welcome_speech = f"Welcome to {self.skill_name}, {self.default_prompt}"

        return response.Response(
            speech=welcome_speech,
            reprompt=self.default_prompt
        )

    @with_transitions({'trigger': amazon_intent.HELP, 'source': '*'})
    def helping(self) -> response.Response:
        return response.Response(
            speech=HELP,
            reprompt=DEFAULT_PROMPT
        )

    @with_transitions(
        {
            'trigger': NEW_SEARCH,
            'source': '*',
            'conditions': 'm_no_query_search'
        }
    )
    def no_query_search(self) -> response.Response:
        """No query specified, ask for query"""
        return response.Response(
            speech=f"Please say what it is that you want to do. For example, 'I want to buy "
                   f"flowers'. Or, 'I want to get a ride.'",
            reprompt=DEFAULT_PROMPT
        )

    @with_transitions(
        {
            'trigger': NEW_SEARCH,
            'source': '*',
            'prepare': 'm_search',
            'conditions': 'm_no_result'
        })
    def no_result(self) -> response.Response:
        """No results, ask for rephrase or help"""
        return response.Response(
            speech=f"{_you_asked_for(self.attributes.query)},"
                   f" I could not find any such skills. Please rephrase, or say"
                   f" help me, for help.",
            reprompt=DEFAULT_PROMPT
        )

    @with_transitions(
        {
            'trigger': NEW_SEARCH,
            'source': '*',
            'prepare': 'm_search',
            'conditions': 'm_has_result_and_query'
        },
        {
            'trigger': NTH_SKILL,
            'source': '*',
            'conditions': 'm_has_nth',
            'after': 'm_set_nth'
        },
        {
            'trigger': PREVIOUS_SKILL,
            'source': '*',
            'conditions': 'm_has_previous',
            'after': 'm_set_previous'
        },
        {
            'trigger': NEXT_SKILL,
            'source': '*',
            'conditions': 'm_has_next',
            'after': 'm_set_next'
        },
        {
            'trigger': amazon_intent.NO,
            'source': 'has_result',
            'conditions': 'm_has_next',
            'after': 'm_set_next'
        }
    )
    def has_result(self) -> response.Response:
        """Offer a preview of a skill"""
        attributes = self.attributes
        query = attributes.query
        skill = attributes.skill
        asked_for_speech = ''
        if attributes.first_time_presenting_results:
            asked_for_speech = _you_asked_for(query)
        if attributes.number_of_hits == 1:
            skill_position_speech = 'The only skill I found is'
        else:
            skill_position_speech = f'The {ENGLISH_NUMBERS[attributes.skill_cursor]} skill is'
            if attributes.first_time_presenting_results:
                if attributes.number_of_hits > 6:
                    num_hits = f'Here are the top {MAX_SKILLS} results.'
                else:
                    num_hits = f'I found {len(attributes.skills)} skills.'
                skill_position_speech = f'{num_hits} {skill_position_speech}'
        return response.Response(
            speech=f"{asked_for_speech} "
                   f" {skill_position_speech} {_get_verbal_skill(skill)}."
                   f" {HEAR_MORE}",
            card=f"Search for {query}",
            card_content=f"""
            Top result: {skill.name}

            {_get_highlights(skill)}
            """,
            reprompt=DEFAULT_PROMPT
        )

    @with_transitions(
        {
            'trigger': NTH_SKILL,
            'source': '*',
            'unless': 'm_has_nth'
        },
        {
            'trigger': PREVIOUS_SKILL,
            'source': '*',
            'unless': 'm_has_previous'
        },
        {
            'trigger': NEXT_SKILL,
            'source': '*',
            'unless': 'm_has_next'
        },
        {
            'trigger': amazon_intent.NO,
            'source': 'has_result',
            'unless': 'm_has_next'
        }
    )
    def bad_navigate(self) -> response.Response:
        """Bad navigation (first, second, third, previous, next)"""
        attributes = self.attributes
        if not attributes.skills:
            if attributes.query:
                speech = f"I did not find any skills for query {attributes.query}."
            else:
                speech = f"To navigate to a skill, please search first. {HELP}"
        elif attributes.intent == PREVIOUS_SKILL:
            speech = "There is no previous skill. I am currently at skill number one."
        elif attributes.intent == NEXT_SKILL:
            speech = f"Sorry, there is no next skill. How else can I help you?"
        elif attributes.intent == amazon_intent.NO:
            speech = f"There are no more results. Please try a different search phrase."
        else:  # nth skill
            nth = attributes.nth_as_index
            if nth >= 0:
                speech = f"You asked for skill {nth + 1}. I found only " \
                         f"{len(attributes.skills)} skills for the query {attributes.query}."
            else:
                speech = f"Sorry, I'm not sure which skill you want to go to. Please rephrase. " \
                         f"For example, tell me about skill 3."

        return response.Response(
            speech=speech,
            reprompt=DEFAULT_PROMPT
        )

    @with_transitions(
        {
            'trigger': DESCRIBE_RATINGS,
            'source': '*',
            'conditions': 'm_has_result'
        }
    )
    def describe_ratings(self):
        """
        when we've found a skill that the user might like and the user wants to know how
        well-liked it is
        """
        skill = self.attributes.skill
        return response.Response(
            speech=f"{skill.name} {_get_verbal_ratings(skill)}."
                   f" Would you like to hear more about this skill?",
            reprompt="Would you like to hear more about this skill?"
        )

    @with_transitions(
        {
            'trigger': amazon_intent.NO,
            'source': ['describing', 'is_that_all'],
        },
        {
            'trigger': amazon_intent.CANCEL,
            'source': PROMPT_ON_STOP_STATES
        },
        {
            'trigger': amazon_intent.STOP,
            'source': PROMPT_ON_STOP_STATES
        }
    )
    def search_prompt(self) -> response.Response:
        """when we're asking the user to conduct a new search"""
        return response.Response(
            speech=DEFAULT_PROMPT,
            reprompt=DEFAULT_PROMPT
        )

    @with_transitions(
        {
            'trigger': amazon_intent.YES,
            'source': ['has_result', 'describe_ratings']
        }
    )
    def describing(self) -> response.Response:
        """Describe a skill, used in response generator"""
        skill = self.attributes.skill
        if skill.num_ratings > 0:
            rating_str = f"{skill.avg_rating} (from {skill.num_ratings} reviews)"
        else:
            rating_str = "No reviews yet"

        interrupt_hint = ""
        if not self.attributes.said_interrupt:
            interrupt_hint = "Okay, interrupt me anytime by saying 'Alexa.'"
            self.attributes.said_interrupt = True

        return response.Response(
            speech=f"{interrupt_hint} {skill.name}."
                   f" {skill.short_description}",
            card=skill.name,
            card_content=f"""
            Creator: {skill.creator}
            Category: {skill.category}
            Average rating: {rating_str}
            {skill.description}
            """,
            image=skill.image_url,
            reprompt=IS_THAT_ALL
        )

    @with_transitions(
        {
            'trigger': amazon_intent.NO,
            'source': 'describe_ratings'
        },
        {
            'trigger': amazon_intent.CANCEL,
            'source': CONTINUE_ON_STOP_STATES
        },
        {
            'trigger': amazon_intent.STOP,
            'source': CONTINUE_ON_STOP_STATES
        }
    )
    def is_that_all(self) -> response.Response:
        """when we want to see if the user is done with the skill"""
        return response.Response(
            speech=f"Okay, {IS_THAT_ALL}",
            reprompt=IS_THAT_ALL
        )

    @with_transitions(
        {
            'trigger': amazon_intent.YES,
            'source': ['describing', 'is_that_all']
        },
        {
            'trigger': amazon_intent.CANCEL,
            'source': EXIT_ON_STOP_STATES
        },
        {
            'trigger': amazon_intent.STOP,
            'source': EXIT_ON_STOP_STATES
        },
        {
            'trigger': NEW_SEARCH,
            'source': '*',
            'conditions': 'm_searching_for_exit'
        }
    )
    def exiting(self) -> response.Response:
        return response.end(SKILL_NAME)
