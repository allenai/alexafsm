alexafsm
========

* Finite-state machine library for building complex Alexa conversations.
* Written in Python 3.6 (primarily for type annotation and string interpolation).
* Free software: Apache Software License 2.0.

## Features

* FSM-based library for building Alexa skills with complex dialog state tracking. 
* Built-in analytics with [VoiceLabs](http://voicelabs.co/).

## Getting Started

Install from [PyPi](https://pypi.python.org/pypi/alexafsm): `pip install alexafsm`

Consult the Alexa skill search skill in the `tests` directory for details of how to 
write an `alexafsm` skill. An Alexa skill is composed of the following three classes: 
`SessionAttributes`, `States`, and `Policy`:

* `SessionAttributes` is a class that holds session attributes 
(`alexa_request['session']['attributes']`). 
   * The core attributes are `intent`, `slots`, and `state`. `intent` and `slots` map 
   directly to Alexa's concepts. 
   * `slots` should be of type `Slots`, which in turn is defined as a named tuple, one 
   field for each slot type. In the skill search example, `Slots = namedtuple('Slots', ['query']`).
   This named tuple class should be specified in the class definition as `slots_cls = Slots`.
   * `state` holds the name of the current state in the state machine.
   * Each Alexa skill can contain arbitrary number of additional attributes. If an attribute is 
    not meant to be sent back to Alexa server (e.g. so as to reduce the payload size), it should
    be added to `not_sent_fields`. In the skill search example, `skill` and `result` are not sent 
    to Alexa server.
*  `States` is a class that specifies most of the FSM and its behavior. It holds a reference to
a `SessionAttributes` object, the type of which is specified by overriding the 
`session_attributes_cls` class attribute. The FSM is specified by a list of parameter-less methods. 
Each method specifies the following:
     * The name of the method is also the name of a state in the FSM.
     * The method may be decorated with one or several transitions, using `with_transitions`
     decorators. Transitions can be inbound (`source` needs to be specified) or outbound (`dest`
     needs to be specified). 
     * Each method returns a `Response` object which is sent to Alexa. 
     * Transitions can be specified with `prepare`, `after`, and `conditions` attributes. See
      https://github.com/tyarkoni/transitions for detailed documentations. The values of these
      attributes are parameter-less methods of the `Policy` class, which is described next.
* `Policy` is the class that holds everything together. It contains a reference to a `States` 
object, the type of which is specified by overriding the `states_cls` class attribute. A `Policy` 
 object initializes itself by constructing a FSM based on the `States` type. It can also add
 additional transitions (using method `add_extra_transitions`) that may not be easily specified 
 in the `States` class via `with_transition` decorator. `Policy` class contains the following 
 key methods:
    * `handle` takes an Alexa request, parses it, and hands over intent requests to `execute` method. 
    * `execute` updates (`update_with_request`) the policy's internal state with the request's 
    details (intent, slots, session attributes), then call `trigger` to make the state transition. 
    It then looks up the corresponding response generating methods of the `States` class to generate
    a response for Alexa.
    * `initialize` will initialize a policy without any request.
    * `get_policy` implements a `lru_cache`-backed pool of policies to handle multiple 
    users/sessions. The cache is keyed of session Id (`alexa_request['session'][sessionId]`). 
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
    return json.dumps(policy.handle(req, vi).build_alexa_response()).encode('utf-8')
```

