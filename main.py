import classes
import graphics
import sys

#Starting the game 
print("""
Welcome to Monsoon Front!
Today, you got a call from the chief advisor to PM Narendra Modi.
The Indian Meterological department predicts severe rains and perhaps flooding of the Brahmaputra in Arunachal Pradesh and Assam
You've been asked to manage the floods, evacuate as required, and save lives.
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

boats = {"Guwahati" : 1000}
dams = {classes.dam("Ranganadi", 10000, 3000, 35, 0.15, "Subansiri", "Upper Subansiri", "Built")}
potential_dams = {"A": {"capacity" : 3000, "failure" : 0.1, "cost": 30}}
political = 100
money = 100
helicopter = 2

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

    if boats[A] < x:
        print("Insufficient boats to reassign in A")
    else: 
        B = int(input("Input B "))
        boats[A] -= x
        boats[B] += x
        print("Operation successful")

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
    pass

commands = {"quit": quitting, "show-boats": show_boats, 
            "show-dams": show_dams,"deploy-boats": deploy_boats, "build-dam": build_dam, "deploy-food": deploy_food}

def run_turn():
    while True:
        command = input("Issue your command ")
        if command == "end-turn":
            break
        if command not in commands:
            print("Invalid command")
        else:
            commands[command.lower()]()


def post_turn():
    for river in classes.rivers:
        river.flood()

    for dam in dams:
        dam.fail()

    for sector in classes.gamemap:
        sector.health =- sector.flooded*0.1