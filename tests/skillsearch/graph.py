import sys

from alexafsm.utils import graph
from tests.skillsearch.policy import Policy

if __name__ == '__main__':
    png_file = sys.argv[1]
    print(f"Drawing FSM graph for {Policy} to {png_file}")
    graph(Policy, png_file)
