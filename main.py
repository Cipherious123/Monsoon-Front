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
helicopter = 2
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

def helicopter_rescue(): #Incomplete!
    global money
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

def flood_sector():
    pass

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
    
    # ---- Phase-based parameters ----
    base_mean = (1 - phase) * 5.0 + phase * 3.0
    cyclone_prob = 0.05 + phase * 0.15
    low_rain_prob = phase * 0.20
    
    # ---- Decide global weather mode ----
    roll = random.random()
    if roll < cyclone_prob:
        mode = "cyclone"
        global_base = random.uniform(8.0, 12.0)
    elif roll < cyclone_prob + low_rain_prob:
        mode = "drought"
        global_base = random.uniform(0.5, 1.5)
    else:
        mode = "normal"
        global_base = base_mean
    
    # ---- Generate MORE spatial noise anchors with STRONGER influence ----
    anchor_count = max(8, len(sectors) // 3)  # More anchors
    anchors = []
    sector_list = list(sectors.values())
    
    for _ in range(anchor_count):
        ax, ay = random.choice(sector_list).coords
        # Much stronger local variations
        if mode == "cyclone":
            strength = random.uniform(2.0, 8.0)  # Extra rainfall pockets
        elif mode == "drought":
            strength = random.uniform(-1.0, 0.5)  # Slight variations in drought
        else:
            strength = random.uniform(-3.0, 3.0)  # Normal variation
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
        
        # Add small local noise for organic feel
        local_noise = random.gauss(0, 0.5)
        
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

    rainfall_map = generate_rainfall(classes.game_map, rain_history)
    for sector_name in classes.game_map:
        classes.game_map[sector_name].flooded(rainfall_map[sector_name]*10)
    

    for dam in dams:
        dam.fail()

    for river in classes.rivers:
        river.flood_propagate()

    deaths = 0
    for sector_name in classes.game_map:
        classes.game_map[sector_name].flood()
        deaths += classes.game_map[sector_name].deaths
    
    inter_turn_recovery()

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