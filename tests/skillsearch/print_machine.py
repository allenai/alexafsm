from alexafsm.utils import print_machine
from tests.skillsearch.policy import Policy

if __name__ == '__main__':
    print_machine(Policy.initialize())
