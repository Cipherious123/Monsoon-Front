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
    pass

commands = {"quit": quitting, "show-boats": show_boats, 
            "show-dams": show_dams,"deploy-boats": deploy_boats, "": show_dams, "show-dams": show_dams}

while True:
    command = input("Issue your command ")
    commands[command.lower()]()

    