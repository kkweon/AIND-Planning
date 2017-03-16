from aimacode.logic import PropKB
from aimacode.planning import Action
from aimacode.search import (
    Node, Problem,
)
from aimacode.utils import expr
from lp_utils import (
    FluentState, encode_state, decode_state,
)
from my_planning_graph import PlanningGraph


# User Defined Helper Functions
def At(object: str, place: str) -> expr:
    return expr("At({}, {})".format(object, place))


def In(object1: str, object2: str) -> expr:
    return expr("In({}, {})".format(object1, object2))


def Load(cargo: str, plane: str, airport: str) -> expr:
    return expr("Load({}, {}, {})".format(cargo, plane, airport))


def Unload(cargo: str, plane: str, airport: str) -> expr:
    return expr("Unload({}, {}, {})".format(cargo, plane, airport))


class AirCargoProblem(Problem):
    def __init__(self, cargos, planes, airports, initial: FluentState, goal: list):
        """

        :param cargos: list of str
            cargos in the problem
        :param planes: list of str
            planes in the problem
        :param airports: list of str
            airports in the problem
        :param initial: FluentState object
            positive and negative literal fluents (as expr) describing initial state
        :param goal: list of expr
            literal fluents required for goal test
        """
        self.state_map = initial.pos + initial.neg
        self.initial_state_TF = encode_state(initial, self.state_map)
        Problem.__init__(self, self.initial_state_TF, goal=goal)
        self.cargos = cargos
        self.planes = planes
        self.airports = airports
        self.actions_list = self.get_actions()

    def get_actions(self):
        '''
        This method creates concrete actions (no variables) for all actions in the problem
        domain action schema and turns them into complete Action objects as defined in the
        aimacode.planning module. It is computationally expensive to call this method directly;
        however, it is called in the constructor and the results cached in the `actions_list` property.

        Returns:
        ----------
        list<Action>
            list of Action objects
        '''

        # TODO create concrete Action objects based on the domain action schema for: Load, Unload, and Fly
        # concrete actions definition: specific literal action that does not include variables as with the schema
        # for example, the action schema 'Load(c, p, a)' can represent the concrete actions 'Load(C1, P1, SFO)'
        # or 'Load(C2, P2, JFK)'.  The actions for the planning problem must be concrete because the problems in
        # forward search and Planning Graphs must use Propositional Logic

        def load_actions():
            '''Create all concrete Load actions and return a list

            :return: list of Action objects
            '''
            loads = []
            # TODO create all load ground actions from the domain Load action
            for ap in self.airports:
                for p in self.planes:
                    for c in self.cargos:
                        precond_pos = [At(c, ap), At(p, ap)]
                        precond_neg = []
                        precond = [precond_pos, precond_neg]

                        effect_add = [In(c, p)]
                        effect_rem = [At(c, ap)]
                        effect = [effect_add, effect_rem]

                        load = Action(Load(c, p, ap), precond, effect)
                        loads.append(load)

            return loads

        def unload_actions():
            '''Create all concrete Unload actions and return a list

            :return: list of Action objects
            '''
            unloads = []
            # TODO create all Unload ground actions from the domain Unload
            # action
            for ap in self.airports:
                for p in self.planes:
                    for c in self.cargos:
                        precond_pos = [In(c, p), At(p, ap)]
                        precond_neg = []
                        precond = [precond_pos, precond_neg]

                        effect_add = [At(c, ap)]
                        effect_rem = [In(c, p)]
                        effect = [effect_add, effect_rem]

                        unload = Action(Unload(c, p, ap), precond, effect)
                        unloads.append(unload)

            return unloads

        def fly_actions():
            '''Create all concrete Fly actions and return a list

            :return: list of Action objects
            '''
            flys = []
            for fr in self.airports:
                for to in self.airports:
                    if fr != to:
                        for p in self.planes:
                            precond_pos = [expr("At({}, {})".format(p, fr)), ]
                            precond_neg = []
                            effect_add = [expr("At({}, {})".format(p, to))]
                            effect_rem = [expr("At({}, {})".format(p, fr))]
                            fly = Action(expr("Fly({}, {}, {})".format(p, fr, to)),
                                         [precond_pos, precond_neg],
                                         [effect_add, effect_rem])
                            flys.append(fly)
            return flys

        return load_actions() + unload_actions() + fly_actions()

    def actions(self, state: str) -> list:
        """ Return the actions that can be executed in the given state.

        :param state: str
            state represented as T/F string of mapped fluents (state variables)
            e.g. 'FTTTFF'
        :return: list of Action objects
        """
        possible_actions = []
        kb = PropKB()
        kb.tell(decode_state(state, self.state_map).pos_sentence())
        for action in self.actions_list:
            is_possible = True
            for clause in action.precond_pos:
                if clause not in kb.clauses:
                    is_possible = False
            for clause in action.precond_neg:
                if clause in kb.clauses:
                    is_possible = False
            if is_possible:
                possible_actions.append(action)

        return possible_actions

    def result(self, state: str, action: Action):
        """ Return the state that results from executing the given
        action in the given state. The action must be one of
        self.actions(state).

        :param state: state entering node
        :param action: Action applied
        :return: resulting state after action
        """
        new_state = FluentState([], [])
        old_state = decode_state(state, self.state_map)
        for fluent in old_state.pos:
            if fluent not in action.effect_rem:
                new_state.pos.append(fluent)
        for fluent in action.effect_add:
            if fluent not in new_state.pos:
                new_state.pos.append(fluent)
        for fluent in old_state.neg:
            if fluent not in action.effect_add:
                new_state.neg.append(fluent)
        for fluent in action.effect_rem:
            if fluent not in new_state.neg:
                new_state.neg.append(fluent)
        return encode_state(new_state, self.state_map)

    def goal_test(self, state: str) -> bool:
        """ Test the state to see if goal is reached

        :param state: str representing state
        :return: bool
        """
        kb = PropKB()
        kb.tell(decode_state(state, self.state_map).pos_sentence())
        for clause in self.goal:
            if clause not in kb.clauses:
                return False
        return True

    def h_1(self, node: Node):
        # note that this is not a true heuristic
        h_const = 1
        return h_const

    def h_pg_levelsum(self, node: Node):
        '''
        This heuristic uses a planning graph representation of the problem
        state space to estimate the sum of all actions that must be carried
        out from the current state in order to satisfy each individual goal
        condition.
        '''
        # requires implemented PlanningGraph class
        pg = PlanningGraph(self, node.state)
        pg_levelsum = pg.h_levelsum()
        return pg_levelsum

    def h_ignore_preconditions(self, node: Node):
        '''
        This heuristic estimates the minimum number of actions that must be
        carried out from the current state in order to satisfy all of the goal
        conditions by ignoring the preconditions required for an action to be
        executed.
        '''
        # TODO implement (see Russell-Norvig Ed-3 10.2.3  or Russell-Norvig
        # Ed-2 11.2)
        count = len([s for (i, s) in enumerate(self.state_map)
                     if s in self.goal and node.state[i] == "F"])

        return count


def air_cargo_p1() -> AirCargoProblem:
    cargos = ['C1', 'C2']
    planes = ['P1', 'P2']
    airports = ['JFK', 'SFO']

    pos = [expr('At(C1, SFO)'),
           expr('At(C2, JFK)'),
           expr('At(P1, SFO)'),
           expr('At(P2, JFK)')]

    neg = [expr('At(C2, SFO)'),
           expr('In(C2, P1)'),
           expr('In(C2, P2)'),
           expr('At(C1, JFK)'),
           expr('In(C1, P1)'),
           expr('In(C1, P2)'),
           expr('At(P1, JFK)'),
           expr('At(P2, SFO)')]

    init = FluentState(pos, neg)

    goal = [expr('At(C1, JFK)'),
            expr('At(C2, SFO)')]
    return AirCargoProblem(cargos, planes, airports, init, goal)


def air_cargo_p2() -> AirCargoProblem:
    """
    Given:
        Init(At(C1, SFO) ∧ At(C2, JFK) ∧ At(C3, ATL)
        ∧ At(P1, SFO) ∧ At(P2, JFK) ∧ At(P3, ATL)
        ∧ Cargo(C1) ∧ Cargo(C2) ∧ Cargo(C3)
        ∧ Plane(P1) ∧ Plane(P2) ∧ Plane(P3)
        ∧ Airport(JFK) ∧ Airport(SFO) ∧ Airport(ATL))
        Goal(At(C1, JFK) ∧ At(C2, SFO) ∧ At(C3, SFO))
    """
    cargos = ['C1', 'C2', 'C3']
    planes = ['P1', 'P2', 'P3']
    airports = ['SFO', 'JFK', 'ATL']

    pos = [At('C1', 'SFO'), At('C2', 'JFK'), At('C3', 'ATL')]
    pos += [At('P1', 'SFO'), At('P2', 'JFK'), At('P3', 'ATL')]

    neg = [At('C1', 'JFK'), At('C1', 'ATL'),
           At('C2', 'SFO'), At('C2', 'ATL'),
           At('C3', 'SFO'), At('C3', 'JFK')]

    neg += [At('P1', 'JFK'), At('P1', 'ATL'),
            At('P2', 'SFO'), At('P2', 'ATL'),
            At('P3', 'SFO'), At('P3', 'JFK')]

    neg += [In(c, p) for p in planes for c in cargos]

    init = FluentState(pos, neg)
    goal = [At('C1', 'JFK'), At('C2', 'SFO'), At('C3', 'SFO')]

    return AirCargoProblem(cargos, planes, airports, init, goal)


def air_cargo_p3() -> AirCargoProblem:
    # TODO implement Problem 3 definition
    '''
    Given: 
        Init(At(C1, SFO) ∧ At(C2, JFK) ∧ At(C3, ATL) ∧ At(C4, ORD) 
        ∧ At(P1, SFO) ∧ At(P2, JFK) 
        ∧ Cargo(C1) ∧ Cargo(C2) ∧ Cargo(C3) ∧ Cargo(C4)
        ∧ Plane(P1) ∧ Plane(P2)
        ∧ Airport(JFK) ∧ Airport(SFO) ∧ Airport(ATL) ∧ Airport(ORD))
        Goal(At(C1, JFK) ∧ At(C3, JFK) ∧ At(C2, SFO) ∧ At(C4, SFO))
    '''
    cargos = ['C1', 'C2', 'C3', 'C4']
    planes = ['P1', 'P2']
    airports = ['SFO', 'JFK', 'ATL', 'ORD']

    pos = [At('C1', 'SFO'), At('C2', 'JFK'), At('C3', 'ATL'), At('C4', 'ORD')]
    pos += [At('P1', 'SFO'), At('P2', 'JFK')]

    neg = [At('C1', 'JFK'), At('C1', 'ATL'), At('C1', 'ORD'),
           At('C2', 'SFO'), At('C2', 'ATL'), At('C2', 'ORD'),
           At('C3', 'SFO'), At('C3', 'JFK'), At('C3', 'ORD'),
           At('C4', 'SFO'), At('C4', 'JFK'), At('C4', 'ATL')]

    neg += [At('P1', 'JFK'), At('P1', 'ATL'), At('P1', 'ORD'),
            At('P2', 'SFO'), At('P2', 'ATL'), At('P2', 'ORD')]

    neg += [In(c, p) for p in planes for c in cargos]

    init = FluentState(pos, neg)
    goal = [At('C1', 'JFK'), At('C2', 'SFO'), At('C3', 'JFK'), At('C4', 'SFO')]

    return AirCargoProblem(cargos, planes, airports, init, goal)
