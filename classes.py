import random

#sprites
map_spt = "templates/map.jpg"
boat_spt = "templates/boat.png"
town_spt = "templates/city.png"
village_spt = "templates/villade.png"
heli_spt = "templates/heli.png"
flood_spt = "templates/flood.png"
dam_spt = "templates/dam.png"
pot_dam_spt = "templates/valley.png"

class GameRNG:
    def __init__(self, seed):
        self.rng = random.Random(seed)

    def chance(self, p):
        return self.rng.random() < p

rng = GameRNG(8)
class sector:
    def __init__(self, name,  population, power, absorption, infra, altitude, coords):
        self.name = name
        self.population = population
        self.power = power
        self.absorption = absorption
        self.infra = infra
        self.altitude = altitude
        self.flooded = 0
        self.health = 1
        self.deaths = 0
        self.coords = coords
        self.evac = 0

    def flood(self, game_turn):
        """
        Apply consequences of flooding to this sector.
        Should be called once per turn after flood propagation.
        """

        if self.flooded <= 0:
            return 0,0  # no flood, no consequences

        # Poor infra collapses faster under flood pressure
        infra_damage = self.flooded * (1.2 - self.infra / 100)
        self.infra -= infra_damage
        self.infra = max(self.infra, 0)

        health_damage = self.flooded * 0.6
        self.health -= health_damage
        self.health = max(self.health, 0)

        # Deaths scale with flood level, population,
        # and inversely with infra & health
        vulnerability = (2 - self.infra + self.health) / 2
        death_rate = 0.0005 * self.flooded * vulnerability

        new_deaths = int(self.population * death_rate)
        new_deaths = min(new_deaths, self.population)

        self.population -= new_deaths
        self.deaths += new_deaths

        political_loss = (
            infra_damage * self.power * 10 * 2**(-2/game_turn)
        )

        morale_loss = new_deaths * 0.01 * 2**(-2/game_turn)
        return political_loss, morale_loss


    def evacuation(self):
        """
        Progress evacuation for one turn.
        Reduces population in this sector and redistributes evacuees
        to nearby non-evacuated sectors based on distance.
        """

        if self.evac <= 0 or self.population <= 0:
            return 

        # --- Time decay (front-loaded evacuation) ---
        base_fraction = 0.45 / self.evac

        # ---Constraint ---
        infra_factor = max(0.0, min(1.0, self.infra))
        flood_factor = 1 / (1 + max(0, self.flooded))

        evac_fraction = base_fraction * infra_factor * flood_factor
        evac_fraction = min(evac_fraction, 0.6)

        evacuees = int(self.population * evac_fraction)
        evacuees = min(evacuees, self.population)

        if evacuees <= 0:
            self.evac += 1
            return 
        self.population -= evacuees

        # --- Find valid destination sectors ---
        sx, sy = self.coords
        candidates = []

        for sector in game_map.values():
            if sector is self:
                continue
            if sector.evac > 0:
                continue

            dx = sector.coords[0] - sx
            dy = sector.coords[1] - sy
            dist = (dx**2 + dy**2)**0.5

            if dist > 0:
                candidates.append((sector, dist))

        # --- Redistribute evacuees ---
        if candidates:
            weights = [1 / dist for _, dist in candidates]
            total_weight = sum(weights)

            distributed = 0

            for (sector, _), weight in zip(candidates, weights):
                share = int(evacuees * (weight / total_weight))
                sector.population += share
                distributed += share

            # Handle rounding leftovers → Guwahati
            leftover = evacuees - distributed
            if leftover > 0:
                game_map["Guwahati"].population += leftover

        self.evac += 1

    def absorb(self):
        self.flooded -= min(2 * self.absorption, self.flooded * self.absorption)


class river:
    def __init__(self, name, path, terminal):
        self.name = name
        self.path = path #[{sector:, width:, max_height, height, dam}, {}...]
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
        Called once per turn. Dams provide powerful flood control.
        """
        BASE_MAX_TRANSFER_FRACTION = 0.25
        BASE_FLOW_COEFFICIENT = 0.6
        FLOOD_SPILL_FACTOR = 0.3
        
        # Dam mechanics
        DAM_EMERGENCY_THRESHOLD = 0.95  # Auto-release at 95% capacity
        DAM_CONTROLLED_RELEASE_THRESHOLD = 0.70  # Smart release above 70%
        DAM_EMERGENCY_RELEASE_RATE = 0.5  # Release 50% when critical
        DAM_FLOW_SMOOTHING_RATE = 0.20  # Gradual, controlled release rate
        DAM_DOWNSTREAM_PROTECTION_FACTOR = 0.6  # Released water is 60% of what would naturally flow

        # --- INTERNAL RIVER PROPAGATION ---
        for i in range(len(self.path) - 1):
            current = self.path[i]
            downstream = self.path[i + 1]

            cur_h = current["height"]
            down_h = downstream["height"]

            # --- DAM HANDLING AT CURRENT NODE ---
            if "dam" in current and current["dam"] is not None:
                dam = current["dam"]
                
                # Calculate what would naturally flow without the dam
                natural_flow = cur_h  # All water above this node
                
                # Dam captures incoming flood water
                space_available = dam.capacity - dam.stored_water
                captured = min(natural_flow, space_available)
                
                dam.stored_water += captured
                current["height"] = cur_h - captured
                
                # Calculate dam fill percentage
                fill_ratio = dam.stored_water / dam.capacity if dam.capacity > 0 else 0
                
                # Smart release logic - controlled and strategic
                controlled_release = 0
                
                # Player manual release (highest priority)
                if dam.manual_release_amount > 0:
                    controlled_release = min(dam.manual_release_amount, dam.stored_water)
                    dam.release_reason = "MANUAL"
                    dam.auto_released_this_turn = False
                
                # Emergency auto-release (prevents dam failure)
                elif fill_ratio >= DAM_EMERGENCY_THRESHOLD:
                    controlled_release = dam.stored_water * DAM_EMERGENCY_RELEASE_RATE
                    dam.release_reason = "EMERGENCY"
                    dam.auto_released_this_turn = True
                
                # Intelligent flow smoothing (prevents downstream flooding)
                elif fill_ratio >= DAM_CONTROLLED_RELEASE_THRESHOLD:
                    # Calculate safe downstream capacity
                    downstream_available = downstream["max_height"] - down_h
                    
                    # Release gradually to prevent downstream flooding
                    # This is MUCH less than the natural flow would have been
                    safe_release = min(
                        dam.stored_water * DAM_FLOW_SMOOTHING_RATE,
                        downstream_available * 0.8  # Only use 80% of downstream capacity
                    )
                    controlled_release = safe_release
                    dam.release_reason = "CONTROLLED"
                    dam.auto_released_this_turn = True
                
                else:
                    dam.auto_released_this_turn = False
                    dam.release_reason = "HOLDING"
                
                # Apply controlled release - this is modulated, not a raw dump
                if controlled_release > 0:
                    controlled_release = min(controlled_release, dam.stored_water)
                    dam.stored_water -= controlled_release
                    
                    # KEY BENEFIT: Released water flows more gently than natural flood
                    # This represents controlled gates, spillways, etc.
                    modulated_release = controlled_release * DAM_DOWNSTREAM_PROTECTION_FACTOR
                    current["height"] += modulated_release
                    
                    # The "lost" water represents evaporation, seepage, absorption
                    # This is a major benefit - dams actually reduce total flood volume
                    dam.water_absorbed_this_turn = controlled_release - modulated_release
                else:
                    dam.water_absorbed_this_turn = 0
                
                # Reset manual release for next turn
                dam.manual_release_amount = 0
                
                # Update cur_h for downstream flow calculation
                cur_h = current["height"]
                
                # Track dam performance statistics
                dam.total_water_captured += captured
                dam.total_water_absorbed += dam.water_absorbed_this_turn

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

            # Spill if downstream exceeds capacity (more severe without dam protection)
            overflow = max(0, downstream["height"] - downstream["max_height"])
            if overflow > 0:
                spilled = overflow * FLOOD_SPILL_FACTOR
                downstream["height"] -= spilled
                downstream["sector"].flooded += spilled * current["width"]

        # --- TERMINAL HANDLING ---
        if not self.terminal:
            return
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
                altitude_modifier = (tail["sector"].altitude - target["sector"].altitude) / 400

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
    def __init__(self, name, capacity, cap_used, cost, fail_prob, river, sector, state, time_to_build):
        self.name = name
        self.capacity = capacity
        self.cap_used = cap_used
        self.cost = cost
        self.fail_prob = fail_prob
        self.river = river
        self.sector = sector
        self.state = state
        self.build_time = time_to_build

    def control(self):
        pass

    def fail(self):
        prob = self.fail_prob * self.cap_used / self.capacity
        chance = rng.chance(prob)
        if chance:
            self.river.add_water(self.sector.name, self.capacity)
            self.state = "Failed"
            print(f"Oh no! {self.name} has failed! All water released")


lst = [sector("Upper Siang", 35000, 0.20, 0.75, 0.20, 3500, (0,0)),
sector( "East Siang", 100000, 0.30, 0.70, 0.30, 300, (0,0)),
sector( "Upper Dibang Valley", 8000, 0.15, 0.80, 0.15, 4000, (2600,260)),
sector( "Lower Dibang Valley", 60000, 0.25, 0.70, 0.25, 300, (0,0)),
sector( "Lohit", 150000, 0.35, 0.65, 0.10, 400, (0,0)),
sector( "Lower Subansiri", 83000, 0.10, 0.68, 0.28, 600, (0,0)),

sector( "Tinsukia", 1300000, 0.75, 0.40, 0.65, 120, (0,0)),
sector( "Dibrugarh", 1320000, 0.80, 0.38, 0.70, 110, (0,0)),
sector( "Dhemaji", 690000, 0.35, 0.55, 0.30, 105, (0,0)),
sector( "Lakhimpur", 1050000, 0.40, 0.50, 0.35, 100, (0,0)),

sector( "Jorhat", 1100000, 0.60, 0.45, 0.55, 90, (0,0)),
sector( "Golaghat", 1060000, 0.55, 0.48, 0.50, 95, (0,0)),
sector( "Sonitpur", 1900000, 0.65, 0.42, 0.55, 80, (0,0)),
sector( "Biswanath", 610000, 0.45, 0.50, 0.40, 85, (0,0)),

sector( "Nagaon", 2800000, 0.60, 0.40, 0.50, 70, (0,0)),
sector( "Morigaon", 960000, 0.45, 0.52, 0.40, 65, (0,0)),
sector( "Guwahati", 1200000, 0.95, 0.20, 0.90, 55, (0,0)),
sector( "Majuli", 170000, 0.30, 0.60, 0.25, 85, (0,0))
]
game_map = {}
boats = {}
for l in lst:
    #coords = (2600,260)
    #l.coords = coords
    game_map[l.name] = l
    boats[l.name] = {"inactive": 0, "active": 0, "locked": 0}

boats["Guwahati"]["active"] = 1000

Bigriver = river(
        name="Brahmaputra",
        path=[
            # ARUNACHAL PRADESH (Mountainous / Upper reaches)
            {"sector": game_map["Upper Siang"], "width": 180, "max_height": 14, "height": 7},
            {"sector": game_map["East Siang"],  "width": 260, "max_height": 16, "height": 9},

            # ASSAM – ENTRY ZONE (Upper Assam foothills)
            {"sector": game_map["Tinsukia"],    "width": 600, "max_height": 22, "height": 14},
            {"sector": game_map["Dhemaji"],     "width": 450, "max_height": 20, "height": 12},
            {"sector": game_map["Dibrugarh"],   "width": 750, "max_height": 24, "height": 16},

            # ASSAM – CENTRAL ASSAM (Wide floodplains)
            
            {"sector": game_map["Jorhat"],      "width": 1450, "max_height": 34, "height": 26},
            {"sector": game_map["Lakhimpur"],   "width": 900, "max_height": 26, "height": 18},
            {"sector": game_map["Majuli"],      "width": 1550, "max_height": 35, "height": 27},
            {"sector": game_map["Golaghat"],    "width": 1350, "max_height": 32, "height": 24},
            {"sector": game_map["Biswanath"],   "width": 1050, "max_height": 28, "height": 20},
            {"sector": game_map["Sonitpur"],    "width": 1200, "max_height": 30, "height": 22},

            # ASSAM – LOWER ASSAM (Very wide, high flood risk)
            {"sector": game_map["Nagaon"],      "width": 1650, "max_height": 36, "height": 28},
            {"sector": game_map["Morigaon"],    "width": 1750, "max_height": 38, "height": 30},
            {
                "sector": game_map["Guwahati"],
                "width": 2000,
                "max_height": 42,
                "height": 34
            },
        ],
        terminal=None
    )

rivers = {
    "Brahmaputra": Bigriver,

    "Dibang": river(
        name="Dibang",
        path=[
            {"sector": game_map["Upper Dibang Valley"], "width": 120, "max_height": 12, "height": 6, },
            {"sector": game_map["Lower Dibang Valley"], "width": 200, "max_height": 14, "height": 8},
        ],
        terminal=(Bigriver, 1)  # joins at east siang
    ),

    "Lohit": river(
        name="Lohit",
        path=[
            {"sector": game_map["Lohit"],    "width": 140, "max_height": 13, "height": 6},
        ],
        terminal=(Bigriver, 2)  # joins near Tinsukia
    ),

    "Subansiri": river(
        name="Subansiri",
        path=[
            {"sector": game_map["Lower Subansiri"], "width": 220, "max_height": 15, "height": 9,},
        ],
        terminal=(Bigriver, 6)
    ),
}

pot_dams_lst = [  
    dam(name="Lohit Dam",
        capacity=800,
        cap_used=0,
        cost=650,
        fail_prob=0.02,   # risky fast-build dam
        river=rivers["Lohit"],
        sector=game_map["Lohit"],
        state="Not Built",
        time_to_build = 1)   
    ,

    dam(
        name="Siang Dam",
        capacity=2500,
        cap_used=0,
        cost=900,
        fail_prob=0.007,  # very stable but long build
        river=rivers["Brahmaputra"],
        sector=game_map["East Siang"],
        state="Not Built",
        time_to_build = 5
    ),

    dam(
        name="Majuli dam",
        capacity=500,
        cap_used=0,
        cost=400,
        fail_prob=0.025,  # fragile early-game crutch
        river=rivers["Brahmaputra"],
        sector=game_map["Majuli"],
        state="Not Built",
        time_to_build = 1
    )]
pot_dams = {}
for dam_ in pot_dams_lst:
    pot_dams[dam_.name] = dam_

dams_lst = [
    dam(
        name="LSD",
        capacity=2000,
        cap_used=900,     # already holding monsoon inflow
        cost=None,
        fail_prob=0.004,  # old
        river=rivers["Subansiri"],
        sector=game_map["Lower Subansiri"],
        state="Built",
        time_to_build=None
    ),
]
dams = {}
for dam_ in dams_lst:
    dams[dam_.name] = dam_

rivers["Subansiri"].path[1]["dam"] = dams["LSD"]