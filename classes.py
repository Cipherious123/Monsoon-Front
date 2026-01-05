import random

class GameRNG:
    def __init__(self, seed):
        self.rng = random.Random(seed)

    def chance(self, p):
        return self.rng.random() < p

class sector:
    def __init__(self, population, rivers, power, absorption, infra, slope, health):
        self.population = population
        self.rivers = rivers
        self.power = power
        self.absorption = absorption
        self.infra = infra
        self.slope = slope
        self.flooded = 0
        self.health = health
        self.deaths = 0