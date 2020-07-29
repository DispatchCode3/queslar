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
    self.h_chc = player_data['house']['chairs']
    self.h_chd = player_data['house']['stove']
    self.h_multi = player_data['house']['sink']

    # Starting postion
    self.start = (self.b_chc, self.b_chd, self.b_multi, self.h_chc, self.h_chd, self.h_multi)

    # Set moving goal
    self.goal = 0

    # Store the best position
    self.final = self.start

    # Initialize this state to not be THE solution
    self.solution = None


  def print(self):
    print()
    if self.start == self.final:
      print(self.start)
    elif self.goal == 0:
      print("You can't afford anything")
    else:
      bc = (self.final[0] - self.start[0])/10
      bd = (self.final[1] - self.start[1])/10
      bm = (self.final[2] - self.start[2])/10
      hc = (self.final[3] - self.start[3])/10
      hd = (self.final[4] - self.start[4])/10
      hm = (self.final[5] - self.start[5])/10
      print("Buy:")
      print()
      if bc > 0:
        print("  - Boost Crit Chance: ", bc)
      if bd > 0:
        print("  - Boost Crit Damage: ", bd)
      if bm > 0:
        print("  - Boost Multistrike: ", bm)
      if hc > 0:
        print("  - House Crit Chance: ", hc)
      if hd > 0:
        print("  - House Crit Damage: ", hd)
      if hm > 0:
        print("  - House Multistrike: ", hm)
    print()


  def boost_cost(self, critChance, critDamage, multistrike):
    net_chc = critChance - self.b_chc
    net_chd = critDamage - self.b_chd
    net_multi = multistrike - self.b_multi
    
    chc_cost = 0
    if net_chc > 0:
      for i in range(net_chc):
        chc_cost += ((self.b_chc + i) * 10) + 10

    chd_cost = 0		
    if net_chd > 0:
      for i in range(net_chd):
        chd_cost += ((self.b_chd + i) * 10) + 10

    multi_cost = 0		
    if net_multi > 0:
      for i in range(net_multi):
        multi_cost += ((self.b_multi + i) * 10) + 10      
				
    total_relics = self.p_relics - (chc_cost + chd_cost + multi_cost)
      
    if total_relics < 0:
      total_price = abs(total_relics * self.m_relics)
    else:
      total_price = 0
        
    return total_price        


  def house_cost(self, critChance, critDamage, multistrike):       
    net_chc = critChance - self.h_chc
    net_chd = critDamage - self.h_chd
    net_multi = multistrike - self.h_multi
        
    chc_cost = 0    
    if net_chc > 0:
      for i in range(net_chc):
        chc_cost += int(1000+(1000*((self.h_chc + i)**1.25)))

    chd_cost = 0
    if net_chd > 0:
      for i in range(net_chd):
        chd_cost += int(1000+(1000*((self.h_chc + i)**1.25)))

    multi_cost = 0      	
    if net_multi > 0:
      for i in range(net_multi):
        multi_cost += int(1000+(1000*((self.h_chc + i)**1.25)))
      

    total_meat = self.p_meat - (chc_cost + chd_cost + multi_cost)
    total_iron = self.p_iron - (chc_cost + chd_cost + multi_cost)
    total_wood = self.p_wood - (chc_cost + chd_cost + multi_cost)
    total_stone = self.p_stone - (chc_cost + chd_cost + multi_cost)
        
    if total_meat < 0:
      meat_price = abs(total_meat * self.m_meat)
    else:
      meat_price = 0
			
    if total_iron < 0:
      iron_price = abs(total_iron * self.m_iron)
    else:
      iron_price = 0
            
    if total_wood < 0:
      wood_price = abs(total_wood * self.m_wood)
    else:
      wood_price = 0
        
    if total_stone < 0:
      stone_price = abs(total_stone * self.m_stone)
    else:
      stone_price = 0
            
    total_price = (meat_price + iron_price + wood_price + stone_price)
        
    return total_price


  def dmg_value(self, bc, bd, bm, hc, hd, hm):
    chc = self.b_chc + self.h_chc + bc + hc
    chd = self.b_chd + self.h_chd + bd + hd
    multi = self.b_multi + self.h_multi + bm + hm
    base_chc = self.b_chc + self.h_chc
    base_chd = self.b_chd + self.h_chd
    base_multi = self.b_multi + self.h_multi
    
    damage = ((1 + (chc * (0.2 + chd))) * (1 + multi)) / ((1 + (base_chc * (0.2 + base_chd))) * (1 + base_multi)) - 1
    return damage

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
      if total_cost <= self.budget:
        result.append((action, (bc, bd, bm, hc, hd, hm)))
        this_dmg = self.dmg_value(bc, bd, bm, hc, hd, hm)
        if this_dmg > self.goal: 
          self.goal = this_dmg
          self.final = (bc, bd, bm, hc, hd, hm)
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
        self.print()
        return

      # Choose a node from the frontier
      node = frontier.remove()
      self.num_explored += 1


      # Mark node as explored
      self.explored.add(node.state)

      # Add neighbors to frontier
      for action, state in self.neighbors(node.state):
        if not frontier.contains_state(state) and state not in self.explored:
          child = Node(state=state, parent=node, action=action)
          frontier.add(child)

  def shopping_list(self):
    b_chc = self.final[0] - self.b_chc 
    b_chd = self.final[1] - self.b_chd
    b_multi = self.final[2] - self.b_multi
    h_chc = self.final[3] - self.h_chc
    h_chd = self.final[4] - self.h_chd 
    h_multi = self.final[5] - self.h_multi

    b_chc_cost = 0
    if b_chc > 0:
      for i in range(b_chc):
        b_chc_cost += ((self.b_chc + i) * 10) + 10

    b_chd_cost = 0		
    if b_chd > 0:
      for i in range(b_chd):
        b_chd_cost += ((self.b_chd + i) * 10) + 10

    b_multi_cost = 0		
    if b_multi > 0:
      for i in range(b_multi):
        b_multi_cost += ((self.b_multi + i) * 10) + 10      
				
    total_relics = self.p_relics - (b_chc_cost + b_chd_cost + b_multi_cost)
      
    if total_relics < 0:
      to_buy_relics = abs(total_relics)
      relics_total_price = abs(total_relics * self.m_relics)
    else:
      to_buy_relics = 0
      relics_total_price = 0
        
    h_chc_cost = 0    
    if h_chc > 0:
      for i in range(h_chc):
        h_chc_cost += int(1000+(1000*((self.h_chc + i)**1.25)))

    h_chd_cost = 0
    if h_chd > 0:
      for i in range(h_chd):
        h_chd_cost += int(1000+(1000*((self.h_chc + i)**1.25)))

    h_multi_cost = 0      	
    if h_multi > 0:
      for i in range(h_multi):
        h_multi_cost += int(1000+(1000*((self.h_chc + i)**1.25)))
      

    total_meat = self.p_meat - (h_chc_cost + h_chd_cost + h_multi_cost)
    total_iron = self.p_iron - (h_chc_cost + h_chd_cost + h_multi_cost)
    total_wood = self.p_wood - (h_chc_cost + h_chd_cost + h_multi_cost)
    total_stone = self.p_stone - (h_chc_cost + h_chd_cost + h_multi_cost)
    
    if total_meat < 0:
      to_buy_meat = abs(total_meat)
      meat_price = abs(total_meat * self.m_meat)
    else:
      to_buy_meat = 0
      meat_price = 0
			
    if total_iron < 0:
      to_buy_iron = abs(total_iron)
      iron_price = abs(total_iron * self.m_iron)
    else:
      to_buy_iron = 0
      iron_price = 0
            
    if total_wood < 0:
      to_buy_wood = abs(total_wood)
      wood_price = abs(total_wood * self.m_wood)
    else:
      to_buy_wood = 0
      wood_price = 0
        
    if total_stone < 0:
      to_buy_stone = abs(total_stone)
      stone_price = abs(total_stone * self.m_stone)
    else:
      to_buy_stone = 0
      stone_price = 0
            
    mats_total_price = (meat_price + iron_price + wood_price + stone_price)

    total_price = mats_total_price + relics_total_price

    if total_price > 0:
      print("Shopping List:")
      print()
      if to_buy_relics > 0:
        print("  - Relics: ", to_buy_relics)
      if to_buy_meat > 0:
        print("  - Meat: ", to_buy_meat)
      if to_buy_iron > 0:
        print("  - Iron: ", to_buy_iron)
      if to_buy_wood > 0:
        print("  - Wood: ", to_buy_wood)
      if to_buy_stone > 0:
        print("  - Stone: ", to_buy_stone)
      print()
      print("Gold spent: ", total_price)
      print()

#if len(sys.argv) != 2:
#    sys.exit("Usage: python queslar_tools.py budget")

q = Queslar(300000)
print("Current:")
q.print()
print("Solving...")
q.solve()
q.shopping_list()
print("States Explored:", q.num_explored)
