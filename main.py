import classes
import graphics
import sys
import random
import math
import threading
import queue

command_queue = queue.Queue()

def terminal_input_loop():
    while True:
        cmd = input("Issue your command ")
        command_queue.put(cmd)

threading.Thread(
    target=terminal_input_loop,
    daemon=True
).start()

#Starting the game 
print("""
Welcome to Monsoon Front!
Today, you got a call from the chief advisor to PM Narendra Modi.
The Indian Meterological department predicts severe rains and perhaps flooding of the Brahmaputra and its tributaries 
in Arunachal Pradesh and Assam. You've been asked to manage the floods, evacuate as required, and save lives.
""")

#start = input("Do you accept the mission (Yes/No) ")
start = "Yes"
if start.lower() == "no":
    print("Alright. Maybe some other time")
    sys.exit()

game_time = 1
dams = [classes.dam("Ranganadi", 10000, 3000, 0, 0.15, "Brahmaputra", classes.game_map["Guwahati"], "Built")]
potential_dams = [classes.dam("Ranganadi", 10000, 3000, 35, 0.15, "Brahmaputra", classes.game_map["Guwahati"], "Unbuilt")]
political = 100
money = 1000
morale = 100
heli = 2
locked_heli = 0
rain_history = []
deaths = 0

graphics.load_map(classes.map_spt)
home_spt = []

for sector_name in classes.game_map:
    if classes.game_map[sector_name].population < 100000:
        spt = classes.village_spt
    elif classes.game_map[sector_name].population < 1000000:
        spt = classes.town_spt
    else:
        spt = classes.village_spt

    click_text = f"""{sector_name} - 
                    Population : {classes.game_map[sector_name].population}
                    Health : {classes.game_map[sector_name].health}
                    Infrastructure : {classes.game_map[sector_name].infra}
                    Altitude : {classes.game_map[sector_name].altitude}
                    Flood level: {classes.game_map[sector_name].flooded}
                    Absorption index: {classes.game_map[sector_name].absorption}
                    Political importance: {classes.game_map[sector_name].power}
                    Flood deaths so far: {classes.game_map[sector_name].deaths}
                    Evacuation warning: ???
                    """
    
    home_spt.append({(spt, "-", click_text): classes.game_map[sector_name].coords})

click_text = f""" Money : {money}
                  Political power : {political}
                  Turn number: {game_time}
                  Deaths so far: {deaths}
                  Click "t" to get a tutorial
                  List of Commands - "quit-game": quitting, "show-boats": show_boats, 
                    "show-dams": show_dams,"deploy-boats": deploy_boats, "build-dam": build_dam, 
                    "deploy-food": deploy_food, "call-evac": evac, "flood-sector": flood_sector,
                    "control-dam": control_dam, "deploy-heli": deploy_helicopter, "end-turn"

"""
home_spt.append({(classes.ind_spt, "general stats", click_text): (500, 20)})
graphics.set_sprites_with_labels(home_spt)

graphics.gui_tick()


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
    global money

    print("You are reassigning x boats from sector A to sector B")
    x = int(input("Input x "))
    A = input("Input A ")

    if classes.boats[A]["active"] < x:
        print("Insufficient boats to reassign in A")
    else: 
        B = int(input("Input B "))
        classes.boats[A]["active"] -= x
        classes.boats[B]["locked"] += x
        print(f"Your boats are now in {B}. They cannot be activated to rescue people in this turn.")

def build_dam():
    global money
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
    global money
    print("You are deploying food to areas affected by floods")

    c = input("Enter the name of the sector you want to input")
    y = int(input("Enter the amount of money's worth of food you want to deploy:(1 UNIT OF MONEY/ PACKET OF FOOD"))

    if y > money:
        print("Insufficient resource")

    if y <= money:
        money -= y

        classes.game_map[c].health += y*0.02


def activate_boat():
    global money
    global morale
    print("""This actually evacuates people from one region to another
     - costs 0.05 per boat activation, each boat evacuates 500 people
        It increases morale and health of the target sector but reduces health of output sector""")
    
    insector=input("Enter the sector in which boats are to be activated ")
    outsector = input("Enter name of sector to send the evacuees to ")
    num=int(input('Enter the number of boats you want to activate '))

    if num < classes.boats["inactive"]:
        print("""Insufficient boats in target sector to activate!
               Remember, you can't activate a boat right after deploying it, you must wait one turn""")
        return
    
    if money < 0.05*num:
        print("Insufficient money")
        return
    
    if insector not in classes.game_map or outsector not in classes.game_map:
        print("Invalid Sector Names!")
        return 
    
    money -= 0.05*num

    failure_chance = classes.game_map[insector].flooded * 0.01
    lost = 0
    for _ in range(num):
        if random.random() < failure_chance:
            lost += 1
    if lost >0:
        print(f"Due to dangerous floodwaters, you have lost {lost} boats")
    num -= lost

    classes.boats["insector"]["inactive"]-=num
    classes.boats["insector"]["active"]+=num

    classes.game_map[insector].population -= 500*num
    classes.game_map[insector].health += 0.002*num
    classes.game_map[outsector].health -= 0.002*num
    classes.game_map[insector].population += 500*num
    morale += 0.25 * num

def helicopter_rescue(): 
    global money
    print("This is for emergency evacuation where other modes of evacuation may not be effective. " \
    "It has a chance of greatly increases morale but can fail!")

    sec_name = input("Enter the name of the sector you want to input")
    if sec_name not in classes.game_map:
        print("Sector not found")
        return
    
    if sec_name.flooded < 0.5:
        print("Helicopter rescue not available if flood level is very low")
        return
    
    num = input("Enter number of helicopters to deploy")

    if num > heli:
        print("Insufficent Helicopters")
        return
    if num*4 > money:
        print("Insufficient Money")
 
    money -= num*4

    failure_chance = classes.game_map[sec_name].altitude * 0.001
    lost = 0
    for _ in range(num):
        if random.random() < failure_chance:
            lost += 1
    if lost >0:
        print(f"Due to dangerous altitude, you have lost {lost} Helicopters!")
    num -= lost

    morale += num*2
    classes.game_map[sec_name].health += num*0.01
    print("Action Completed")

def evac():
    """
    Orders evacuation of a sector.
    Heavy morale and political cost, but saves lives later.
    """
    global morale
    global political

    print("""
This evacuation will significantly reduce casualties,
but public morale and political confidence have suffered.""")
    
    sector_name = input("Which sector do you wish to order an evacuation?")
    if sector_name in classes.game_map:
        sector_ = classes.game_map[sector_name]
    else:
        print("Sector not found")
        return

    if sector_.evac > 0:
        print(f"sector {sector_.name} has already been evacuated.")
        return

    sector_.evac = 1 #Turn number 1 of evacuation!

    # Penalties
    morale = max(0, morale - 30)
    political = max(0, political - 25)

    print(f"\nEVACUATION ORDER ISSUED FOR sector {sector_name.upper()}")
    print("-" * 60)

    print("""
FLOOD PREPARATION & EVACUATION GUIDELINES
----------------------------------------
1. Move immediately to higher ground or designated relief camps.
2. Carry essential documents, medicines, food, and clean water.
3. Switch off electricity and gas supplies before leaving.
4. Do NOT attempt to cross fast-moving water on foot or vehicle.
5. Follow instructions from local authorities and army units.
6. Help children, elderly, and injured individuals evacuate first.
7. Stay tuned to official announcements for updates.

""")

    print("-" * 60)

def flood_sector(sector, river_reduction=2.0):
    """
    Deliberately floods a sector to reduce river height
    and protect downstream regions.
    """
    global morale
    global political

    print("""
This action will significantly reduce effects on downstream sectors,
but public morale and political confidence will suffer.""")
    
    river_name = input("Which river do you choose? ")
    sector_name = input("Which sector do you wish to flood? ")
    if sector_name in classes.game_map and river_name in classes.rivers:
        sector_ = classes.game_map[sector_name]
        river_ = classes.rivers[river_name]
    else:
        print("Sector/River not found")
        return
    
    ind = -1
    for path_var in river_.path:
        ind += 1
        if path_var["sector"] == sector_:
            break
    else:
        print("Sector isn't in the river's path")
        return

    height_diff = path_var["height"] - path_var["max_height"]
    if height_diff < 0:
        print("River is not overflowing. Can't flood sector")
        return
    
    print(f"\nEMERGENCY FLOODING INITIATED IN SECTOR {sector.name.upper()}")
    print("-" * 60)

    # Reduce river height 
    original_height = path_var["height"]
    path_var["height"] = max(path_var["height"] - river_reduction, path_var["max_height"])

    change = original_height - path_var["height"]
    sector.flooded += change * path_var["width"]
    river_.path[ind] = path_var

    # Severe penalties
    morale -= 10 * change
    political -= 10 * change 

    print(f"River height reduced from {original_height}m to {path_var['height']}m.")

def control_dam():
    dam_name = input("Name of dam to control: ")
    if dam_name not in dams:
        print("Dam not found")
        return

    amt = float(input("Amount of water to release"))
    if amt > dams[dam_name].cap_used:
        print("Amount is greater than water held by reservoir! Releasing all the water")
        amt = dams[dam_name].cap_used
    
    dams[dam_name].cap_used -= amt
    dams[dam_name].river.add_water(dams[dam_name].sector, amt)

commands = {"quit-game": quitting, "show-boats": show_boats, 
            "show-dams": show_dams,"deploy-boats": deploy_boats, "build-dam": build_dam, 
            "deploy-food": deploy_food, "call-evac": evac, "flood-sector": flood_sector,
             "control-dam": control_dam, "deploy-heli": helicopter_rescue}

def generate_rainfall(
    sectors,
    turn_number,
    correlation_radius=5.0):
    """
    ***Generate spatially correlated rainfall for sectors.***
    Rainfall organically stops after ~10 turns.
    -------------------------------------------------------------------------
    Args:
        sectors (dict):
            sector_id -> sector
        turn_number (int)
        correlation_radius (float): higher = smoother rainfall
    Returns:
        dict:
            sector_id -> rainfall amount (float)
    """
    # ---- Game phase (0 = early, 1 = late) ----
    phase = min(1.0, turn_number / 10)
    
    if turn_number <= 10:
        decay_factor = 1.0 - (turn_number / 10) ** 2  # Quadratic decay
    else:
        decay_factor = random.uniform(0.0, 0.05) if random.random() < 0.1 else 0.0
    
    if decay_factor < 0.01:
        return {sector_id: 0.0 for sector_id in sectors}
    
    # ---- Phase-based parameters (scaled by decay) ----
    base_mean = ((1 - phase) * 5.0 + phase * 3.0) * decay_factor
    cyclone_prob = (0.05 + phase * 0.15) * decay_factor
    low_rain_prob = phase * 0.20
    
    # ---- Decide global weather mode ----
    roll = random.random()
    if roll < cyclone_prob:
        mode = "cyclone"
        global_base = random.uniform(8.0, 12.0) * decay_factor
    elif roll < cyclone_prob + low_rain_prob:
        mode = "drought"
        global_base = random.uniform(0.5, 1.5) * decay_factor
    else:
        mode = "normal"
        global_base = base_mean
    
    # ---- Generate spatial noise anchors ----
    anchor_count = max(8, len(sectors) // 3)
    anchors = []
    sector_list = list(sectors.values())
    
    for _ in range(anchor_count):
        ax, ay = random.choice(sector_list).coords
        if mode == "cyclone":
            strength = random.uniform(2.0, 8.0) * decay_factor
        elif mode == "drought":
            strength = random.uniform(-1.0, 0.5) * decay_factor
        else:
            strength = random.uniform(-3.0, 3.0) * decay_factor
        anchors.append((ax, ay, strength))
    
    # ---- Allocate rainfall to sectors ----
    rainfall_map = {}
    
    for sector_id, sector in sectors.items():
        # Calculate weighted influence from all anchors
        total_influence = 0.0
        total_weight = 0.0
        
        for ax, ay, strength in anchors:
            dist = math.hypot(sector.coords[0] - ax, sector.coords[1] - ay)
            weight = math.exp(-dist / correlation_radius)
            total_influence += strength * weight
            total_weight += weight
        
        # Normalize influence and add local randomness
        if total_weight > 0:
            avg_influence = total_influence / total_weight
        else:
            avg_influence = 0.0

        local_noise = random.gauss(0, 0.5) * decay_factor
        
        # Combine global base with local spatial variation
        rainfall = max(0.0, global_base + avg_influence + local_noise)
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

    classes.boats["Guwahati"]["inactive"] += boats_gained
    helicopters += helicopters_gained
    deaths = 0


def end_turn():     
    for sector_name in classes.boats:
        classes.boats["inactive"] += classes.boats["locked"]
        classes.boats["locked"] = 0
    heli += locked_heli
    locked_heli = 0

    rainfall_map = generate_rainfall(classes.game_map, rain_history)
    for sector_name in classes.game_map:
        classes.game_map[sector_name].flooded(rainfall_map[sector_name]*10)
        classes.game_map[sector_name].evacuation()

    for dam in dams:
        dam.fail()

    for river in classes.rivers:
        river.flood_propagate()

    deaths = 0
    for sector_name in classes.game_map:
        classes.game_map[sector_name].flood()
        deaths += classes.game_map[sector_name].deaths
        classes.game_map[sector_name].absorb()

    if political < 0:
        print("Game over! Political acceptance has dropped below 0! The politicians are angry and you have been fired!!!")
        _ = input("Good try! Enter X to end the game")
        sys.exit()
    
    if morale < 0:
        print("Game over! Morale has dropped below 0! The people are angry and you have been fired!!!")
        _ = input("Good try! Enter X to end the game")
        sys.exit()

    inter_turn_recovery()

def end_game():
    total_score = 0
    max_possible_score = 0

    report = []

    # ---- weights (tweak these for balance) ----
    W_DEATHS = 0.45
    W_INFRA  = 0.20
    W_HEALTH = 0.20
    W_FLOOD  = 0.15

    for sector in classes.lst:
        # ---- normalize metrics ----
        if sector.initial_population > 0:
            survival_rate = 1 - (sector.deaths / sector.initial_population)
            survival_rate = max(0, survival_rate)
        else:
            survival_rate = 1

        infra_score  = sector.infra          # already 0–1
        health_score = sector.health         # already 0–1

        # assume flooded ranges roughly 0–10
        flood_score = max(0, 1 - (sector.flooded / 10))

        sector_score = (
            survival_rate * W_DEATHS +
            infra_score  * W_INFRA +
            health_score * W_HEALTH +
            flood_score  * W_FLOOD
        )

        total_score += sector_score
        max_possible_score += 1  # each sector maxes at 1

        report.append({
            "sector": sector.name,
            "survival_rate": round(survival_rate, 2),
            "infra": round(infra_score, 2),
            "health": round(health_score, 2),
            "flood": round(sector.flooded, 2),
            "sector_score": round(sector_score, 2)
        })

    # ---- final normalization ----
    final_score = (total_score / max_possible_score) * 100

    # ---- grading ----
    if final_score >= 85:
        grade = "Outstanding Relief Effort"
    elif final_score >= 70:
        grade = "Effective Command"
    elif final_score >= 50:
        grade = "Mixed Results"
    else:
        grade = "Relief Failure"

    return {
        "final_score": round(final_score, 1),
        "grade": grade,
        "sector_report": report
    }

def handle_command(command):
    if command == "end-turn":
        end_turn()
        return

    if command not in commands:
        print("Invalid command")
    else:
        commands[command.lower()]()

while True:
    graphics.gui_tick()
    
    if not command_queue.empty():
        command = command_queue.get()
        handle_command(command)