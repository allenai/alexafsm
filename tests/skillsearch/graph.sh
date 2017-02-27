#!/usr/bin/env bash

png=./tests/skillsearch/fsm.png
export PYTHONPATH=./alexafsm:$PYTHONPATH
python ./tests/skillsearch/graph.py $png
echo "Opening the FSM graph ..."
open $png
