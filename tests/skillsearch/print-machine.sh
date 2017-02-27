#!/usr/bin/env bash

export PYTHONPATH=./alexafsm:$PYTHONPATH
python ./tests/skillsearch/print_machine.py > ./tests/skillsearch/machine.txt
