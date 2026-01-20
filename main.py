import classes
import graphics
import sys
import random
import math

#Starting the game 
print("""
Welcome to Monsoon Front!
Today, you got a call from the chief advisor to PM Narendra Modi.
The Indian Meterological department predicts severe rains and perhaps flooding of the Brahmaputra and its tributaries 
in Arunachal Pradesh and Assam. You've been asked to manage the floods, evacuate as required, and save lives.
""")

start = input("Do you accept the mission (Yes/No) ")
if start.lower() == "no":
    print("Alright. Maybe some other time")
    sys.exit()
print("Tutorial ...")

graphics.load_map(classes.map_spt)
home_spt = {}

for sector in classes.game_map:
    if sector.population < 100000:
        spt = classes.village_spt
    elif sector.population < 1000000:
        spt = classes.town_spt
    else:
        spt = classes.village_spt

    home_spt[spt] = sector.coords
    graphics.set_sprites({spt:sector.coords})

graphics.gui_tick()

game_time = 1
boats = {"Guwahati" : {"inactive": 1000, "active": 0, "locked": 0}}
dams = [classes.dam("Ranganadi", 10000, 3000, 35, 0.15, "Subansiri", "Upper Subansiri", "Built")]
potential_dams = [classes.dam("Ranganadi", 10000, 3000, 35, 0.15, "Subansiri", "Upper Subansiri", "Unbuilt")]
political = 100
money = 100
helicopter = 2
rain_history = []

def quitting():
    confirm = input("Input QWERTY to quit. Progress won't be saved ")
    if confirm == "QWERTY":
        sys.exit()
    else:
        print("Continuing with the game")

def show_boats():
    pass

def show_dams():
    pass

def deploy_boats():
    print("You are reassigning x boats from sector A to sector B")
    x = int(input("Input x "))
    A = int(input("Input A "))

    if boats[A]["active"] < x:
        print("Insufficient boats to reassign in A")
    else: 
        B = int(input("Input B "))
        boats[A]["active"] -= x
        boats[B]["locked"] += x
        print(f"Your boats are now in {B}. They cannot be activated to rescue people in this turn.")

def build_dam():
    dam_build = input("Name of dam to build")
    if dam_build not in potential_dams:
        print("Dam not found. Check your spelling!")
        return

    if money < potential_dams[dam_build]["cost"]:
        print("Insufficient resources")
    else:
        money -=  potential_dams[dam_build]["cost"]
        dams[dam_build] = potential_dams[dam_build]
        del potential_dams[dam_build]

def deploy_food():
    print("You are deploying food to areas affected by floods")

    c = input("Enter the name of the sector you want to input")
    y = int(input("Enter the amount of money's worth of food you want to deploy:(1 UNIT OF MONEY/ PACKET OF FOOD"))

    if y > money:
        print("Insufficient resource")

    if y <= money:
        money -= y

        classes.game_map[c].health += y*0.02

def helicopter_rescue(): #Incomplete!
    print("This choice is for emergency evacuation where other modes of evacuation may not be effective.")

    sec_name = input("Enter the name of the sector you want to input")
    choice = input("Enter your choice of deployment")

    if choice==True:
        if money>=10:
            money-=10
            helicopter-=1

    if choice==False:
        pass

def evac():
    pass

commands = {"quit": quitting, "show-boats": show_boats, 
            "show-dams": show_dams,"deploy-boats": deploy_boats, "build-dam": build_dam, 
            "deploy-food": deploy_food, "call_evac": evac}

def generate_rainfall(
    sectors,
    turn_number,
    correlation_radius=5.0
):
    """
    Generate spatially correlated rainfall for sectors.

    Args:
        sectors (dict):
            sector_id -> (x, y)
        turn_number (int)
        max_turns (int)
        correlation_radius (float): higher = smoother rainfall

    Returns:
        dict:
            sector_id -> rainfall amount (float)
    """

    # ---- Game phase (0 = early, 1 = late) ----
    phase = min(1.0, turn_number / 10)

    # ---- Phase-based probabilities ----
    # Early: consistently high rain
    # Late: more variance, extremes & droughts
    base_mean = (1 - phase) * 5.0 + phase * 3.0
    base_variance = (1 - phase) * 1.0 + phase * 4.0

    cyclone_prob = 0.05 + phase * 0.20
    low_rain_prob = phase * 0.25

    # ---- Decide global weather mode ----
    roll = random.random()

    if roll < cyclone_prob:
        global_intensity = random.uniform(10.0, 18.0)
    elif roll < cyclone_prob + low_rain_prob:
        global_intensity = random.uniform(0.3, 1.2)
    else:
        global_intensity = random.gauss(base_mean, base_variance)

    # ---- Generate spatial noise anchors ----
    anchor_count = max(3, len(sectors) // 6)
    anchors = []

    for _ in range(anchor_count):
        ax, ay = random.choice(list(sectors.values()))
        strength = random.uniform(-2.0, 2.0)
        anchors.append((ax, ay, strength))

    # ---- Allocate rainfall to sectors ----
    rainfall_map = {}

    for sector_id, (sx, sy) in sectors.items():
        influence = 0.0

        for ax, ay, strength in anchors:
            dist = math.hypot(sx - ax, sy - ay)
            weight = math.exp(-dist / correlation_radius)
            influence += strength * weight

        rainfall = max(0.0, global_intensity + influence)
        rainfall_map[sector_id] = rainfall

    return rainfall_map

def inter_turn_recovery():
    """
    Recharges player health, money, and rescue resources between turns.
    Balances catch-up for bad turns and rewards political power.
"""

    death_factor = min(deaths / 1000, 2.0)  # cap effect
    political_factor = 0.5 + (political / 100)

    base_money = 100
    disaster_aid = 20 * death_factor
    political_bonus = 70 * political_factor

    money_gain = base_money + disaster_aid + political_bonus
    money += int(money_gain)

    boats_gained = int((1 + death_factor) * random.choice([0, 1, 2]))
    helicopters_gained = 2 if random.random() < (political / 200) else 0

    boats["Guwahati"]["inactive"] += boats_gained
    helicopters += helicopters_gained
    deaths = 0

def random_events_between_turns(player, sectors):
    """
    Creates random inter-turn events.
    Modifies player and sector stats directly.
    Returns a list of event descriptions for logging/UI.
    """

    event_log = []

    # Number of events this turn (keeps game unpredictable)
    num_events = random.choices([0, 1, 2], weights=[2, 5, 3])[0]

    if num_events == 0:
        return ["No major incidents reported this turn."]

    for _ in range(num_events):

        event_type = random.choice([
            "political_visit",
            "illegal_immigration",
            "disease_outbreak",
            "media_expose",
            "ngo_aid",
            "boat_breakdown"
        ])

        # Pick a sector if required
        sector = random.choice(sectors)
        severity = random.uniform(0.5, 1.5)

        # -------------------------
        # POLITICAL VISIT
        # -------------------------
        if event_type == "political_visit":
            cost = int(20 * severity)
            gain = int(10 * severity)

            if money >= cost:
                money -= cost
                political = min(100, political + gain)
                sector.infra += 2
                event_log.append(
                    f"Political visit in {sector.name}. Money spent: {cost}. "
                    f"Political power +{gain}, infra improved."
                )
            else:
                political -= 5
                event_log.append(
                    f"Political visit mishandled in {sector.name}. "
                    f"Public anger rises. Political power -5."
                )

        # -------------------------
        # ILLEGAL IMMIGRATION CRISIS
        # -------------------------
        elif event_type == "illegal_immigration":
            influx = int(1000 * severity)
            sector.population += influx
            sector.health -= 5 * severity
            political -= 3

            event_log.append(
                f"Illegal immigration reported in {sector.name}. "
                f"Population +{influx}, health worsens, political backlash."
            )

        # -------------------------
        # DISEASE OUTBREAK
        # -------------------------
        elif event_type == "disease_outbreak":
            if sector.flood_level > 0.3:
                deaths = int(sector.population * 0.002 * severity)
                sector.deaths += deaths
                sector.health -= 10 * severity

                # Player response cost
                response_cost = int(30 * severity)
                if money >= response_cost:
                    money -= response_cost
                    sector.health += 8
                    event_log.append(
                        f"Disease outbreak in {sector.name}. {deaths} deaths. "
                        f"Funds spent controlling outbreak."
                    )
                else:
                    sector.deaths += int(deaths * 0.5)
                    political -= 5
                    event_log.append(
                        f"Disease outbreak worsens in {sector.name} due to lack of funds."
                    )
            else:
                event_log.append(
                    f"Minor disease scare in {sector.name}, no major impact."
                )

        # -------------------------
        # MEDIA EXPOSE
        # -------------------------
        elif event_type == "media_expose":
            loss = int(8 * severity)
            political -= loss

            if money >= 15:
                money -= 15
                political += 5
                event_log.append(
                    "Media exposes relief inefficiencies. "
                    "Damage control attempted."
                )
            else:
                event_log.append(
                    "Media exposes relief failures. "
                    f"Political power -{loss}."
                )

        # -------------------------
        # NGO AID
        # -------------------------
        elif event_type == "ngo_aid":
            heal = int(10 * severity)
            sector.health += heal
            political += 20
            event_log.append(
                f"NGOs assist in {sector.name}. Health +{heal}, money +20."
            )

        # -------------------------
        # BOAT BREAKDOWN (GAME-WIDE)
        # -------------------------
        elif event_type == "boat_breakdown":
            if player.boats > 0:
                lost = random.choice([0, 1])
                player.boats -= lost
                event_log.append(
                    f"Rescue boat breakdown reported. Boats lost: {lost}."
                )
            else:
                event_log.append(
                    "Boat maintenance issues reported, but no boats left to lose."
                )

    return event_log

def run_turn():
    while True:
        command = input("Issue your command ")
        if command == "end-turn":
            break
        if command not in commands:
            print("Invalid command")
        else:
            commands[command.lower()]()
        
    generate_rainfall(game_time, rain_history)
    for dam in dams:
        dam.fail()

    for river in classes.rivers:
        river.flood_propagate()

    deaths = 0
    for sector_name in classes.gamemap:
        classes.gamemap[sector].flood()
        deaths += classes.gamemap[sector].deaths
    
    inter_turn_recovery()
    random_events_between_turns()