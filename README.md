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
* Option to use session Id-based pool of session handlers.
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
field for each slot type. In the skill search example, `Slots = namedtuple('Slots', ['query']`).
This named tuple class should be specified in the class definition as `slots_cls = Slots`.
* `state` holds the name of the current state in the state machine.
* Each Alexa skill can contain arbitrary number of additional attributes. If an attribute is
not meant to be sent back to Alexa server (e.g. so as to reduce the payload size), it should
be added to `not_sent_fields`. In the skill search example, `skill` and `result` are not sent
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
        'trigger': amazon_intent.YES,             # the triggering intent
        'source': ['one_result', 'many_results'], # list of source states
        'prepare': 'm_retrieve_skill_with_id'     # action to be executed before transition
    }
)
def describing(self) -> response.Response:
    skill = self.attributes.skill

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
a database. They are the only methods responsible for side-effects, e.g. modifying
the attributes of the states. This design facilitates ease of debugging.

### `Policy`

`Policy` is the class that holds everything together. It contains a reference to a `States`
object, the type of which is specified by overriding the `states_cls` class attribute. A `Policy`
object initializes itself by constructing a FSM based on the `States` type. It can also add
additional transitions (using method `add_extra_transitions`) that may not be easily specified
in the `States` class via `with_transition` decorator. `Policy` class contains the following
key methods:

* `handle` takes an Alexa request, parses it, and hands over all intent requests to `execute` method.
* `execute` updates (`update_with_request`) the policy's internal state with the request's
    details (intent, slots, session attributes), then calls `trigger` to make the state transition.
    It then looks up the corresponding response generating methods of the `States` class to generate
    a response for Alexa.
* `initialize` will initialize a policy without any request.
* `get_policy` implements a `lru_cache`-backed pool of policies to handle multiple
    users/sessions. The cache is keyed off session Id (`alexa_request['session'][sessionId]`).
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
    policy = Policy.get_policy(req['session']['sessionId'])
    # Alternatively, use policy = Policy.initialize() to bypass policy pool

    return json.dumps(policy.handle(req).build_alexa_response()).encode('utf-8')
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

### Graph Visualization

`alexafsm` uses the `transitions` library's API to draw the FSM graph. For example,
the skill search skill's FSM can be visualized using the [graph.py](https://github.com/allenai/alexafsm/blob/master/tests/skillsearch/server.py).
invoked from [graph.sh](https://github.com/allenai/alexafsm/blob/master/tests/skillsearch/graph.sh).
The resulting graph is displayed follow:

![FSM Example](https://github.com/allenai/alexafsm/blob/master/tests/skillsearch/fsm.png)

### Graph Printout

For complex graphs, it may be easier to inspect the FSM in text format. Use the
`print_machine` method to accomplish this. The output for the skill search skill is
below:

```text
Machine states:
    initial, describing, exiting, is_that_all, many_results, no_results, one_result, rephrase_or_refine, search_prompt

Events and transitions:

Event: AMAZON.YesIntent
    Source: one_result
        one_result -> describing, prepare: ['m_retrieve_skill_with_id']
    Source: many_results
        many_results -> describing, prepare: ['m_retrieve_skill_with_id']
    Source: describing
        describing -> exiting
    Source: is_that_all
        is_that_all -> exiting
Event: AMAZON.CancelIntent
    Source: initial
        initial -> exiting
    Source: describing
        describing -> exiting
        describing -> is_that_all
    Source: exiting
        exiting -> exiting
    Source: is_that_all
        is_that_all -> exiting
    Source: many_results
        many_results -> exiting
    Source: no_results
        no_results -> exiting
    Source: one_result
        one_result -> exiting
    Source: rephrase_or_refine
        rephrase_or_refine -> exiting
    Source: search_prompt
        search_prompt -> exiting
Event: AMAZON.NoIntent
    Source: one_result
        one_result -> is_that_all
    Source: many_results
        many_results -> rephrase_or_refine
    Source: describing
        describing -> search_prompt
    Source: is_that_all
        is_that_all -> search_prompt
Event: AMAZON.StopIntent
    Source: describing
        describing -> is_that_all
Event: Search
    Source: initial
        initial -> no_results, prepare: ['m_search'], conditions: ['m_no_results']
        initial -> one_result, prepare: ['m_search'], conditions: ['m_one_result']
        initial -> many_results, prepare: ['m_search'], conditions: ['m_many_results']
    Source: describing
        describing -> no_results, prepare: ['m_search'], conditions: ['m_no_results']
        describing -> one_result, prepare: ['m_search'], conditions: ['m_one_result']
        describing -> many_results, prepare: ['m_search'], conditions: ['m_many_results']
    Source: exiting
        exiting -> no_results, prepare: ['m_search'], conditions: ['m_no_results']
        exiting -> one_result, prepare: ['m_search'], conditions: ['m_one_result']
        exiting -> many_results, prepare: ['m_search'], conditions: ['m_many_results']
    Source: is_that_all
        is_that_all -> no_results, prepare: ['m_search'], conditions: ['m_no_results']
        is_that_all -> one_result, prepare: ['m_search'], conditions: ['m_one_result']
        is_that_all -> many_results, prepare: ['m_search'], conditions: ['m_many_results']
    Source: many_results
        many_results -> no_results, prepare: ['m_search'], conditions: ['m_no_results']
        many_results -> one_result, prepare: ['m_search'], conditions: ['m_one_result']
        many_results -> many_results, prepare: ['m_search'], conditions: ['m_many_results']
    Source: no_results
        no_results -> no_results, prepare: ['m_search'], conditions: ['m_no_results']
        no_results -> one_result, prepare: ['m_search'], conditions: ['m_one_result']
        no_results -> many_results, prepare: ['m_search'], conditions: ['m_many_results']
    Source: one_result
        one_result -> no_results, prepare: ['m_search'], conditions: ['m_no_results']
        one_result -> one_result, prepare: ['m_search'], conditions: ['m_one_result']
        one_result -> many_results, prepare: ['m_search'], conditions: ['m_many_results']
    Source: rephrase_or_refine
        rephrase_or_refine -> no_results, prepare: ['m_search'], conditions: ['m_no_results']
        rephrase_or_refine -> one_result, prepare: ['m_search'], conditions: ['m_one_result']
        rephrase_or_refine -> many_results, prepare: ['m_search'], conditions: ['m_many_results']
    Source: search_prompt
        search_prompt -> no_results, prepare: ['m_search'], conditions: ['m_no_results']
        search_prompt -> one_result, prepare: ['m_search'], conditions: ['m_one_result']
        search_prompt -> many_results, prepare: ['m_search'], conditions: ['m_many_results']
```
