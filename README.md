alexafsm
========

* Finite-state machine library for building complex Alexa conversations.
* Written in Python 3.6 (primarily for type annotation and string interpolation).
* Free software: Apache Software License 2.0.

## Features

* FSM-based library for building Alexa skills with complex dialog state tracking. 
* Built-in analytics with [VoiceLabs](http://voicelabs.co/).
* Can be paired with any Python server library (Flask, CherryPy, etc.)

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
*`intent` and `slots` map directly to Alexa's concepts. 
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
 `many_results`. 
* Each method returns a `Response` object which is sent to Alexa. 
* Transitions can be specified with `prepare`, `after`, and `conditions` attributes. See
https://github.com/tyarkoni/transitions for detailed documentations. The values of these
attributes are parameter-less methods of the `Policy` class, which is described next.
      
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

