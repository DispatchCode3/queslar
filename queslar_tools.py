import requests
import sys


class Node():

    def __init__(self, state, parent, action):
        self.state = state
        self.parent = parent
        self.action = action


class StackFrontier():

    def __init__(self):
        self.frontier = []

    def add(self, node):
        self.frontier.append(node)

    def contains_state(self, state):
        return any(node.state == state for node in self.frontier)

    def empty(self):
        return len(self.frontier) == 0

    def remove(self):
        if self.empty():
            raise Exception("empty frontier")
        else:
            node = self.frontier[-1]
            self.frontier = self.frontier[:-1]
            return node


class Queslar():

    def __init__(self, budget):     
        response = requests.get('https://queslar.com/api/player/full/8ae05dc0af139baee899ce54db72ef03d14dadbf7659d2dab080674497355105')
        player_data = response.json()
        
        response = requests.get('https://queslar.com/api/market/history-latest/8ae05dc0af139baee899ce54db72ef03d14dadbf7659d2dab080674497355105')
        market_data = response.json()

        # Set gold budget
        self.gold = player_data['currency']['gold']
        if budget > self.gold:
            self.budget = self.gold
        else:
            self.budget = budget

        # Starting player resources
        self.p_relics = player_data['currency']['relics']
        self.p_meat = player_data['currency']['meat']
        self.p_iron = player_data['currency']['iron']
        self.p_wood = player_data['currency']['wood']
        self.p_stone = player_data['currency']['stone']

        # Starting resource cost
        self.m_relics = market_data[3]['price']
        self.m_meat = market_data[5]['price']
        self.m_iron = market_data[7]['price']
        self.m_wood = market_data[9]['price']
        self.m_stone = market_data[11]['price']

        # Starting boosts
        self.b_chc = player_data['boosts']['critChance']
        self.b_chd = player_data['boosts']['critDamage']
        self.b_multi = player_data['boosts']['multistrike']
        self.h_chc = player_data['boosts']['chairs']
        self.h_chd = player_data['boosts']['stove']
        self.h_multi = player_data['boosts']['sink']

        # Starting postion
        self.start = (self.b_chc, self.b_chd, self.b_multi, self.h_chc, self.h_chd, self.h_multi)

        # Set goal (infinity for now?)
        self.goal = float('inf')

        # Initialize this state to not be THE solution
        self.solution = None


    def print(self):
        solution = self.solution[1] if self.solution is not None else None
        print()
        print(solution)
        print()


    def boost_cost(self, critChance, critDamage, multistrike):
        net_chc = self.b_chc - critChance
        net_chd = self.b_chd - critDamage
        net_multi = self.b_multi - multistrike
        
        chc_cost = 0
        chd_cost = 0
        multi_cost = 0

        if net_chc > 0:
            for i in range(net_chc):
                chc_cost += ((self.b_chc + (i + 1)) * 10) + 10
        if net_chd > 0:
            for i in range(net_chd):
                chd_cost += ((self.b_chd + (i + 1)) * 10) + 10
        if net_multi > 0:
            for i in range(net_multi):
                multi_cost += ((self.b_multi + (i + 1)) * 10) + 10

        total_relics = self.p_relics - (chc_cost + chd_cost + multi_cost)
        total_price = 0
        if total_relics > 0:
            total_price = total_relics * self.m_relics
        
        return total_price        


    def house_cost(self):
        
        #TODO#

    def neighbors(self,state):
        bcc, bcd, bcm, hcc, hcd, hcm = state
        candidates = [
            ("Boost CHC", (bcc + 1, bcd, bcm, hcc, hcd, hcm)),
            ("Boost CHD", (bcc, bcd + 1, bcm, hcc, hcd, hcm)),
            ("Boost Multi", (bcc, bcd, bcm + 1, hcc, hcd, hcm)),
            ("House CHC", (bcc, bcd, bcm, hcc + 1, hcd, hcm)),
            ("House CHD", (bcc, bcd, bcm, hcc, hcd + 1, hcm)),
            ("House Multi", (bcc, bcd, bcm, hcc, hcd, hcm + 1))
        ]

        result = []
        for action, (bc, bd, bm, hc, hd, hm) in candidates:

            boost_total_cost = self.boost_cost(bc, bd, bm)
            house_total_cost = self.house_cost(hc, hd, hm)
            total_cost = boost_total_cost + house_total_cost

            if total_cost < self.budget:
                result.append((action, (bcc, bcd, bcm, hcc, hcd, hcm + 1)))
        return result

    
    def solve(self):
        """Finds a solution to maze, if one exists."""

        # Keep track of number of states explored
        self.num_explored = 0

        # Initialize frontier to just the starting position
        start = Node(state=self.start, parent=None, action=None)
        frontier = StackFrontier()
        frontier.add(start)

        # Initialize an empty explored set
        self.explored = set()

        # Keep looping until solution found
        while True:

            # If nothing left in frontier, then no path
            if frontier.empty():
                raise Exception("no solution")

            # Choose a node from the frontier
            node = frontier.remove()
            self.num_explored += 1

            # If node is the goal, then we have a solution
            if node.state == self.goal:
                actions = []
                cells = []
                while node.parent is not None:
                    actions.append(node.action)
                    cells.append(node.state)
                    node = node.parent
                actions.reverse()
                cells.reverse()
                self.solution = (actions, cells)
                return

            # Mark node as explored
            self.explored.add(node.state)

            # Add neighbors to frontier
            for action, state in self.neighbors(node.state):
                if not frontier.contains_state(state) and state not in self.explored:
                    child = Node(state=state, parent=node, action=action)
                    frontier.add(child)


if len(sys.argv) != 2:
    sys.exit("Usage: python queslar_tools.py budget")

q = Queslar(sys.argv[1])
print("Current:")
m.print()
print("Solving...")
m.solve()
print("States Explored:", m.num_explored)
print("Solution:")
m.print()
