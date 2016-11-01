#!/usr/bin/python

import pygcurse
import pygame
import fov

import math
import random


img_thrust = "      " + \
			 " #>   " + \
			 " #>>> " + \
			 " #>   "

img_light =  "      " + \
			 "  #   " + \
			 " #>#  " + \
			 "  #   "

img_laser =  "      " + \
			 "      " + \
			 " #> --" + \
			 "      "
                                                                                                     	 

img_ship=		          "               .__./''''''| \n" +\
				"          ._____________/   |/^^^^^^^\ \n" +\
				"	         |             `===` _______| \n" +\
				"                  `.             .___/^^^^^^^^\ \n" +\
				"	         `------------'~~~\________/ \n" +\
				"                          `........\ \n" +\
				"	                           `-------' \n"





SCREEN_WIDTH = 60
SCREEN_HEIGHT = 50
GAME_WIDTH = 50
GAME_HEIGHT = 40
GAME_X = 10
GAME_Y = 0
LEFT_CONSOLE_WIDTH = 10
LEFT_CONSOLE_HEIGHT = 50
LEFT_CONSOLE_X = 0
LEFT_CONSOLE_Y = 0
BOTTOM_CONSOLE_WIDTH = 49
BOTTOM_CONSOLE_HEIGHT = 10
BOTTOM_CONSOLE_X = 11 # offset by 1 to avoid border overlap
BOTTOM_CONSOLE_Y = 40

BORDER_CORNER_CHAR = "O"
BORDER_COLOR = 'green'

TRAIL_COLOR = pygame.Color(255,140,0)

win = pygcurse.PygcurseWindow(SCREEN_WIDTH, SCREEN_HEIGHT, 'Hulk')
font = pygame.font.Font("xirod.ttf",10)
win.font = font
win.autoupdate = False

class GameObject:
	def __init__(self):
		self.paused = False
		self.playing = True
		self.on_ship = False
		self.console_list = []
		self.entity_list = []
		self.ability_list = []
		self.graphical_entity_list = []
		self.enemy_list = []
		self.turn_count = 0
		self.ship_log_messages = []
		self.derelict_color = 'white'

gameObject = GameObject()

class Console:
	def __init__(self, x,y,width,height,name='',bottom_margin = 0):
		self.x=x
		self.y=y
		self.width=width
		self.height=height
		self.messages = []
		self.name = name
		self.bottom_margin=bottom_margin
		gameObject.console_list.append(self)

class Entity:
	def __init__(self, x, y,char,color = 'white', bg_color = 'black',is_physical=True,lifespan=None):
		self.x = x
		self.y = y
		self.char = char
		self.color = color
		self.bg_color = bg_color
		if is_physical: # todo: make this class-based
			gameObject.entity_list.append(self)
		else:
			gameObject.graphical_entity_list.append(self)
			self.lifespan = lifespan


	def has_collided(self, entity):
		if self is not entity and self.x == entity.x and self.y == entity.y:
			return True
		else:
			return False

	def destroy(self):
		if self in gameObject.entity_list:
			gameObject.entity_list.remove(self)
		if self in gameObject.graphical_entity_list:
			gameObject.graphical_entity_list.remove(self)

class DynamicEntity(Entity):
	def __init__(self, *args, **kwargs):
		Entity.__init__(self, *args, **kwargs)
	def move(self, direction):

		if isinstance(self, Player):
			gameObject.turn_count = gameObject.turn_count + 1

		# todo: make speed trail
		old_x = self.x
		old_y = self.y

		if direction=='up':
			self.y -= self.speed
		elif direction=='down':
			self.y += self.speed
		elif direction == 'left':
			self.x -= self.speed
		elif direction == 'right':
			self.x += self.speed
		elif direction == 'wait':
			return

		has_trail = False
		if self.speed > 1:
			# if the entity is moving very fast
			if old_x > self.x:
				trail_x = self.x + 1
			elif old_x == self.x:
				trail_x = self.x
			elif old_x < self.x:
				trail_x = self.x - 1

			if old_y > self.y:
				trail_y = self.y + 1
			elif old_y == self.y:
				trail_y = self.y
			elif old_y < self.y:
				trail_y = self.y - 1 
			trail = self.create_trail(trail_x,trail_y)
			has_trail = True

		for entity in gameObject.entity_list:
			if has_trail:
				if trail.has_collided(entity):
					self.x = old_x
					self.y = old_y
					self.handle_collision(entity)
					trail.destroy()
					has_trail = False

			if self.has_collided(entity):
				# don't move onto other entities, but instead collide with them
				self.x = old_x
				self.y = old_y
				self.handle_collision(entity)
				if has_trail:
					self.x = trail.x
					self.y = trail.y
					trail.destroy()
	
	def take_damage(self,dmg):
		self.hp = self.hp - dmg
		if self.hp <=0:
			self.hp = 0
			self.on_death()

		if isinstance(self, Player):
			updatePlayerHealth(gameObject.conBottomLeft,self)

	def create_trail(self,x,y):
		trail = DynamicEntity(x,y,' ',is_physical = False, lifespan=3)
		trail.bg_color = TRAIL_COLOR
		trail.take_turn = graphicalEntityAI
		return trail

	def create_laser_splash(self,x,y):
		splash = DynamicEntity(x,y,' ',is_physical = False, lifespan=2)
		splash.bg_color = 'darkred'
		splash.take_turn = graphicalEntityAI

	def take_turn(self):
		return


def graphicalEntityAI(self):
	if self.lifespan:
		self.lifespan = self.lifespan - 1
		if self.lifespan < 1:
			self.destroy()

def funcVisitTile(x,y):
	fov_tiles_list.append([x,y])

def funcTileBlocked(x,y):
	for entity in gameObject.entity_list:
		if entity.x == x and entity.y == y:
			return True
	return False

class Enemy(DynamicEntity):
	def __init__(self, *args):
		DynamicEntity.__init__(self, *args)
		self.hp = 50
		self.damage = 25
		self.name = "unknown enemy"
		self.speed = 1
		self.attention_span = 0
		self.focus = random.choice([2,3,4,5])
		gameObject.enemy_list.append(self)

	def move(self, *args):
		oldx = self.x
		oldy = self.y
		DynamicEntity.move(self, *args)
		if oldx == self.x and oldy == self.y:
			self.focus = random.choice([2,3,4,5])

	def handle_collision(self, entity):
		if isinstance(entity, Player) and self.focus == 1:
			self.attack_player(entity)
		return

	def attack_player(self, player):
		player.take_damage(self.damage)
		writeToConsole("Drone attacked by " + self.name + "!", gameObject.conBottom, 'red')
		updatePlayerHealth(gameObject.conBottomLeft, player)
		self.focus = random.choice([2,3,4,5])

	def take_turn(self, player):
		# this is a hit-and-run type of enemy
		if self.attention_span % 1 == 0: #change this value to slow down enemies
			if (self.attention_span % 10) == 0 and self.focus != 1:
				self.focus = random.choice([1,2,3,4,5])
			if self.focus ==1:
				if player.x < self.x:
					self.move('left')
				elif player.x > self.x:
					self.move('right')
				elif player.y > self.y:
					self.move('down')
				elif player.y < self.y:
					self.move('up')
			elif self.focus == 2:
				self.move('up')
			elif self.focus == 3:
				self.move('down')
			elif self.focus == 4:
				self.move('right')
			elif self.focus == 5:
				self.move('left')

		self.attention_span = self.attention_span + 1

	def on_death(self):
		self.destroy()
		gameObject.enemy_list.remove(self)
		writeToConsole("The " + self.name + " dies!", gameObject.conBottom, 'yellow')

class Player(DynamicEntity):
	def __init__(self, *args):
		DynamicEntity.__init__(self, *args)
		self.laser_on = False
		self.light_on = False
		self.thrust_on = False
		self.hp = 100
		self.energy = 150
		self.fov_range = 5
		self.fov_tiles_list =[]
		self.color = 'green'

		self.drone_parts = 5
		self.jump_fuel = 2

	def handle_collision(self, entity):
		if self.laser_on:
			self.energy = self.energy - 50
			if self.energy <= 0:
				writeToConsole("Energy low! Powering down drilling laser...", gameObject.conBottom, 'red')
				setAbilitiesInactive()

		if self.laser_on:
			if isinstance(entity,Wall):
					self.create_laser_splash(entity.x,entity.y)
					if entity.destructible:
						entity.destroy()
					else:
						writeToConsole("The hull is too thick to cut.",gameObject.conBottom,'red')

			if isinstance(entity,Enemy):
				writeToConsole("You hit the " + entity.name + " with your laser!", gameObject.conBottom, 'yellow')
				entity.take_damage(100)
					
		else:
			if isinstance(entity,Wall):
				writeToConsole("You scrape against the metal hull.",gameObject.conBottom,'white')
				self.take_damage(5)
			elif isinstance(entity, DronePart):
				writeToConsole("You found a drone part.", gameObject.conBottom, 'green')
				gameObject.ship_log_messages.append(["Drone part added to stores.", 'green'])
				player.drone_parts = player.drone_parts + 1
				entity.destroy()
			elif isinstance(entity, JumpFuel):
				writeToConsole("You found some jump fuel!", gameObject.conBottom, 'pink')
				gameObject.ship_log_messages.append(["Jump fuel added to stores!", 'pink'])
				player.jump_fuel = player.jump_fuel + 1
				entity.destroy()


	def on_death(self):
		self.destroy()
		writeToConsole("Drone destroyed.", gameObject.conBottom, 'red')
		gameObject.ship_log_messages.append(["Drone destroyed.", 'red'])
		updatePlayerHealth(gameObject.conBottomLeft, player)
		displayDeath()
		self.drone_parts = self.drone_parts - 1

	def update_energy_on_move(self):
		if self.light_on:
			self.energy = self.energy - 50
		if self.thrust_on:
			self.energy = self.energy - 25

		if self.energy <= 0:
			if self.light_on or self.thrust_on:
				setAbilitiesInactive()
				writeToConsole("Energy low! Powering down non-essential functions...", gameObject.conBottom, 'red')

		if self.energy <= -25:
			self.energy = -25 # put a hard floor on energy loss

		if self.energy >= 100:
			self.energy = 100 # put a hard ceiling on energy storage

		self.energy = self.energy + 10

	def move(self, direction):
		DynamicEntity.move(self, direction)
		self.calculate_fov()
		self.update_energy_on_move()
		updatePlayerEnergy(gameObject.conMiddleLeft, self)

	def visit_fov_tile(self,x,y):
		self.fov_tiles_list.append([x,y])

	def fov_tile_blocked(self,x,y):
		for entity in gameObject.entity_list:
			if entity.x == x and entity.y == y:
				return True
		return False

	def calculate_fov(self):
		self.fov_tiles_list = []
		fov.fieldOfView(self.x, self.y, gameObject.conGame.width, gameObject.conGame.height, self.fov_range, self.visit_fov_tile, self.fov_tile_blocked)



class Wall(DynamicEntity):
	def __init__(self, *args):
		DynamicEntity.__init__(self, *args)
		self.color = 'grey'
		self.destructible = True
	def handle_collision(self, entity):
		return


class DronePart(DynamicEntity):
	def __init__(self, *args):
		DynamicEntity.__init__(self, *args)
		self.color = 'green'
		self.char = '+'
	def handle_collision(self, entity):
		return

class JumpFuel(DynamicEntity):
	def __init__(self, *args):
		DynamicEntity.__init__(self, *args)
		self.color = 'pink'
		self.char = '%'
	def handle_collision(self, entity):
		return


class Ability:
	def __init__(self,img,on_activate,on_deactivate,name="unknown ability",color='grey',short_name=""):
		self.name = name
		self.img = img
		self.on_activate = on_activate
		self.on_deactivate = on_deactivate
		self.active = False
		self.usable = True
		self.console = Console(0,0,8,6,short_name)
		gameObject.console_list.remove(self.console) # don't put this in the list of consoles
		self.color = color
		gameObject.ability_list.append(self)

def setActiveAbility(active_ability):
	if active_ability.active == True:
		# deactivate ability
		writeToConsole("Powering down " + active_ability.name + ".", gameObject.conBottom,'white')
		for ability in gameObject.ability_list:
			ability.active = False
			ability.color = 'grey'
			ability.on_deactivate()
	elif active_ability.usable:
		# activate ability
		if player.energy >= 20:
			for ability in gameObject.ability_list:
				ability.active = False
				ability.color = 'grey'
				ability.on_deactivate()
			active_ability.active = True
			active_ability.on_activate()
			active_ability.color = pygame.Color(204,204,0) # dark yellow
			writeToConsole("Power diverted to " + active_ability.name + ".", gameObject.conBottom,'white')
		else:
			writeToConsole("Not enough power!", gameObject.conBottom, 'red')

def setAbilitiesInactive():
	for ability in gameObject.ability_list:
		ability.active = False
		ability.color = 'grey'
		ability.on_deactivate()

def drawAbilities(console):
	cursor_x = console.x + 1
	cursor_y = console.y + 1
	for ability in gameObject.ability_list:
		ability.console.x = cursor_x
		ability.console.y = cursor_y
		drawConsole(ability.console,win,color=ability.color)
		drawConsoleMessages(ability.console)
		cursor_y = cursor_y + ability.console.height + 1

def abilityLaserActivate():
	player.laser_on = True
	player.bg_color = 'darkred'
def abilityLaserDeactivate():
	player.laser_on = False
	player.bg_color = 'black'

def abilityLightActivate():
	player.light_on = True
	player.energy = player.energy - 50
	updatePlayerEnergy(gameObject.conMiddleLeft, player)
	player.fov_range = 15
	player.calculate_fov()
	player.bg_color = 'yellow'
	player.update_energy_on_move()
def abilityLightDeactivate():
	player.light_on = False
	player.fov_range = 5
	player.calculate_fov()
	player.bg_color = 'black'

def abilityThrustActivate():
	player.thrust_on = True
	player.speed = 2
	player.bg_color = TRAIL_COLOR # dark orange
def abilityThrustDeactivate():
	player.thrust_on = False
	player.speed = 1
	player.bg_color = 'black'

def updatePlayerHealth(health_console, player):
	# draw player health
	health_string = ""
	max_lines = 8
	displayed_health = int((player.hp *max_lines)//100) #where player has 100 max hp
	for i in range(max_lines-displayed_health):
		health_string = health_string + "        "
	for i in range(displayed_health):
		health_string = health_string + " #######"
	clearConsoleMessages(health_console)
	writeToConsole(health_string,health_console, color='red', margin="")

def updatePlayerEnergy(energy_console, player):
	energy_string = ""
	max_lines = 9
	displayed_energy = int((player.energy *max_lines)//100) #where player has 100 max hp
	for i in range(max_lines-displayed_energy):
		energy_string = energy_string + "        "
	for i in range(displayed_energy):
		energy_string = energy_string + " #######"
	clearConsoleMessages(energy_console)
	writeToConsole(energy_string,energy_console, color='blue', margin="")

def drawGameEntities(window,console,player):
	for entity in gameObject.entity_list:
		if [entity.x,entity.y] in player.fov_tiles_list:
			putchar(console.x+entity.x, console.y+entity.y,entity.char, entity.color,entity.bg_color)

	for entity in gameObject.graphical_entity_list:
		putchar(console.x+entity.x, console.y+entity.y,entity.char, entity.color,entity.bg_color)

def drawPlayerHealth(health_console):
	drawConsoleMessages(health_console)

def drawPlayerEnergy(energy_console):
	drawConsoleMessages(energy_console)

def drawConsole(console,window,color=BORDER_COLOR):
	# draw sidebars
	for i in range(console.height):
		putchar(console.x+console.width,console.y+i,"|",color)
		putchar(console.x,console.y+i,"|",color)
	for i in range(console.width):
		putchar(console.x+i,console.y,"-",color)
		putchar(console.x+i,console.y+console.height,"-",color)
	# draw corners
	putchar(console.x,console.y,BORDER_CORNER_CHAR,color)
	putchar(console.x,console.y+console.height,BORDER_CORNER_CHAR,color)
	putchar(console.x+console.width,console.y,BORDER_CORNER_CHAR,color)
	putchar(console.x+console.width,console.y+console.height,BORDER_CORNER_CHAR,color)
	# draw name
	try:
		putchar(console.x+1, console.y, console.name, color)
	except:
		return # no name

def drawConsoleList(console_list, window):
	for console in console_list:
		drawConsole(console, window)

def writeToConsole(msg,console,color='white',margin="  "):
	sliced_msg = []
	sliced_msg.append([msg[:console.width-2],color]) # margin of 1 each side
	msg = msg[console.width-2:]
	while len(msg) > 0:
		# keep slicing with a hanging indent
		sliced_msg.append([margin + msg[:console.width-2-len(margin)],color])
		msg = msg[console.width-2-len(margin):]

	console.messages = console.messages + sliced_msg
	if len(console.messages) > console.height-console.bottom_margin: # margin on the bottom
		console.messages = console.messages[-(console.height-console.bottom_margin):]

	drawConsole(console, win)


def drawConsoleMessages(console):
	i=0
	for msg in console.messages:
		win.cursor = (console.x+1, console.y+1+i)
		win.write(msg[0], fgcolor=msg[1])
		i=i+1

def clearConsoleMessages(console):
	console.messages = []


def putchar(x,y,char,color, bgcolor = 'black'):
	win.cursor = (x,y)
	win.putchars(char, fgcolor = color,bgcolor = bgcolor)

def write(x,y,char,color):
	win.cursor = (x,y)
	win.write(char, fgcolor=color)

def createWalls(console):
	for i in range(console.width-1):
		wall = Wall(i,1,'%')
		wall.destructible = False
		wall = Wall(i+1,console.height-1,'%')
		wall.destructible = False
	for i in range(console.height-1):
		wall = Wall(1,i,'%')
		wall.destructible = False
		wall = Wall(console.width-1,i,'%')
		wall.destructible = False

def createRoom(console,x,y,width=10,height=10):
	for i in range(width+1):
		wall = Wall(console.x+x+i,console.y+y,'#')
		wall = Wall(console.x+x+i,console.y+y+height,'#')
	for i in range(height):
		wall = Wall(console.x+x,console.y+y+i,'#')
		wall = Wall(console.x+x+width,console.y+y+i,'#')

	for entity in gameObject.entity_list:
		if isinstance(entity, Wall) and entity.x == console.x+x+width/2 and entity.y > console.y+y:
			entity.destroy() # make door

def createRooms(console, num, max_size):
	rooms = 0
	while rooms < num:
		rx = random.choice(range(console.width-10))
		ry = random.choice(range(console.height-10))
		rw = random.choice(range(1,max_size))
		rh = random.choice(range(1,max_size))
		if rx+rw < console.width and ry+rh < console.height:
			createRoom(console,rx,ry,width=rw, height=rh)
			rooms = rooms + 1
	
def placeDronePart(console, num):
	parts = 0
	while parts < num:
		rx = random.choice(range(10,console.width-10))
		ry = random.choice(range(10,console.height-10))
		overlap = False
		for entity in gameObject.entity_list:
			if entity.x == console.x+rx and entity.y == console.y+ry:
				overlap = True
		if not overlap:
			part = DronePart(console.x+rx, console.y+ry,'+')
			parts = parts + 1

def placeEnemies(console, num):
	parts = 0
	while parts < num:
		rx = random.choice(range(10,console.width-10))
		ry = random.choice(range(10,console.height-10))
		overlap = False
		for entity in gameObject.entity_list:
			if entity.x == console.x+rx and entity.y == console.y+ry:
				overlap = True
		if not overlap:
			part = Enemy(console.x+rx, console.y+ry,'&', 'red')
			parts = parts + 1

def placeJumpFuel(console, num):
	parts = 0
	while parts < num:
		rx = random.choice(range(10,console.width-10))
		ry = random.choice(range(10,console.height-10))
		overlap = False
		for entity in gameObject.entity_list:
			if entity.x == console.x+rx and entity.y == console.y+ry:
				overlap = True
		if not overlap:
			part = JumpFuel(console.x+rx, console.y+ry,'+')
			parts = parts + 1

def drawDots(console, player):
	for tile in player.fov_tiles_list:
		putchar(console.x+tile[0], console.y+tile[1],'.','grey')

def blankConsole(console):
	blank_string = " "
	for i in range(console.width * console.height):
		blank_string = blank_string + " "

	writeToConsole(blank_string, console,'white',"")
	drawConsoleMessages(console)
	clearConsoleMessages(console)
	drawConsole(console, win)
	

def drawGame(window, console, player):
	window.setscreencolors(None, 'black', clear=True) # clear
	drawConsoleMessages(console)
	drawDots(console, player)
	drawGameEntities(window, console, player)
	drawConsoleList(gameObject.console_list, window)
	drawConsoleMessages(gameObject.conBottom)
	drawConsoleMessages(gameObject.conControls)
	drawAbilities(gameObject.conTopLeft)
	drawPlayerHealth(gameObject.conBottomLeft)
	drawPlayerEnergy(gameObject.conMiddleLeft)
	window.update()

###### Menu functions and options ###########

def drawMenu(window, width, height, options, name, align='auto', color='green'):
	if align == 'auto':
		left_margin = math.floor((SCREEN_WIDTH-width)/2)
		top_margin = math.floor((SCREEN_HEIGHT-height)/2)
	else:
		left_margin = align[0]
		top_margin = align[1]

	conMenu = Console(left_margin, top_margin, width, height, name)
	blankConsole(conMenu)

	for option in options:
		writeToConsole("", conMenu, 'white', '') # draw one blank bar
		writeToConsole(" " + option[0], conMenu, color, '')

	drawConsoleMessages(conMenu)
	gameObject.console_list.remove(conMenu)

def returnToShip():
	gameObject.ship_log_messages.append(["Drone recalled.", 'green'])
	shipMenu()

def shipMenu():
	gameObject.paused = False
	gameObject.playing = False
	gameObject.on_ship = True

	

def unpauseGame():
	gameObject.paused = False

def quitGame():
	gameObject.viewing_controls = False
	gameObject.paused = False
	gameObject.playing = False
	gameObject.on_ship = False

def drawControlsMenu():
	drawMenu(win, 40,25,controls_menu_options, '-|controls|-',color='white')
	win.update()

def exitControlsMenu():
	gameObject.viewing_controls = False
	drawGame(win, gameObject.conGame, player)
	drawPauseMenu()

def displayControls():
	gameObject.viewing_controls = True
	drawControlsMenu()
	while gameObject.viewing_controls:
		handleMenuInputs(controls_menu_options)

def displayDeath():
	gameObject.viewing_death_message = True
	drawDeathMenu()
	while gameObject.viewing_death_message:
		handleMenuInputs(death_menu_options)

def exitDeathMenu():
	gameObject.viewing_death_message = False
	shipMenu()


pause_menu_options = [["Continue game? (spacebar)",pygame.K_SPACE, unpauseGame],["View controls (c)",pygame.K_c, displayControls],["Quit game (q)",pygame.K_q, quitGame]]

game_menu_options = [["Recall drone (r)", pygame.K_r, returnToShip]]

controls_menu_options = [
							["Move the drone with the arrow keys.", pygame.K_SPACE, exitControlsMenu],
							["Activate abilities like drilling, exterior lights, and your drilling laser by pressing 1, 2, or 3.", pygame.K_SPACE, exitControlsMenu],
							["Be careful - using abilities drains your energy levels quickly. You will need to wait (with the spacebar) or move around until your energy recharges.", pygame.K_SPACE, exitControlsMenu], 
							["You can drill through most interior walls. Look for more drone parts (+) or ship fuel (%) as you go, but beware! What killed the ship's crew may be still there, waiting in the dark...", pygame.K_SPACE, exitControlsMenu],
							["You can hit 'r' at any point to teleport your drone (and its contents) back to your own ship.", pygame.K_SPACE, exitControlsMenu],
							["(Press spacebar to return)", pygame.K_SPACE, exitControlsMenu]
							]

death_menu_options = [
							["Drone signal lost!", pygame.K_SPACE, exitDeathMenu],
							["Hit spacebar to return to your ship.", pygame.K_SPACE, exitDeathMenu],
							]


def drawPauseMenu():
	drawMenu(win, 30,8,pause_menu_options, '-|game paused|-')
	win.update()

def drawDeathMenu():
	drawMenu(win,30,8,death_menu_options, '-|ERROR|-',color='red')
	win.update()

def pauseGame():
	gameObject.paused = True
	drawPauseMenu()
	while gameObject.paused:
		handleMenuInputs(pause_menu_options)

def handleMenuInputs(menu_options, events = None):
	if events == None:
		events = pygame.event.get()

	for event in events:
		if event.type == pygame.KEYDOWN:
			current_input = event.key
			for option in menu_options:
				if current_input == option[1]:
					option[2]()
			if current_input == pygame.K_ESCAPE:
				pauseGame()

def launchDrone():
	if player.drone_parts > 0:
		initNewDrone()
		gameObject.paused = False
		gameObject.playing = True
		gameObject.on_ship = False
		gameObject.drone_active = True
		player.drone_parts = player.drone_parts - 1
	else:
		writeToConsole("Not enough drone parts!", gameObject.conShipLog, 'red')

def drawStarJump(console):
	for x in range(console.width):
		for y in range(console.height):
			rlife = random.choice([3,4,5,6])
			rcolor = random.choice(['white','pink','blue','red','yellow'])
			jump = DynamicEntity(x,y,'#',is_physical = False, lifespan=rlife)
			jump.color = rcolor
			jump.take_turn = graphicalEntityAI


def makeStarJump():
	if player.jump_fuel > 0:
		player.jump_fuel = player.jump_fuel - 1
		initNewDerelict()
		gameObject.playing = False
		gameObject.on_ship = True
		drawStarJump(gameObject.conShipScreen)
		writeToConsole("Powering up jump engines... Jumped!", gameObject.conShipLog,'pink')
	else:
		writeToConsole("Not enough fuel!", gameObject.conShipLog, 'red')
	

ship_menu_options = [["Make star jump (j)",pygame.K_j, makeStarJump],["Launch drone toward derelict (l)",pygame.K_l, launchDrone]]

def drawShipMenu():
	drawMenu(win, SCREEN_WIDTH-1, 8, ship_menu_options, '-|ship console|-',align=[0,0], color = 'white')

def initShipConsoles():
	# start at y=9 to leave space for the menu
	gameObject.conShipScreen = Console(0, 9, SCREEN_WIDTH-1, 20, '-|viewscreen|-')
	gameObject.conShipReadout = Console(0, 30, SCREEN_WIDTH-1, 3, '-|sensor analysis|-')
	gameObject.conShipData = Console(0, 34, SCREEN_WIDTH-1, 3, '-|inventory|-')
	gameObject.conShipLog = Console(0,38, SCREEN_WIDTH-1, 11, '-|log|-')

	writeToConsole("Drone parts: " + str(player.drone_parts) + " in stores.",gameObject.conShipData,'white')
	writeToConsole("Jump fuel units: " + str(player.jump_fuel) + " in stores.",gameObject.conShipData,'white')

	for msg in gameObject.ship_log_messages:
		writeToConsole(msg[0],gameObject.conShipLog,msg[1])

	for i in range(10):
		# draw ten stars
		rx = random.choice(range(1,SCREEN_WIDTH-1-1))
		ry = random.choice(range(1,20-1))
		star = DynamicEntity(rx,ry,'*',is_physical = False, lifespan=100000000)
		star.color = 'white'
		star.take_turn = lambda x: True

def drawShipLog():
	drawConsole(gameObject.conShipLog, win)

	drawConsoleMessages(gameObject.conShipLog)

def drawShipReadout():
	blankConsole(gameObject.conShipReadout)

	writeToConsole("Ship type: Hermes-class freighter.",gameObject.conShipReadout,'white')
	writeToConsole("Ship reactor offline. Cargo area intact. No life signs.",gameObject.conShipReadout,'white')

	drawConsole(gameObject.conShipReadout, win)
	drawConsoleMessages(gameObject.conShipReadout)

def drawShipScreen():
	blankConsole(gameObject.conShipScreen)
	
	# draw stars
	rand = random.choice(range(1,15))
	if rand == 5:
		rx = random.choice(range(1,gameObject.conShipScreen.width-1))
		ry = random.choice(range(1,gameObject.conShipScreen.height-1))
		star = DynamicEntity(rx,ry,'*',is_physical = False, lifespan=100)
		star.color = 'white'
		star.take_turn = graphicalEntityAI
		
	for entity in gameObject.graphical_entity_list:
				putchar(gameObject.conShipScreen.x+entity.x, gameObject.conShipScreen.y+entity.y,entity.char, entity.color,entity.bg_color)


	putchar(gameObject.conShipScreen.x+10, gameObject.conShipScreen.y+5,img_ship,gameObject.derelict_color)
	drawConsole(gameObject.conShipScreen, win)
	drawConsoleMessages(gameObject.conShipScreen)


def drawShipDataConsole():
	blankConsole(gameObject.conShipData)

	writeToConsole("Drone parts: " + str(player.drone_parts) + " in stores.",gameObject.conShipData,'white')
	writeToConsole("Jump fuel units: " + str(player.jump_fuel) + " in stores.",gameObject.conShipData,'white')

	drawConsole(gameObject.conShipData, win)
	drawConsoleMessages(gameObject.conShipData)



####### Init and main loop #######

player = Player(9,5,'@')
player.speed = 1

def initGameConsoles():
	gameObject.conGame = Console(11,0,SCREEN_WIDTH-12,SCREEN_HEIGHT-11, "-|sensors|-") # x, y, width, height, name
	gameObject.conTopLeft = Console(0,0,10,22, "")
	gameObject.conMiddleLeft = Console(0,23,10,11, "-|power|-")
	gameObject.conBottomLeft = Console(0,35,10,9, "-|hull|-")
	gameObject.conBottom = Console(11,SCREEN_HEIGHT-10,SCREEN_WIDTH-12,9, "-|log|-",bottom_margin=1)
	gameObject.conControls = Console(0,45,10,4, "")

	writeToConsole("(r)ecall drone", gameObject.conControls, 'white', "")

def initNewDerelict():

	gameObject.__init__()
	gameObject.console_list = []
	initGameConsoles()

	gameObject.ability_list = []
	abThrust = Ability(img=img_thrust,on_activate=abilityThrustActivate,on_deactivate=abilityThrustDeactivate,name="thrusters",color=TRAIL_COLOR,short_name="(1)")
	abLight = Ability(img=img_light,on_activate=abilityLightActivate,on_deactivate=abilityLightDeactivate,name="exterior lights",color="yellow", short_name = "(2)")
	abLaser = Ability(img=img_laser,on_activate=abilityLaserActivate,on_deactivate=abilityLaserDeactivate,name="drilling laser",color="red", short_name = "(3)")
	
	for ability in gameObject.ability_list:
		writeToConsole(ability.img,ability.console,ability.color,"") # no margin
	
	# generate seed
	enemy_number = random.choice(range(0,5))
	room_density = random.choice(range(5,25))
	room_size = random.choice(range(2,20))

	createRooms(gameObject.conGame, room_density ,room_size)
	createWalls(gameObject.conGame)
	placeDronePart(gameObject.conGame, (math.floor(enemy_number/2))+2)
	placeJumpFuel(gameObject.conGame, 1)

	#place enemeies
	placeEnemies(gameObject.conGame, enemy_number)

	gameObject.derelict_color = random.choice(['red', 'green', 'yellow', 'blue'])

def initNewDrone():


	gameObject.console_list = []
	gameObject.graphical_entity_list = []
	player.__init__(9,5,'@')

	initGameConsoles()

	updatePlayerHealth(gameObject.conBottomLeft, player)
	updatePlayerEnergy(gameObject.conMiddleLeft, player)

	writeToConsole("Drone activated. " + str(player.drone_parts) + " drones remaining.",gameObject.conBottom,'grey')

	setAbilitiesInactive()
	player.calculate_fov()


initNewDerelict()
initNewDrone()

gameObject.playing = True
gameObject.paused = False
gameObject.drone_active = False
gameObject.on_ship = True
while gameObject.playing:


	if gameObject.drone_active:
		drawGame(win, gameObject.conGame, player)

		for entity in gameObject.graphical_entity_list:
			entity.take_turn(entity) # timeout graphical effects


		for entity in gameObject.enemy_list:
			entity.take_turn(player) # move enemies

		# handle keypresses
		
		events = pygame.event.get()
		for event in events:
			if event.type == pygame.KEYDOWN:
				current_input = event.key
				if current_input == pygame.K_DOWN:
					player.move('down')
				elif current_input == pygame.K_UP:
					player.move('up')
				elif current_input == pygame.K_LEFT:
					player.move('left')
				elif current_input == pygame.K_RIGHT:
					player.move('right')
				elif current_input == pygame.K_SPACE:
					player.move('wait')
				elif current_input == pygame.K_1:
					setActiveAbility(gameObject.ability_list[0])
				elif current_input == pygame.K_2:
					setActiveAbility(gameObject.ability_list[1])
				elif current_input == pygame.K_3:
					setActiveAbility(gameObject.ability_list[2])
		handleMenuInputs(game_menu_options, events)

	if gameObject.paused:
		drawPauseMenu()
		while gameObject.paused:
			handleMenuInputs(pause_menu_options)

	if gameObject.on_ship:
		win.setscreencolors(None, 'black', clear=True) # clear
		gameObject.console_list = []
		initShipConsoles()

		while gameObject.on_ship:
			handleMenuInputs(ship_menu_options)
			for entity in gameObject.graphical_entity_list:
				entity.take_turn(entity) # timeout graphical effects
			win.setscreencolors(None, 'black', clear=True) # clear
			drawShipScreen()
			drawShipMenu()
			drawShipDataConsole()
			drawShipReadout()
			drawShipLog()
			win.update()
			

	

			









