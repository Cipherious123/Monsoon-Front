import random

#sprites
map_spt = "templates/mapp.jpg"
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
class Sector:
    """
    Basic Unit of the Map - Has name,  population, power, absorption, infra, altitude, coords
    """
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
        self.river_in = [] #(river, index of sector in it's path variable)
        
    def flood(self, game_turn, dam_failed):
        """
        Apply consequences of flooding to this sector.
        Should be called once per turn after flood propagation.
        Scales difficulty based on game turn and dam failure status.
        """
        
        if self.flooded <= 0:
            return 0, 0  # no flood, no consequences

        # Early-game protection: reduce severity in first few turns
        # Scales from 0.3x damage at turn 1 to 1.0x damage at turn 6+
        turn_scaling = min(1.0, 0.3 + (game_turn - 1) * 0.14)
        
        # Dam failure is catastrophic - apply full damage immediately
        # Otherwise use turn scaling
        severity_multiplier = 1.0 if dam_failed else turn_scaling
        
        # Poor infra collapses faster under flood pressure
        infra_damage = self.flooded * (1.2 - self.infra / 100) * severity_multiplier
        self.infra -= infra_damage
        self.infra = max(self.infra, 0)

        health_damage = self.flooded * 0.6 * severity_multiplier
        self.health -= health_damage
        self.health = max(self.health, 0)

        # Deaths scale with flood level, population,
        # and inversely with infra & health
        vulnerability = (2 - self.infra / 100 + self.health / 100) / 2
        
        # Reduced base death rate, with additional protection early game
        base_death_rate = 0.0003  # Reduced from 0.0005
        death_rate = base_death_rate * self.flooded * vulnerability * severity_multiplier
        
        new_deaths = int(self.population * death_rate)
        new_deaths = min(new_deaths, self.population)

        self.population -= new_deaths
        self.deaths += new_deaths

        # Political loss also scales with game progression
        political_loss = (infra_damage * self.power / 100) * 0.8  # Reduced by 20%
        
        # Morale loss reduced and scaled
        morale_loss = new_deaths * 0.005 * severity_multiplier  # Reduced from 0.01

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


class River:
    def __init__(self, name, path, terminal, base_flow=5.0):
        self.name = name
        self.path = path  # [{sector:, width:, max_height, height, dam}, {}...]
        self.terminal = terminal  # (river, sector index in terminal river's path)
        self.base_flow = base_flow  # Continuous water spawning rate at source
    
    def spawn_source_water(self):
        """
        Continuously adds water to the first sector (river source).
        Called once per turn to simulate natural water flow.
        """
        if len(self.path) > 0:
            source = self.path[0]
            source["height"] += self.base_flow / source["width"]
            
            # Cap at max height with overflow
            overflow = max(0, source["height"] - source["max_height"])
            if overflow > 0:
                source["height"] = source["max_height"]
                source["sector"].flooded += overflow * source["width"]
    
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
        FLOOD_SPILL_FACTOR = 0.333
        
        # Dam mechanics
        DAM_EMERGENCY_THRESHOLD = 0.95  # Auto-release at 95% capacity
        DAM_TARGET_FILL = 0.90  # Reduce to 90% when emergency triggered

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
                if cur_h <= down_h:
                    natural_flow = 0
                else:
                    altitude_modifier = (current["sector"].altitude - downstream["sector"].altitude) / 400
                    max_fraction_transfer = cur_h * BASE_MAX_TRANSFER_FRACTION * altitude_modifier
                    raw_transfer = (cur_h - down_h) * BASE_FLOW_COEFFICIENT * altitude_modifier
                    max_safe_transfer = (cur_h - down_h) / 2
                    
                    natural_flow = min(max_fraction_transfer, raw_transfer, max_safe_transfer)
                
                # Dam captures incoming flood water
                space_available = dam.capacity - dam.cap_used
                captured = min(natural_flow, space_available)
                
                dam.cap_used += captured
                current["height"] -= captured
                
                if captured > 0:
                    print(f"Dam captured {captured:.1f} units of flood water")
                
                # Calculate dam fill percentage
                fill_ratio = dam.cap_used / dam.capacity if dam.capacity > 0 else 0
                
                # --- MANAGED RELEASE SYSTEM ---
                # Player-configurable gradual release based on dam strategy
                managed_release = dam.calculate_release(fill_ratio)
                
                if managed_release > 0:
                    actual_release = min(managed_release, dam.cap_used)
                    dam.cap_used -= actual_release
                    current["height"] += actual_release
                    
                    if dam.release_mode != "hold":
                        print(f"🌊 {dam.name} controlled release: {actual_release:.1f} units ({dam.release_mode} mode, {fill_ratio*100:.1f}% full)")
                
                # Emergency auto-release (overrides managed release)
                if fill_ratio >= DAM_EMERGENCY_THRESHOLD:
                    # Release enough to bring capacity down to 90%
                    target_capacity = dam.capacity * DAM_TARGET_FILL
                    emergency_release = dam.cap_used - target_capacity
                    emergency_release = max(0, emergency_release)  # Safety check
                    
                    if emergency_release > 0:
                        dam.cap_used -= emergency_release
                        current["height"] += emergency_release
                        print(f"⚠️ EMERGENCY AUTO-RELEASE at {dam.name}: {emergency_release:.1f} units released (Dam at {fill_ratio*100:.1f}% -> {DAM_TARGET_FILL*100:.1f}%)")
                
                # Update cur_h for downstream flow calculation
                cur_h = current["height"]

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
                downstream["sector"].flooded += spilled * current["width"]

        # --- TERMINAL HANDLING --- 
        if self.terminal == None:
            return
        
        terminal_river, terminal_sector_ind = self.terminal
        tail = self.path[-1]
        target = terminal_river.path[terminal_sector_ind]

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


class Dam:
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
        
        # --- NEW: Configurable Release Settings ---
        self.release_mode = "conservative"  # Options: "hold", "conservative", "balanced", "aggressive"
        self.target_fill_level = 0.70  # Target percentage to maintain (70%)
        self.min_release_threshold = 0.30  # Don't release below this fill level
        self.custom_release_rate = None  # Optional: fixed release rate override
    
    def set_release_mode(self, mode):
        """
        Player configures dam release strategy.
        
        Modes:
        - "hold": No automatic release (only emergency)
        - "conservative": Slow, steady release starting at 50% capacity
        - "balanced": Moderate release starting at 40% capacity
        - "aggressive": Fast release starting at 30% capacity
        - "custom": Use custom_release_rate value
        """
        valid_modes = ["hold", "conservative", "balanced", "aggressive", "custom"]
        if mode in valid_modes:
            self.release_mode = mode
            print(f"{self.name} release mode set to: {mode}")
        else:
            print(f"Invalid mode. Choose from: {valid_modes}")
    
    def set_target_fill(self, target_percentage):
        """
        Set the target fill level the dam tries to maintain (0.0 to 1.0).
        Dam will release water to gradually reach this level.
        """
        self.target_fill_level = max(0.0, min(1.0, target_percentage))
        print(f"{self.name} target fill level set to: {self.target_fill_level*100:.1f}%")
    
    def set_custom_release_rate(self, rate):
        """
        Set a fixed release rate (units per turn) for "custom" mode.
        """
        self.custom_release_rate = max(0, rate)
        print(f"{self.name} custom release rate set to: {rate:.1f} units/turn")
    
    def calculate_release(self, fill_ratio):
        """
        Calculates how much water to release this turn based on current strategy.
        
        Returns: amount of water to release (in units)
        """
        if self.release_mode == "hold":
            return 0
        
        if self.release_mode == "custom" and self.custom_release_rate is not None:
            return self.custom_release_rate
        
        # Don't release if below minimum threshold
        if fill_ratio < self.min_release_threshold:
            return 0
        
        # Calculate excess above target
        excess_ratio = fill_ratio - self.target_fill_level
        
        # Only release if above target
        if excess_ratio <= 0:
            return 0
        
        # Base release scales with how far above target we are
        excess_water = excess_ratio * self.capacity
        
        # Mode-specific release rates (fraction of excess per turn)
        if self.release_mode == "conservative":
            # Release 5% of excess per turn (slower, smoother)
            release_fraction = 0.05
        elif self.release_mode == "balanced":
            # Release 10% of excess per turn (moderate)
            release_fraction = 0.10
        elif self.release_mode == "aggressive":
            # Release 20% of excess per turn (faster)
            release_fraction = 0.20
        else:
            release_fraction = 0.10  # Default to balanced
        
        release_amount = excess_water * release_fraction
        
        # Ensure we don't release more than available
        return min(release_amount, self.cap_used)

    def control(self):
        """
        Manual control interface for the player.
        Can be expanded with additional control options.
        """
        pass

    def fail(self):
        """
        Dam failure check based on capacity usage.
        """
        prob = self.fail_prob * self.cap_used / self.capacity
        chance = rng.chance(prob)
        if chance:
            self.river.add_water(self.sector.name, self.capacity)
            self.state = "Failed"
            print(f"Oh no! {self.name} has failed! All water released")
            return True
        return False

lst = [Sector("Upper Siang", 35000, 0.20, 0.75, 0.20, 3500, (2000,500)),
Sector( "East Siang", 100000, 0.30, 0.70, 0.30, 300, (2222,800)),
Sector( "Upper Dibang Valley", 8000, 0.15, 0.80, 0.15, 4000, (2600,260)),
Sector( "Lower Dibang Valley", 60000, 0.25, 0.70, 0.25, 300, (2600,600)),
Sector( "Lohit", 150000, 0.35, 0.65, 0.10, 400, (2850,750)),
Sector( "Lower Subansiri", 83000, 0.10, 0.68, 0.28, 600, (1517,1222)),
Sector("Upper Subansiri", 35000, 0.20, 0.72, 0.22, 2500, (1400,800)),

Sector( "Tinsukia", 1300000, 0.75, 0.40, 0.65, 120, (2500,1100)),
Sector( "Dibrugarh", 1320000, 0.80, 0.38, 0.70, 110, (2200,1300)),
Sector( "Dhemaji", 690000, 0.35, 0.55, 0.30, 105, (2100,1050)),
Sector( "Lakhimpur", 1050000, 0.40, 0.50, 0.35, 100, (1750,1300)),

Sector( "Jorhat", 1100000, 0.60, 0.45, 0.55, 90, (1750,1750)),
Sector( "Golaghat", 1060000, 0.55, 0.48, 0.50, 95, (1400,2000)),
Sector( "Sonitpur", 1900000, 0.65, 0.42, 0.55, 80, (750,1500)),
Sector( "Biswanath", 610000, 0.45, 0.50, 0.40, 85, (1250,1500)),

Sector( "Nagaon", 2800000, 0.60, 0.40, 0.50, 70, (874,1833)),
Sector( "Morigaon", 960000, 0.45, 0.52, 0.40, 65, (623,1915)),
Sector( "Guwahati", 3000000, 0.95, 0.20, 0.90, 55, (305,2000)),
Sector( "Majuli", 170000, 0.30, 0.60, 0.25, 85, (2700,1800))
]
game_map = {}
boats = {}
for l in lst:
    x_coord = l.coords[0] * 0.3
    y_coord = l.coords[1] * 0.3
    l.coords = (x_coord, y_coord)
    game_map[l.name] = l
    boats[l.name] = {"inactive": 0, "active": 0, "locked": 0}

boats["Guwahati"]["inactive"] = 1000

Bigriver = River(
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

    "Dibang": River(
        name="Dibang",
        path=[
            {"sector": game_map["Upper Dibang Valley"], "width": 120, "max_height": 12, "height": 6, },
            {"sector": game_map["Lower Dibang Valley"], "width": 200, "max_height": 14, "height": 8},
        ],
        terminal=(Bigriver, 1)  # joins at east siang
    ),

    "Lohit": River(
        name="Lohit",
        path=[
            {"sector": game_map["Lohit"],    "width": 140, "max_height": 13, "height": 6},
        ],
        terminal=(Bigriver, 2)  # joins near Tinsukia
    ),

    "Subansiri": River(
        name="Subansiri",
        path=[
            {"sector": game_map["Upper Subansiri"], "width": 200, "max_height": 10, "height": 6},
            {"sector": game_map["Lower Subansiri"], "width": 220, "max_height": 15, "height": 9},
        ],
        terminal=(Bigriver, 6)
    ),
}

pot_dams_lst = [  
    Dam(name="Lohit Dam",
        capacity=800,
        cap_used=0,
        cost=650,
        fail_prob=0.02,   # risky fast-build dam
        river=rivers["Lohit"],
        sector=game_map["Lohit"],
        state="Not Built",
        time_to_build = 1)   
    ,

    Dam(
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

    Dam(
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
    Dam(
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

rivers["Subansiri"].path[0]["dam"] = dams["LSD"]

for river_ in rivers:
    ind = -1
    for path_var in rivers[river_].path: #Adding corresponding river to a sector
        ind += 1
        path_var["sector"].river_in.append((rivers[river_], ind))