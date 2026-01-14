import random

#sprites
map_spt = "s"
boat_spt = "s"

class GameRNG:
    def __init__(self, seed):
        self.rng = random.Random(seed)

    def chance(self, p):
        return self.rng.random() < p

rng = GameRNG(8)
class sector:
    def __init__(self, name,  population, power, absorption, infra, slope, health, coords):
        self.name = name
        self.population = population
        self.power = power
        self.absorption = absorption
        self.infra = infra
        self.slope = slope
        self.flooded = 0
        self.health = health
        self.deaths = 0
        self.coords = coords

class river:
    def __init__(self, name, path):
        self.name = name
        self.path = {}
        self.path.fromkeys(path, 0.5)
    
    def flood(self):
        pass


class dam:
    def __init__(self, name, capacity, cap_used, cost, fail_prob, river, coords, state):
        self.name = name
        self.capacity = capacity
        self.cap_used = cap_used
        self.cost = cost
        self.fail_prob = fail_prob
        self.river = river
        self.coords = coords
        self.state = state

    def fail(self):
        prob = self.fail_prob * self.cap_used / self.capacity
        chance = rng.chance(prob)
        if chance:
            self.river.flood(self.capacity, self.coords)
            self.state = "Failed"



game_map = {sector("Guwahati", 3000000, 100, 30, 100, 0, 100): (0,0)}