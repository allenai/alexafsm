#!/usr/bin/env bash

export PYTHONPATH=./alexafsm:$PYTHONPATH
python ./tests/skillsearch/bin/print_machine.py > ./tests/skillsearch/machine.txt
