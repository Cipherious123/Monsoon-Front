import random

#sprites
map_spt = "s"
boat_spt = "s"

class GameRNG:
    def __init__(self, seed):
        self.rng = random.Random(seed)

    def chance(self, p):
        return self.rng.random() < p

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

game_map = {sector("Guwahati", 3000000, 100, 30, 100, 0, 100): (0,0)}