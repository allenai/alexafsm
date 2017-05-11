alexafsm
========

* Finite-state machine library for building complex Alexa conversations.
* Free software: Apache Software License 2.0.

Dialog agents need to keep track of the various pieces of information to make
decisions how to respond to a given user input. This is referred to as context,
session, or state tracking. As the dialog complexity increases, this
state-tracking logic becomes harder to write, debug, and maintain. This library
takes the finite-state machine design approach to address this complexity. Developers
using this library can model dialog agents with first-class concepts such as
states, attributes, transition, and actions. Visualization and other tools are
also provided to help understand and debug complex FSM conversations.

## Features

* FSM-based library for building Alexa skills with complex dialog state tracking.
* Tools to validate, visualize, and print the FSM graph.
* Support analytics with [VoiceLabs](http://voicelabs.co/).
* Can be paired with any Python server library (Flask, CherryPy, etc.)
* Written in Python 3.6 (primarily for type annotation and string interpolation).

## Getting Started

Install from [PyPi](https://pypi.python.org/pypi/alexafsm):

    pip install alexafsm

Consult the [Alexa skill search](https://github.com/allenai/alexafsm/tree/master/tests/skillsearch) skill in the `tests` directory for details of how to
write an `alexafsm` skill. An Alexa skill is composed of the following three classes:
`SessionAttributes`, `States`, and `Policy`.

### `SessionAttributes`

`SessionAttributes` is a class that holds session attributes (`alexa_request['session']['attributes']`)
and any information we need to keep track of dialog state.
* The core attributes are `intent`, `slots`, and `state`.
* `intent` and `slots` map directly to Alexa's concepts.
* `slots` should be of type `Slots`, which in turn is defined as a named tuple, one
field for each slot type. In the skill search example, `Slots = namedtuple('Slots', ['query', 'nth']`).
This named tuple class should be specified in the class definition as `slots_cls = Slots`.
* `state` holds the name of the current state in the state machine.
* Each Alexa skill can contain arbitrary number of additional attributes. If an attribute is
not meant to be sent back to Alexa server (e.g. so as to reduce the payload size), it should
be added to `not_sent_fields`. In the skill search example, `searched` and `first_time` are not sent
to Alexa server.

See the implementation of skill search skill's [`SessionAttributes`](https://github.com/allenai/alexafsm/blob/master/tests/skillsearch/session_attributes.py)

###  `States`

`States` is a class that specifies most of the FSM and its behavior. It holds a reference to
a `SessionAttributes` object, the type of which is specified by overriding the
`session_attributes_cls` class attribute. The FSM is specified by a list of
parameter-less methods. Consider the following method:

```python
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
```

Each method encodes the following:

* The name of the method is also the name of a state (`describing`) in the FSM.
* The method may be decorated with one or several transitions, using `with_transitions`
decorators. Transitions can be inbound (`source` needs to be specified) or outbound (`dest`
needs to be specified).
* Each method returns a `Response` object which is sent to Alexa.
* Transitions can be specified with `prepare` and `conditions` attributes. See
https://github.com/tyarkoni/transitions for detailed documentations. The values of these
attributes are parameter-less methods of the `Policy` class.
* The `prepare` methods are responsible for "actions" of the FSM such as querying
a database. The `after` methods are responsible for updating the state after the transition
completes. They are the only methods responsible for side-effects, e.g. modifying
the attributes of the states. This design facilitates ease of debugging.

### `Policy`

`Policy` is the class that holds everything together. It contains a reference to a `States`
object, the type of which is specified by overriding the `states_cls` class attribute. A `Policy`
object initializes itself by constructing a FSM based on the `States` type. `Policy` class 
contains the following key methods:

* `handle` takes an Alexa request, parses it, and hands over all intent requests to `execute` method.
* `execute` updates the policy's internal state with the request's
    details (intent, slots, session attributes), then calls `trigger` to make the state transition.
    It then looks up the corresponding response generating methods of the `States` class to generate
    a response for Alexa.
* `initialize` will initialize a policy without any request.
* `validate` performs validation of a policy object based on `Policy` class definition and
    a intent schema json file. It looks for intents that are not handled, invalid
    source/dest/prepare specifications, and unreachable states. The test in `test_skillsearch.py`
    performs such validation as a test of `alexafsm`.

The Alexa skill search skill in the `tests` directory also contains a Flask-based server that shows
how to use `Policy` in five lines of code:


```python
@app.route('/', methods=['POST'])
def main():
    req = flask_request.json
    policy = Policy.initialize()
    return json.dumps(policy.handle(req, settings.vi)).encode('utf-8')
```

## Other Tools

`alexafsm` supports validation, graph visualization, and printing of the FSM.

### Validation

Simply initialize a `Policy` before calling `validate`. This function takes as
input the path to the skill's Alexa intent schema json file and performs the
following checks:

* All Alexa intents have corresponding events/triggers in the FSM.
* All states have either inbound or outbound transitions.
* All transitions are specified with valid source and destination states.
* All conditions and prepare actions are handled with methods in the `Policy` class.

### Change Detection with Record and Playback

When making code changes that are not supposed to impact a skill's dialog logic, we may want a tool
to check that the skill's logic indeed stay the same. This is done by first recording 
(`SkillSettings().record = True`) one or several sessions, making the code change, then checking 
if the changed code still produces the same set of dialogs (`SkillSettings().playback = True`).
During playback, calls to databases such as ElasticSearch can be fulfilled from data read from files
generated during the recording. This is done by decorating the database call with `recordable`
function. See [the ElasticSearch call](https://github.com/allenai/alexafsm/blob/master/tests/skillsearch/clients.py#L40)
in Skill Search for an example usage.

### Graph Visualization

`alexafsm` uses the `transitions` library's API to draw the FSM graph. For example,
the skill search skill's FSM can be visualized using the [graph.py](https://github.com/allenai/alexafsm/blob/master/tests/skillsearch/bin/graph.py).
invoked from [graph.sh](https://github.com/allenai/alexafsm/blob/master/tests/skillsearch/bin/graph.sh).
The resulting graph is displayed follow:

![FSM Example](https://github.com/allenai/alexafsm/blob/master/tests/skillsearch/fsm.png)

### Graph Printout

For complex graphs, it may be easier to inspect the FSM in text format. Use the
`print_machine` method to accomplish this. The output for the skill search skill is
below:

```text
Machine states:
	bad_navigate, describe_ratings, describing, exiting, has_result, helping, initial, is_that_all, no_query_search, no_result, search_prompt

Events and transitions:

Event: NthSkill
	Source: bad_navigate
		bad_navigate -> bad_navigate, conditions: ['m_has_nth']
		bad_navigate -> has_result, conditions: ['m_has_nth']
	Source: describe_ratings
		describe_ratings -> bad_navigate, conditions: ['m_has_nth']
		describe_ratings -> has_result, conditions: ['m_has_nth']
	Source: describing
		describing -> bad_navigate, conditions: ['m_has_nth']
		describing -> has_result, conditions: ['m_has_nth']
	Source: exiting
		exiting -> bad_navigate, conditions: ['m_has_nth']
		exiting -> has_result, conditions: ['m_has_nth']
	Source: has_result
		has_result -> bad_navigate, conditions: ['m_has_nth']
		has_result -> has_result, conditions: ['m_has_nth']
	Source: helping
		helping -> bad_navigate, conditions: ['m_has_nth']
		helping -> has_result, conditions: ['m_has_nth']
	Source: initial
		initial -> bad_navigate, conditions: ['m_has_nth']
		initial -> has_result, conditions: ['m_has_nth']
	Source: is_that_all
		is_that_all -> bad_navigate, conditions: ['m_has_nth']
		is_that_all -> has_result, conditions: ['m_has_nth']
	Source: no_query_search
		no_query_search -> bad_navigate, conditions: ['m_has_nth']
		no_query_search -> has_result, conditions: ['m_has_nth']
	Source: no_result
		no_result -> bad_navigate, conditions: ['m_has_nth']
		no_result -> has_result, conditions: ['m_has_nth']
	Source: search_prompt
		search_prompt -> bad_navigate, conditions: ['m_has_nth']
		search_prompt -> has_result, conditions: ['m_has_nth']
Event: PreviousSkill
	Source: bad_navigate
		bad_navigate -> bad_navigate, conditions: ['m_has_previous']
		bad_navigate -> has_result, conditions: ['m_has_previous']
	Source: describe_ratings
		describe_ratings -> bad_navigate, conditions: ['m_has_previous']
		describe_ratings -> has_result, conditions: ['m_has_previous']
	Source: describing
		describing -> bad_navigate, conditions: ['m_has_previous']
		describing -> has_result, conditions: ['m_has_previous']
	Source: exiting
		exiting -> bad_navigate, conditions: ['m_has_previous']
		exiting -> has_result, conditions: ['m_has_previous']
	Source: has_result
		has_result -> bad_navigate, conditions: ['m_has_previous']
		has_result -> has_result, conditions: ['m_has_previous']
	Source: helping
		helping -> bad_navigate, conditions: ['m_has_previous']
		helping -> has_result, conditions: ['m_has_previous']
	Source: initial
		initial -> bad_navigate, conditions: ['m_has_previous']
		initial -> has_result, conditions: ['m_has_previous']
	Source: is_that_all
		is_that_all -> bad_navigate, conditions: ['m_has_previous']
		is_that_all -> has_result, conditions: ['m_has_previous']
	Source: no_query_search
		no_query_search -> bad_navigate, conditions: ['m_has_previous']
		no_query_search -> has_result, conditions: ['m_has_previous']
	Source: no_result
		no_result -> bad_navigate, conditions: ['m_has_previous']
		no_result -> has_result, conditions: ['m_has_previous']
	Source: search_prompt
		search_prompt -> bad_navigate, conditions: ['m_has_previous']
		search_prompt -> has_result, conditions: ['m_has_previous']
Event: NextSkill
	Source: bad_navigate
		bad_navigate -> bad_navigate, conditions: ['m_has_next']
		bad_navigate -> has_result, conditions: ['m_has_next']
	Source: describe_ratings
		describe_ratings -> bad_navigate, conditions: ['m_has_next']
		describe_ratings -> has_result, conditions: ['m_has_next']
	Source: describing
		describing -> bad_navigate, conditions: ['m_has_next']
		describing -> has_result, conditions: ['m_has_next']
	Source: exiting
		exiting -> bad_navigate, conditions: ['m_has_next']
		exiting -> has_result, conditions: ['m_has_next']
	Source: has_result
		has_result -> bad_navigate, conditions: ['m_has_next']
		has_result -> has_result, conditions: ['m_has_next']
	Source: helping
		helping -> bad_navigate, conditions: ['m_has_next']
		helping -> has_result, conditions: ['m_has_next']
	Source: initial
		initial -> bad_navigate, conditions: ['m_has_next']
		initial -> has_result, conditions: ['m_has_next']
	Source: is_that_all
		is_that_all -> bad_navigate, conditions: ['m_has_next']
		is_that_all -> has_result, conditions: ['m_has_next']
	Source: no_query_search
		no_query_search -> bad_navigate, conditions: ['m_has_next']
		no_query_search -> has_result, conditions: ['m_has_next']
	Source: no_result
		no_result -> bad_navigate, conditions: ['m_has_next']
		no_result -> has_result, conditions: ['m_has_next']
	Source: search_prompt
		search_prompt -> bad_navigate, conditions: ['m_has_next']
		search_prompt -> has_result, conditions: ['m_has_next']
Event: AMAZON.NoIntent
	Source: has_result
		has_result -> bad_navigate, conditions: ['m_has_next']
		has_result -> has_result, conditions: ['m_has_next']
	Source: describe_ratings
		describe_ratings -> is_that_all
	Source: describing
		describing -> search_prompt
	Source: is_that_all
		is_that_all -> search_prompt
Event: DescribeRatings
	Source: bad_navigate
		bad_navigate -> describe_ratings, conditions: ['m_has_result']
	Source: describe_ratings
		describe_ratings -> describe_ratings, conditions: ['m_has_result']
	Source: describing
		describing -> describe_ratings, conditions: ['m_has_result']
	Source: exiting
		exiting -> describe_ratings, conditions: ['m_has_result']
	Source: has_result
		has_result -> describe_ratings, conditions: ['m_has_result']
	Source: helping
		helping -> describe_ratings, conditions: ['m_has_result']
	Source: initial
		initial -> describe_ratings, conditions: ['m_has_result']
	Source: is_that_all
		is_that_all -> describe_ratings, conditions: ['m_has_result']
	Source: no_query_search
		no_query_search -> describe_ratings, conditions: ['m_has_result']
	Source: no_result
		no_result -> describe_ratings, conditions: ['m_has_result']
	Source: search_prompt
		search_prompt -> describe_ratings, conditions: ['m_has_result']
Event: AMAZON.YesIntent
	Source: has_result
		has_result -> describing
	Source: describe_ratings
		describe_ratings -> describing
	Source: describing
		describing -> exiting
	Source: is_that_all
		is_that_all -> exiting
Event: AMAZON.CancelIntent
	Source: no_result
		no_result -> exiting
	Source: search_prompt
		search_prompt -> exiting
	Source: is_that_all
		is_that_all -> exiting
	Source: bad_navigate
		bad_navigate -> exiting
	Source: no_query_search
		no_query_search -> exiting
	Source: describing
		describing -> is_that_all
	Source: has_result
		has_result -> is_that_all
	Source: describe_ratings
		describe_ratings -> is_that_all
	Source: initial
		initial -> search_prompt
	Source: helping
		helping -> search_prompt
Event: AMAZON.StopIntent
	Source: no_result
		no_result -> exiting
	Source: search_prompt
		search_prompt -> exiting
	Source: is_that_all
		is_that_all -> exiting
	Source: bad_navigate
		bad_navigate -> exiting
	Source: no_query_search
		no_query_search -> exiting
	Source: describing
		describing -> is_that_all
	Source: has_result
		has_result -> is_that_all
	Source: describe_ratings
		describe_ratings -> is_that_all
	Source: initial
		initial -> search_prompt
	Source: helping
		helping -> search_prompt
Event: NewSearch
	Source: bad_navigate
		bad_navigate -> exiting, conditions: ['m_searching_for_exit']
		bad_navigate -> has_result, prepare: ['m_search'], conditions: ['m_has_result_and_query']
		bad_navigate -> no_query_search, conditions: ['m_no_query_search']
		bad_navigate -> no_result, prepare: ['m_search'], conditions: ['m_no_result']
	Source: describe_ratings
		describe_ratings -> exiting, conditions: ['m_searching_for_exit']
		describe_ratings -> has_result, prepare: ['m_search'], conditions: ['m_has_result_and_query']
		describe_ratings -> no_query_search, conditions: ['m_no_query_search']
		describe_ratings -> no_result, prepare: ['m_search'], conditions: ['m_no_result']
	Source: describing
		describing -> exiting, conditions: ['m_searching_for_exit']
		describing -> has_result, prepare: ['m_search'], conditions: ['m_has_result_and_query']
		describing -> no_query_search, conditions: ['m_no_query_search']
		describing -> no_result, prepare: ['m_search'], conditions: ['m_no_result']
	Source: exiting
		exiting -> exiting, conditions: ['m_searching_for_exit']
		exiting -> has_result, prepare: ['m_search'], conditions: ['m_has_result_and_query']
		exiting -> no_query_search, conditions: ['m_no_query_search']
		exiting -> no_result, prepare: ['m_search'], conditions: ['m_no_result']
	Source: has_result
		has_result -> exiting, conditions: ['m_searching_for_exit']
		has_result -> has_result, prepare: ['m_search'], conditions: ['m_has_result_and_query']
		has_result -> no_query_search, conditions: ['m_no_query_search']
		has_result -> no_result, prepare: ['m_search'], conditions: ['m_no_result']
	Source: helping
		helping -> exiting, conditions: ['m_searching_for_exit']
		helping -> has_result, prepare: ['m_search'], conditions: ['m_has_result_and_query']
		helping -> no_query_search, conditions: ['m_no_query_search']
		helping -> no_result, prepare: ['m_search'], conditions: ['m_no_result']
	Source: initial
		initial -> exiting, conditions: ['m_searching_for_exit']
		initial -> has_result, prepare: ['m_search'], conditions: ['m_has_result_and_query']
		initial -> no_query_search, conditions: ['m_no_query_search']
		initial -> no_result, prepare: ['m_search'], conditions: ['m_no_result']
	Source: is_that_all
		is_that_all -> exiting, conditions: ['m_searching_for_exit']
		is_that_all -> has_result, prepare: ['m_search'], conditions: ['m_has_result_and_query']
		is_that_all -> no_query_search, conditions: ['m_no_query_search']
		is_that_all -> no_result, prepare: ['m_search'], conditions: ['m_no_result']
	Source: no_query_search
		no_query_search -> exiting, conditions: ['m_searching_for_exit']
		no_query_search -> has_result, prepare: ['m_search'], conditions: ['m_has_result_and_query']
		no_query_search -> no_query_search, conditions: ['m_no_query_search']
		no_query_search -> no_result, prepare: ['m_search'], conditions: ['m_no_result']
	Source: no_result
		no_result -> exiting, conditions: ['m_searching_for_exit']
		no_result -> has_result, prepare: ['m_search'], conditions: ['m_has_result_and_query']
		no_result -> no_query_search, conditions: ['m_no_query_search']
		no_result -> no_result, prepare: ['m_search'], conditions: ['m_no_result']
	Source: search_prompt
		search_prompt -> exiting, conditions: ['m_searching_for_exit']
		search_prompt -> has_result, prepare: ['m_search'], conditions: ['m_has_result_and_query']
		search_prompt -> no_query_search, conditions: ['m_no_query_search']
		search_prompt -> no_result, prepare: ['m_search'], conditions: ['m_no_result']
Event: AMAZON.HelpIntent
	Source: bad_navigate
		bad_navigate -> helping
	Source: describe_ratings
		describe_ratings -> helping
	Source: describing
		describing -> helping
	Source: exiting
		exiting -> helping
	Source: has_result
		has_result -> helping
	Source: helping
		helping -> helping
	Source: initial
		initial -> helping
	Source: is_that_all
		is_that_all -> helping
	Source: no_query_search
		no_query_search -> helping
	Source: no_result
		no_result -> helping
	Source: search_prompt
		search_prompt -> helping

```
