"""
States implementation for skill search
"""
from alexafsm import response, amazon_intent
from alexafsm.states import States as IStates, with_transitions
from tests.skillsearch.session_attributes import SessionAttributes
from tests.skillsearch.skill import Skill


class States(IStates):
    """
    A collection of static methods that generate responses based on the current session attributes.
    Each method corresponds to a state of the FSM.
    """

    session_attributes_cls = SessionAttributes
    default_prompt = "What skill do you want to find"

    def no_results_search(self) -> response.Response:  # pylint: disable=no-self-use
        """
        if user refuses to remove category filter, then ask him to rephrase
        """
        return response.Response(
            speech=f"You asked for {self.attributes.slots.query},"
                   f" I could not find any such skills. Please rephrase.",
            reprompt=States.default_prompt
        )

    def one_result_search(self) -> response.Response:
        """
        when a search results in exactly one result
        """
        skill = self.attributes.skill
        attributes = self.attributes
        return response.Response(
            speech=f"You asked for {attributes.slots.query}, "
                   f" The only skill I could find is {_get_verbal_skill(skill)}."
                   f" Would you like to hear more about it?",
            card=f"Search for {attributes.slots.query}",
            card_content=f"""
            Top result: {skill.name}

            {skill.get_highlights()}
            """,
            reprompt=States.default_prompt
        )

    def many_results_search(self) -> response.Response:
        """
        when a search results in multiple results, allowing for the user to filter them down
        """
        attributes = self.attributes
        return response.Response(
            speech=f"Searching for {attributes.slots.query}."
                   f" The first of {attributes.result.hits.total} skills is"
                   f"{_get_verbal_skill(attributes.skill)}."
                   f" Does that sound like what you want?",
            card=f"""Search for "{attributes.slots.query}" """,
            card_content=f"""
            Top result: {attributes.skill.name}

            {attributes.skill.get_highlights()}
            """,
            reprompt=States.default_prompt
        )

    @with_transitions(
        {
            'trigger': amazon_intent.NO,
            'source': ['many_results_search']
        }
    )
    def rephrase_or_refine(self) -> response.Response:
        """
        when we're asking the user to refine a search because there are too many results and we
        haven't yet found the skill the user wants
        """
        return response.Response(
            speech="Please rephrase",
            reprompt="Rephrase your query."
        )

    @with_transitions({
        'trigger': amazon_intent.NO,
        'source': ['describing', 'is_that_all'],
    })
    def search_prompt(self) -> response.Response:
        """
        when we're asking the user to conduct a new search
        """
        return response.Response(
            speech=States.default_prompt,
            reprompt=States.default_prompt
        )

    @with_transitions(
        {
            'trigger': amazon_intent.YES,
            'source': ['one_result_search', 'many_results_search'],
            'prepare': 'm_retrieve_skill_with_id'
        }
    )
    def describing(self) -> response.Response:
        """
        Describe a skill, used in response generator
        """
        skill = self.attributes.skill
        if skill.num_ratings > 0:
            rating_str = f"{skill.avg_rating} (from {skill.num_ratings} reviews)"
        else:
            rating_str = "No reviews yet"
        # don't say category and creator because they will have already been said
        return response.Response(
            speech=f"Okay, just tell me when to stop. {skill.name}"
                   f" {_get_verbal_ratings(skill, say_no_reviews=False)}. {skill.description}",
            card=skill.name,
            card_content=f"""
            Creator: {skill.creator}
            Category: {skill.category}
            Average rating: {rating_str}
            {skill.description}
            """,
            image=skill.image_url,
            reprompt="Will that be all?"
        )

    @with_transitions(
        {
            'trigger': amazon_intent.NO,
            'source': ['one_result_search']
        },
        {
            'trigger': amazon_intent.CANCEL,
            'source': 'describing'
        },
        {
            'trigger': amazon_intent.STOP,
            'source': 'describing'
        }
    )
    def is_that_all(self) -> response.Response:
        """
        when we want to see if the user is done with the skill
        """
        return response.Response(
            speech="Okay, will that be all?",
            reprompt="Will that be all?"
        )

    @with_transitions(
        {
            'trigger': amazon_intent.YES,
            'source': ['describing', 'is_that_all']
        },
        {
            'trigger': amazon_intent.CANCEL,
            'source': '*'
        }
    )
    def exiting(self) -> response.Response:
        """
        when the user is done with the skill and wants to exit
        """
        return response.end(States.skill_name)


def _get_verbal_skill(skill: Skill) -> str:
    """
    Get the natural language representation of a skill

    This tells the user the name of the skill

    >>> _get_verbal_skill(Skill(name='AI thing', category='Smart Home'))
    'AI thing in the category Smart Home'

    Also lists the creator when known

    >>> _get_verbal_skill(Skill(name='AI thing', creator='AI2', category='Smart Home'))
    'AI thing by AI2 in the category Smart Home'
    """
    category_str = f" in the category {skill.category}"

    if skill.creator:
        return f"{skill.name} by {skill.creator}{category_str}"
    return f"{skill.name}{category_str}"


def _get_verbal_ratings(skill: Skill, say_no_reviews: bool = True) -> str:
    """
    Get a verbal description of the rating for a skill

    say_no_reviews: if there are no reviews, this will mention that explicitly
    """
    if skill.num_ratings > 0:
        return f"has an average rating of {skill.avg_rating} from {skill.num_ratings} reviews"
    if say_no_reviews:  # there are no reviews, and we want to tell the user that explicitly
        return "has no reviews at this time"
    return ""  # there are no reviews, but we don't need to tell the user that


def _get_highlights(skill: Skill):
    """
    Get highlights for a skill
    """
    return '\n'.join([h for _, hs in skill.meta.highlight.to_dict().items() for h in hs])
