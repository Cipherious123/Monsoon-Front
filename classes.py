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

    def flood(self):
        """
        Apply consequences of flooding to this sector.
        Should be called once per turn after flood propagation.
        """

        if self.flooded <= 0:
            return 0  # no flood, no consequences

        absorbed = self.flooded * self.absorption
        self.flooded -= absorbed

        # Poor infra collapses faster under flood pressure
        infra_damage = self.flooded * (1.2 - self.infra / 100)
        self.infra -= infra_damage
        self.infra = max(self.infra, 0)

        health_damage = self.flooded * 0.6
        self.health -= health_damage
        self.health = max(self.health, 0)

        # Deaths scale with flood level, population,
        # and inversely with infra & health
        vulnerability = (2 - (self.infra + self.health + self.vulnerability) / 100)
        death_rate = 0.0005 * self.flooded * vulnerability

        new_deaths = int(self.population * death_rate)
        new_deaths = min(new_deaths, self.population)

        self.population -= new_deaths
        self.deaths += new_deaths

        political_loss = (
            new_deaths * 0.01 +
            infra_damage * 0.3 +
            self.flooded * 0.5
        )

        self.political_power -= political_loss
        self.political_power = max(self.political_power, 0)


class river:
    def __init__(self, name, path, terminal):
        self.name = name
        self.path = path #[{sector:, width:, max_height, height}, {}...]
        self.terminal = terminal #(river, sector index in terminal river's path)
    
    def add_water(self, sector, amount):
        """
        Increases water level in a certain sector of the river by amount.
        """
        for path_var in self.path:
            if sector == path_var["sector"]:
                path_var["height"] += amount / path_var["width"]
                break
        
    def flood_propagate(self):
        """
        Propagates flood water along the river path.
        Called once per turn.
        """
        BASE_MAX_TRANSFER_FRACTION = 0.25
        BASE_FLOW_COEFFICIENT = 0.6
        FLOOD_SPILL_FACTOR = 0.3

        # --- INTERNAL RIVER PROPAGATION ---
        for i in range(len(self.path) - 1):
            current = self.path[i]
            downstream = self.path[i + 1]

            cur_h = current["height"]
            down_h = downstream["height"]

            # No flow if no pressure
            if cur_h <= down_h:
                continue
            
            altitude_modifier = (current["sector"].altitude - downstream["sector"].altitude) / 400
            max_fraction_transfer = (
                cur_h * BASE_MAX_TRANSFER_FRACTION * altitude_modifier
            )

            raw_transfer = (
                (cur_h - down_h) * BASE_FLOW_COEFFICIENT * altitude_modifier
            )

            # --- CRITICAL INVARIANT ---
            # Never allow gradient reversal
            max_safe_transfer = (cur_h - down_h) / 2

            transfer = min(
                max_fraction_transfer,
                raw_transfer,
                max_safe_transfer
            )

            if transfer <= 0:
                continue

            current["height"] -= transfer
            downstream["height"] += transfer

            # Spill if downstream exceeds capacity
            overflow = max(0, downstream["height"] - downstream["max_height"])
            if overflow > 0:
                spilled = overflow * FLOOD_SPILL_FACTOR
                downstream["height"] -= spilled
                downstream["sector"].flooded += spilled*current["width"]

        # --- TERMINAL HANDLING ---
        terminal_river, terminal_sector = self.terminal
        tail = self.path[-1]

        if tail["height"] <= 0:
            return

        # CASE 1: Tributary joins another river
        if terminal_river is not None:
            target = terminal_river.path[0]

            tail_h = tail["height"]
            target_h = target["height"]

            if tail_h > target_h:
                altitude_modifier = (tail["sector"].altitude - target_h.altitude) / 400

                max_fraction_transfer = (
                    tail_h * BASE_MAX_TRANSFER_FRACTION * altitude_modifier
                )

                raw_transfer = (
                    (tail_h - target_h)
                    * BASE_FLOW_COEFFICIENT
                    * altitude_modifier
                )

                max_safe_transfer = (tail_h - target_h) / 2

                transfer = min(
                    max_fraction_transfer,
                    raw_transfer,
                    max_safe_transfer
                )

                if transfer > 0:
                    tail["height"] -= transfer
                    target["height"] += transfer

                    overflow = max(0, target["height"] - target["max_height"])
                    if overflow > 0:
                        spilled = overflow * FLOOD_SPILL_FACTOR 
                        target["height"] -= spilled
                        target["sector"].flooded += spilled * tail["width"]

class dam:
    def __init__(self, name, capacity, cap_used, cost, fail_prob, river, sector, state):
        self.name = name
        self.capacity = capacity
        self.cap_used = cap_used
        self.cost = cost
        self.fail_prob = fail_prob
        self.river = river
        self.sector = sector
        self.state = state

    def control(self):
        pass

    def fail(self):
        prob = self.fail_prob * self.cap_used / self.capacity
        chance = rng.chance(prob)
        if chance:
            self.river.add_water(self.sector_name, self.capacity)
            self.state = "Failed"



game_map = {"Guwahati" : sector("Guwahati", 3000000, 100, 30, 100, 0, 100, (0,0))}
rivers = {"Brahmaputra": river("Brahmaputra", {"Guwahati": ()}, ())}