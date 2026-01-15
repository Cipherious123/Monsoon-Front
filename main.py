import classes
import graphics
import sys
import random

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

        for i in classes.game_map:
            if i.name==c:
                i.food+=y

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


commands = {"quit": quitting, "show-boats": show_boats, 
            "show-dams": show_dams,"deploy-boats": deploy_boats, "build-dam": build_dam, "deploy-food": deploy_food}

def generate_rainfall(turn_number, recent_rain_history=None):
    """
    Decide rainfall for a turn.

    Args:
        turn_number (int): current game turn
        recent_rain_history (list): list of last N rainfall values (can be None)

    Returns:
        dict with keys:
        - 'type': str (normal / heavy / extreme)
        - 'rainfall': float (amount of water added)
        - 'description': str (for player-facing events)
    """

    if recent_rain_history is None:
        recent_rain_history = []

    # ---- Base probabilities ----
    normal_rain_prob = 0.65
    heavy_rain_prob = 0.25
    extreme_prob = 0.10   # cyclones, cloudbursts, etc.

    # ---- Anti-stall mechanic ----
    # If it's been dry recently, push probability upward
    avg_recent_rain = sum(recent_rain_history[-5:]) / max(1, len(recent_rain_history[-5:]))

    if avg_recent_rain < 1.5:
        heavy_rain_prob += 0.10
        extreme_prob += 0.05

    # Normalize
    total = normal_rain_prob + heavy_rain_prob + extreme_prob
    normal_rain_prob /= total
    heavy_rain_prob /= total
    extreme_prob /= total

    roll = random.random()

    # ---- Normal rainfall ----
    if roll < normal_rain_prob:
        rainfall = random.uniform(0.5, 2.5)
        rain_history.append(rainfall)

        return {
            "type": "normal",
            "rainfall": rainfall,
            "description": "Seasonal rainfall across the area."
        }

    # ---- Heavy rainfall / monsoon surge ----
    elif roll < normal_rain_prob + heavy_rain_prob:
        rainfall = random.uniform(3.0, 6.0)
        rain_history.append(rainfall)
        return {
            "type": "heavy",
            "rainfall": rainfall,
            "description": "Heavy monsoon rains swell rivers and low-lying areas."
        }

    # ---- Extreme weather event ----
    else:
        event = random.choice(["Cyclone", "Cloudburst", "Depression"])
        rainfall = random.uniform(8.0, 15.0)
        rain_history.append(rainfall)

        return {
            "type": "extreme",
            "rainfall": rainfall,
            "description": f"{event} strikes the region! Massive rainfall overwhelms defenses."
        }
    

def inter_turn_recovery(player):
    """
    Recharges player health, money, and rescue resources between turns.
    Balances catch-up for bad turns and rewards political power.
    """

    # ---------- CATCH-UP FACTOR (based on deaths) ----------
    # More deaths → more aid, but diminishing returns
    death_factor = min(player.deaths_this_turn / 1000, 2.0)  # cap effect

    # ---------- POLITICAL POWER FACTOR ----------
    # Scales from 0.5 to 1.5
    political_factor = 0.5 + (player.political_power / 100)

    # ---------- MONEY GRANTS ----------
    base_money = 500
    disaster_aid = 800 * death_factor
    political_bonus = 700 * political_factor

    money_gain = base_money + disaster_aid + political_bonus
    money_gain *= random.uniform(0.9, 1.1)

    player.money += int(money_gain)

    # ---------- RESOURCE REPLENISHMENT ----------
    # Boats help more during heavy death turns
    boats_gained = int((1 + death_factor) * random.choice([0, 1, 2]))

    # Helicopters are rarer, depend heavily on political power
    helicopters_gained = 1 if random.random() < (player.political_power / 200) else 0

    boats["Guwahati"]["inactive"] += boats_gained
    helicopters += helicopters_gained
    player.deaths_this_turn = 0

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

            if player.money >= cost:
                player.money -= cost
                player.political_power = min(100, player.political_power + gain)
                sector.infra += 2
                event_log.append(
                    f"Political visit in {sector.name}. Money spent: {cost}. "
                    f"Political power +{gain}, infra improved."
                )
            else:
                player.political_power -= 5
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
            player.political_power -= 3

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
                if player.money >= response_cost:
                    player.money -= response_cost
                    sector.health += 8
                    event_log.append(
                        f"Disease outbreak in {sector.name}. {deaths} deaths. "
                        f"Funds spent controlling outbreak."
                    )
                else:
                    sector.deaths += int(deaths * 0.5)
                    player.political_power -= 5
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
            player.political_power -= loss

            if player.money >= 15:
                player.money -= 15
                player.political_power += 5
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
            player.money += 20
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

    for sector in classes.gamemap:
        sector.flood()

    inter_turn_recovery()
    random_events_between_turns()