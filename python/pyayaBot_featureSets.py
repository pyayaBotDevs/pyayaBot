## pyayaBot_featureSets.py 
## Author(s): Daniel "Albinohat" Mercado
## This module contains all of the interactive feature sets for pyayaBot.

## TODO [ NOT STARTED ], [ IN-PROGRESS ], [ TESTING ] or [ DONE ]
##
## ==All Feature Sets==
## Implement multi-threading [ DONE ]
##   Command executions [ DONE ]
##   Logging [ DONE ]
##
## ==BasicFeatureSet==
## Implement log threading. [ NOT STARTED ]
## Implement command flood protection on a global basis. [ DONE ] 
## Implement command flood protection on a per-user basis. [ DONE ]
## Rework MOTD SET into a SET [setting] [ DONE ]
##    Second word is what you are setting. Third + will be the new value.
## Rework MOTD TIMER into a SET TIMER [type] command [ DONE ]
##
## ==ModerationFeatureSet==
## Implement kick/ban detection. [ NOT STARTED ]
##   Requires joining #jtv [ NOT STARTED ] (Work also required in main)
## Insert Admin logging into timeout/ban detection. [ NOT STARTED ]
##
## ==OsuFeatureSet==
## Implement displaying metadata of a YouTube video upon seeing an osu! beatmap link. [ NOT STARTED ]
##
## ==QLRanksFeatureSet==
## Implement QLRanks integration [ DONE ]
##   Implement !qlr command [ DONE ]
##   Implement QLPlayer class [ DONE ]
##
## ==YouTubeFeatureSet==
## Implement displaying metadata of a YouTube video upon seeing a YouTube video link in chat. [ NOT STARTED ]

## BACKLOG [ NOT STARTED ], [ IN-PROGRESS ], [ TESTING ] or [ DONE ]
##
## ==All Feature Sets==
##
## Insert DEBUG-level system logging into existing methods. (Replace  '#' commented out print lines with writeToSystemLog calls) [ NOT STARTED ]
##
## ==QLRanksFeatureSet==
## Add support to store information about a player in all gametypes.

## BUG FIXES
##

## Standard Imports
import json, re, sys, time, urllib2

## Third-party imports.
import pyayaBot_main, pyayaBot_threading

from bs4 import BeautifulSoup

## BasicFeatureSet - Contains methods which supply non-game-specific features in a channel.
class BasicFeatureSet():
	## __init__    - Initialize the attributes of a User object.
	## self.parent            - A handle to the parent Bot object.
	## self.motd              - The message of the day. 
	## self.motd_cooldown     - The time to wait between sending the MOTD to chat.
	## self.bool_motd_enabled - A boolean tracking whether or not the MOTD should be sent to the chat.
	## self.global_cooldown   - The amount of time that must pass before any user can issue consecutive commands.
	## self.user_cooldown     - The amount of time that must pass before a specific user may issue consecutive commands.
	##
	## bfs                    - The BasicFeatureSet dictionary containing the settings.
	def __init__(self, parent, bfs):
		self.parent            = parent
		self.motd              = bfs["motd"]
		self.motd_cooldown     = bfs["motd_cooldown"]
		self.bool_motd_enabled = bfs["bool_motd_enabled"]
		self.global_cooldown   = bfs["global_cooldown"]
		self.user_cooldown     = bfs["user_cooldown"]

		#self.printBasicFeatureSet()

	## parseLineFromChat - This method parses through a line of chat (A single chat message) to see if it contains a command.
	## t                 - The line of text to parse.
	def checkIfCommand(self, t):
		if (re.match("^[!@$].+$", t)):
			return 1
		else:
			return 0

	## executeCommand - This method executes a command typed by a user.
	## This method will contain logic to handle basic commands.
	## c              - The command to execute as a Command object.
	def executeCommand(self, c):
		bool_valid_command = 1

		## Look up the User object associated with the username who sent the command.
		for user in self.parent.list_of_users:
			if (user.name == c.user):
				## ADMIN-level commands - Verify that the User is an admin.
				if (c.level == "ADMIN" and user.bool_isadmin == 1):
					if (re.match("^shutdown$", c.name.lower())):
						pyayaBot_threading.WriteToSystemLogThread(self.parent, pyayaBot_main.SystemMessage(self.parent.log, "INFO", "ADMIN-level SHUTDOWNBOT command issued by " + c.user)).join()
						self.parent.shutdownBot()

				## MOD-level commands - Verify that the User is an op.
				elif (c.level == "OP" and (user.bool_isop == 1 or user.bool_isadmin == 1)):
					## SAVE COMMANDS - These commands save live configuration settings to files to be reused later.
					if (re.match("^save", c.name.lower())):
						## SAVE CHANNEL CONFIG - This command saves the current channel configuration.
						if (re.match("^save\s+channel\s+config$", c.name.lower())):
							self.saveChannelConfig(c)

					## SET Commands - These commands alter live configuration settings.
					elif (re.match("^set", c.name.lower())):
						## SET MOTD - Calls the setMotd method to change the message of the day.
						if (re.match("^set\s+motd\s+", c.name.lower())):
							self.setMotd(c)
						
						## SET COOLDOWN COMMANDS - These commands set various timers to allow/dissalow command executions.
						elif (re.match("^set\s+cooldown", c.name.lower())):
							## SET COOLDOWN GLOBAL - Sets the time that all users must wait before a User-level command can be used.
							if (re.match("^set\s+cooldown\s+global ", c.name.lower())):	
								self.setCooldownGlobal(c)

							## SET TIMER COMMAND - Sets the time that the bot must wait before sending the MOTD to the chat.
							elif (re.match("^set\s+cooldown\s+motd ", c.name.lower())):
								self.setCooldownMotd(c)

							## SET COOLDOWN USER - Sets the time that each user must wait before a User-level command can be used.
							elif (re.match("^set\s+cooldown\s+user ", c.name.lower())):
								self.setCooldownUser(c)
						
					## TOGGLE COMMANDS - These commands toggle booleans to enable/disable features.
					elif (re.match("^toggle", c.name.lower())):
						## TOGGLE MOTD COMMAND - Toggles whether or not the MOTD should be sent to the chat.
						if (re.match("^toggle\s+motd$", c.name.lower())):
							self.toggleMotd(c)

					## YO Command - Simple example of bot responding to user input. Meant for debug purposes.
					elif (re.match("yo", c.name.lower())):
						self.parent.sendChatMessage("Adrian!")
						pyayaBot_threading.WriteToSystemLogThread(self.parent, pyayaBot_main.SystemMessage(self.parent.log, "INFO", "OP-level YO command issued by " + c.user)).join()

				## USER-level commands - No User verification required.
				## Update the user's timer for flood protection.
				elif ((c.level == "USER") and (time.time() - user.last_command_time > self.global_cooldown) and (time.time() - user.last_command_time > self.user_cooldown)):
					## BasicFeatureSet commands - No prefix.
					## MOTD COMMAND - Sends the MOTD to the chat.
					if (re.match("^motd$", c.name.lower())):
						self.sendMotd()

					## QLRanksFeatureSet commands - qrl prefix.
					## QLRANK COMMANDS - These commands offer functionality from QLRanks.com
					elif ((re.match("^qlrank", c.name.lower())) and (self.parent.bool_qlranks_feature_set == 1)):
						## QLRANK LASTGAME COMMAND - Sends info about a player's last played game to the chat.
						if (re.match("^qlrank\s+lastgame\s+[a-zA-Z_]+", c.name.lower())):
							if (self.parent.qlranks_feature_set.checkIfKnownQLPlayer(self.parent.qlranks_feature_set.getQLPlayerName(c.name)) == 0):
								pyayaBot_threading.AddQLPlayerAndSendQLPlayerLastGameThread(self.parent, QLPlayer(self.parent.qlranks_feature_set.parseQLRankPage(self.parent.qlranks_feature_set.getQLPlayerSoup(c.name)))).join()
							else:
								self.parent.qlranks_feature_set.sendQLPlayerLastGame(self.parent.qlranks_feature_set.getQLPlayerObjectByName(c.name))						

						## QLRANK MAPS COMMAND	- Sends a player's 3 most played maps to the chat.
						elif (re.match("^qlrank\s+maps\s+[a-zA-Z0-9_]+", c.name.lower())):
							if (self.parent.qlranks_feature_set.checkIfKnownQLPlayer(self.parent.qlranks_feature_set.getQLPlayerName(c.name)) == 0):
								pyayaBot_threading.AddQLPlayerAndSendQLPlayerMapsThread(self.parent, self.parent, QLPlayer(self.parent.qlranks_feature_set.parseQLRankPage(self.parent.qlranks_feature_set.getQLPlayerSoup(c.name)))).join()
							else:
								self.parent.qlranks_feature_set.sendQLPlayerMaps(self.parent.qlranks_feature_set.getQLPlayerObjectByName(c.name))
						
						## QLRANK PROFILE COMMAND - Sends the URL to a player's QLRanks profile to the chat.
						elif (re.match("^qlrank\s+profile\s+[a-zA-Z0-9_]+", c.name.lower())):
							if (self.parent.qlranks_feature_set.checkIfKnownQLPlayer(self.parent.qlranks_feature_set.getQLPlayerName(c.name)) == 0):
								pyayaBot_threading.AddQLPlayerAndSendQLPlayerProfileThread(self.parent, QLPlayer(self.parent.qlranks_feature_set.parseQLRankPage(self.parent.qlranks_feature_set.getQLPlayerSoup(c.name)))).join()
							else:
								self.parent.qlranks_feature_set.sendQLPlayerProfile(self.parent.qlranks_feature_set.getQLPlayerObjectByName(c.name))
						
						## QRL STATS COMMAND - Sends a player's vitial stats to the chat.
						elif (re.match("^qlrank\s+stats\s+[a-zA-Z0-9_]+", c.name.lower())):
							if (self.parent.qlranks_feature_set.checkIfKnownQLPlayer(self.parent.qlranks_feature_set.getQLPlayerName(c.name)) == 0):
								pyayaBot_threading.AddQLPlayerAndSendQLPlayerStatsThread(self.parent, QLPlayer(self.parent.qlranks_feature_set.parseQLRankPage(self.parent.qlranks_feature_set.getQLPlayerSoup(c.name)))).join()
							else:
								self.parent.qlranks_feature_set.sendQLPlayerStats(self.parent.qlranks_feature_set.getQLPlayerObjectByName(c.name))
						
						else:
							bool_valid_command = 0

					else:
						bool_valid_command = 0		

				if (bool_valid_command == 1):
					user.updateLastCommandTime()

				else:
					pyayaBot_threading.WriteToSystemLogThread(self.parent, pyayaBot_main.SystemMessage(self.parent.log, "WARNING", "INVALID-level command \"" + c.name + "\" issued by " + c.user + ". Ignoring.")).join()

	## getMotd - Returns the message of the day.
	def getMotd(self):
		return self.motd

	## getMotdTimer - Returns the time the bot waits before saying the MOTD to chat.
	def getMotdTimer(self):
		return self.motd_cooldown

	## printBasicFeatureSet - Prints the attributes of the printBasicFeatureSet instance.
	def printBasicFeatureSet(self):
		print "    BasicFeatureSet.printBasicFeatureSet()"
		print "        self.parent: " + str(self.parent)
		print "        self.motd: " + self.motd
		print "        self.motd_cooldown: " + str(self.motd_cooldown)
		print "        self.global_cooldown: " + str(self.global_cooldown)
		print "        self.user_cooldown: " + str(self.user_cooldown)
		
	## saveChannelConfig - This method saves the current channel settings to the config file.
	## c                 - The command object containing the user and new MOTD text.
	def saveChannelConfig(self, c):
		pyayaBot_threading.WriteToSystemLogThread(self.parent, pyayaBot_main.SystemMessage(self.parent.log, "INFO", "OP-level SAVE CHANNEL CONFIG command issued by " + c.user + ".")).join()

		try:
			config_json = json.load(open(self.parent.channel_config_path))
			
		except IOError:
			print "    pyayaBot_featureSets.BasicFeatureSet.saveChannelConfig(): Unable to open file: \"" + config_path + ".\""
			self.parent.sendChatMessage("Unable to open the channel configuration file. Unable to save the channel configuration.")
			pyayaBot_threading.WriteToSystemLogThread(self.parent, pyayaBot_main.SystemMessage(self.parent.log, "ERROR", "Unable to open the channel configuration file. Unable to save the channel configuration.")).join()

		except ValueError:
			print "    pyayaBot_featureSets.BasicFeatureSet.saveChannelConfig(): Invalid JSON detected."
			self.parent.sendChatMessage("Invalid configuration file format. Unable to save the channel configuration.")
			pyayaBot_threading.WriteToSystemLogThread(self.parent, pyayaBot_main.SystemMessage(self.parent.log, "ERROR", "Invalid configuration file format. Unable to save the channel configuration.")).join()

		try:
			config_path = open(self.parent.channel_config_path, "r+")

		except IOError:
			print "    pyayaBot_featureSets.BasicFeatureSet.saveChannelConfig(): Unable to open file: \"" + config_path + ".\""
			self.parent.sendChatMessage("Unable to open the channel configuration file. Unable to save the channel configuration.")
			pyayaBot_threading.WriteToSystemLogThread(self.parent, pyayaBot_main.SystemMessage(self.parent.log, "ERROR", "Unable to open the channel configuration file. Unable to save the channel configuration.")).join()

		
		## Parse through each of the key value pairs of the entire JSON payload.
		for fs in config_json["feature_sets"]:
			if (fs["name"] == "BasicFeatureSet"):
				for key, value in fs.iteritems():
					if (key == "motd"):
						fs["motd"] = self.motd
					elif (key == "motd_cooldown"):
						fs["motd_cooldown"] = self.motd_cooldown
					elif (key == "bool_motd_enabled"):
						fs["bool_motd_enabled"] = self.bool_motd_enabled
					elif (key == "global_cooldown"):
						fs["global_cooldown"] = self.global_cooldown
					elif (key == "user_cooldown"):
						fs["user_cooldown"] = self.user_cooldown
					else:
						pyayaBot_threading.WriteToSystemLogThread(self.parent, pyayaBot_main.SystemMessage(self.parent.log, "WARNING", "Invalid configuration key \"" + key + "\" detected. Ignoring...")).join()

		json.dump(config_json, config_path, indent=4)
		
		self.parent.sendChatMessage("Successfully saved the configuration.")
		pyayaBot_threading.WriteToSystemLogThread(self.parent, pyayaBot_main.SystemMessage(self.parent.log, "INFO", "Successfully saved the configuration.")).join()
		
	## sendMotd - Sends the message of the day to chat.
	def sendMotd(self):
		self.parent.sendChatMessage(self.getMotd())

	## setMotd - Changes the current message of the day.
	## c       - The command object containing the user and new MOTD text.
	def setMotd(self, c):
		new_value = re.split("\s+", c.name, 3)[3].strip()
		if (len(new_value) > 10 and len(new_value) < 500):
			self.motd = re.split("\s+", c.name, 2)[2]
			self.parent.sendChatMessage("MOTD updated successfully!")
			pyayaBot_threading.WriteToSystemLogThread(self.parent, pyayaBot_main.SystemMessage(self.parent.log, "INFO", "OP-level MOTD SET command issued by " + c.user + ". New value: " + self.motd + ".")).join()
		
		else:
			self.parent.sendChatMessage("Invalid SET MOTD command. Syntax: @set motd [Message]")
			self.parent.sendChatMessage("Message must be between 10 and 500 characters long.")

	## setCooldownGlobal - Change the cooldown time between command executions globally.
	## c                 - The command object containing the user and new cooldown.
	def setCooldownGlobal(self, c):
		new_value = re.split("\s+", c.name, 3)[3]

		if (new_value.isdigit() and (int(new_value) >= 0 and int(new_value) <= 3600)):
			self.global_cooldown = float(new_value)		
			self.parent.sendChatMessage("Global cooldown updated successfully!")
			pyayaBot_threading.WriteToSystemLogThread(self.parent, pyayaBot_main.SystemMessage(self.parent.log, "INFO", "OP-level SET COOLDOWN GLOBAL command issued by " + c.user + ". New value: " + str(self.global_cooldown) + ".")).join()
		
		else:
			self.parent.sendChatMessage("Invalid SET COOLDOWN GLOBAL command. Syntax: @set cooldown global [Number]")
			self.parent.sendChatMessage("Number must be between 0 and 3600.")

	## setCooldownMotd - Changes the time the bot waits between sending the MOTD.
	## c            - The command object containing the user and new MOTD timer.
	def setCooldownMotd(self, c):
		new_value = re.split("\s+", c.name, 3)[3]

		if ((int(new_value) >= 300 and int(new_value) <= 3600)):
			self.motd_cooldown = float(new_value)
			self.parent.send_motd_thread.updateDelay(self.motd_cooldown)
			self.parent.sendChatMessage("MOTD cooldown updated successfully!")
			pyayaBot_threading.WriteToSystemLogThread(self.parent, pyayaBot_main.SystemMessage(self.parent.log, "INFO", "OP-level SET COOLDOWN MOTD command issued by " + c.user + ". New value: " + str(self.motd_cooldown) + ".")).join()

		else:
			self.parent.sendChatMessage("Invalid SET COOLDOWN MOTD command. Syntax: @set timer motd [Number]")
			self.parent.sendChatMessage("Number must be between 300 and 3600.")

	## setCooldownUser - Change the cooldown time between command executions for users.
	## c               - The command object containing the user and new cooldown.
	def setCooldownUser(self, c):
		new_value = re.split("\s+", c.name, 3)[3]

		if (new_value.isdigit() and (int(new_value) >= 0 and int(new_value) <= 3600)):
			self.user_cooldown = float(new_value)
			self.parent.sendChatMessage("User cooldown updated successfully!")
			pyayaBot_threading.WriteToSystemLogThread(self.parent, pyayaBot_main.SystemMessage(self.parent.log, "INFO", "OP-level SET COOLDOWN USER command issued by " + c.user + ". New value: " + str(self.user_cooldown) + ".")).join()
		
		else:
			self.parent.sendChatMessage("Invalid SET COOLDOWN USER command. Syntax: @set cooldown user [Number]")
			self.parent.sendChatMessage("Number must be between 0 and 3600.")

	## toggleMotd - This methods toggles whether or not the MOTD should be sent to chat.
	## c               - The command object containing the user and new cooldown.
	def toggleMotd(self, c):
		if (self.bool_motd_enabled == 1):
			self.bool_motd_enabled = 0

			self.parent.sendChatMessage("MOTD Disabled.")
			pyayaBot_threading.WriteToSystemLogThread(self.parent, pyayaBot_main.SystemMessage(self.parent.log, "INFO", "OP-level TOGGLE MOTD command issued by " + c.user + ". New value: " + str(self.bool_motd_enabled) + ". (Disabled)")).join()
		else:
			self.bool_motd_enabled = 1

			self.parent.sendChatMessage("MOTD Enabled.")
			pyayaBot_threading.WriteToSystemLogThread(self.parent, pyayaBot_main.SystemMessage(self.parent.log, "INFO", "OP-level TOGGLE MOTD command issued by " + c.user + ". New value: " + str(self.bool_motd_enabled) + ". (Enabled)")).join()

## End of BasicFeatureSet class.

## Command - Contains the text and level of a command.
class Command():
	## __init__ - This method initializes the command instance.
	## self.user  - The user who issued the command.
	## self.name  - The name of the command without the prefix. (!, @ or #)
	## self.level - The level of access required to execute the command. (USER, MOD or ADMIN)
	##
	## u          - The user who sent the text. Sent from BasicFeatureSet.parseLineFromChat as a string.
	## t          - The text sent from BasicFeatureSet.parseLineFromChat as a string.
	def __init__(self, u, t):
		self.user = u
		self.name = t[1:]

		if (t[0] == "!"):
			self.level = "USER"
		elif (t[0] == "@"):
			self.level = "OP"
		elif (t[0] == "$"):
			self.level = "ADMIN"
		else:
			self.level = "INVALID"
		
		#self.printCommand()

	## printCommand - This method will print the attributes of the BasicFeatureSet.Command instance.
	def printCommand(self):
		print "    BasicFeatureSet.Command.printCommand()"
		print "        self.user: " + self.user
		print "        self.name: " + self.name
		print "        self.level: " + self.level

## End of Command class.			

## This class contains methods which supply information related to the game Quake Live.
class QLRanksFeatureSet():
	## __init__ - This method initializes the command instance.
	## self.parent            - A handle to the parent Bot object.
	## self.list_of_qlplayers - Contains known QLPlayer objects. This allows the bot to cache player info before needlessly reparsing player pages.
	##
	## fs                     - The QLRanksFeatureSet dictionary containing the settings.
	def __init__(self, parent, fs):
		self.parent            = parent
		self.list_of_qlplayers = []

	## addQLPlayer - This method adds a QLPlayer object to the list of QL players.
	## p           - The QLPlayer object to add to the list.
	def addQLPlayer(self, p):
		for player in self.list_of_qlplayers:
			if (player.name == p.name):
				return
		
		self.list_of_qlplayers.append(p)
		
	## checkIfKnownQLPlayer - Returns whether or not the player requested has been cached in the list of QL players.
	## p                    - The name of the player to check.
	def checkIfKnownQLPlayer(self, p):
		for player in self.list_of_qlplayers:
			if (player.name == p):
				return 1

		return 0

	## getQLPlayerName - This method returns the name of a given player from a QL command.
	## command_text    - The command text containing name of the player to lookup.
	def getQLPlayerName(self, command_text):
		command_list = re.split("\s+", command_text, 3)
		
		if (len(command_list) == 3):
			player_name = command_list[2]
		
		elif (len(command_list) == 4):
			player_name = command_list[3]
		
		else:
			## This should never execute but is here as a fail-safe. The regex matching in BasicFeatureSet.executeCommand should prevent this from being hit.
			self.parent.sendChatMessage("Invalid QLRANK command: Syntax: !qrl (stats|maps|lastgame) [Player]") 
			self.parent.sendChatMessage("Player must be a QL player's name.")
			sys.exit()
		
		return player_name
				
	## getQLPlayerObjectByName - This method returns the name of a given player from a QL command.
	## command_text            - The command text containing name of the player to lookup.
	def getQLPlayerObjectByName(self, command_text):
		command_list = re.split("\s+", command_text, 3)
		
		if (len(command_list) == 3):
			player_name = command_list[2]
		
		elif (len(command_list) == 4):
			player_name = command_list[3]
		
		else:
			## This should never execute but is here as a fail-safe. The regex matching in BasicFeatureSet.executeCommand should prevent this from being hit.
			self.parent.sendChatMessage("Invalid QLRANK command: Syntax: !qrl (stats|maps|lastgame) [Player]") 
			self.parent.sendChatMessage("Player must be a QL player's name.")
			sys.exit()
		
		for player in self.list_of_qlplayers:
			if (player.name == player_name):
				return player

	## getQLPlayerSoup - This method returns the soup to parse for a given player.
	## command_text    - The command text containing name of the player to lookup.
	def getQLPlayerSoup(self, command_text):
		command_list = re.split("\s+", command_text, 3)
		
		if (len(command_list) == 3):
			player_name    = command_list[2]
			player_profile = "http://www.qlranks.com/duel/player/" + player_name
			soup           = BeautifulSoup(urllib2.urlopen(player_profile).read())
		
		#elif (len(command_list) == 4):
			#player_name    = command_list[3]
			#player_profile = "http://www.qlranks.com/duel/player/" + player_name		
			#soup           = BeautifulSoup(urllib2.urlopen("http://www.qlranks.com/" + command_list[2] + "/player/" + player_name).read())
		
		else:
			## This should never execute but is here as a fail-safe. The regex matching in BasicFeatureSet.executeCommand should prevent this from being hit.
			self.parent.sendChatMessage("Invalid QLRANK command: Syntax: !qrl (stats|maps|lastgame) [Player]") 
			self.parent.sendChatMessage("Player must be a QL player's name.")
			sys.exit()
			
		return player_name, player_profile, soup

	## parseQLRankpage - This method uses BeautifulSoup to parse through HTML pages to extract information about the player.
	## player_tuple    - A tuple containing the player's name, profile and soup of their profile.
	def parseQLRankPage(self, player_tuple):
		player_name    = player_tuple[0]
		player_profile = player_tuple[1]
		soup           = player_tuple[2]

		## The player does not exist. Send an error to chat and exit the current thread.
		if (str(soup.title).find(player_name) == -1):
			self.parent.sendChatMessage("No player with name " + player_name + " was found on QLRanks.") 
			sys.exit()
		
		## Give the chat feedback so they know it is wokring.
		self.parent.sendChatMessage("I am looked up \"" + player_name + "\" now...") 
		
		## Get the vital stats from the stats div and format it nicely for chat.
		player_stats = soup.select("div #stats")[0].get_text().replace("Elo:", "| Elo:").replace("Ladder:", "| Ladder:").replace("Duels Tracked:", "| Duels Tracked:").replace("Win %:", "| Win %:").replace("TS %:", "| TS %:")
		
		## Get the top 3 maps played from the inline JS.
		maps_string  = ""
		map_counter  = 0
		player_maps  = re.findall("({label: \"[a-zA-Z0-9_ ]+\", data: [0-9]+\})", str(soup.select("body form div script")))
		
		for map in player_maps:
			map         = map.replace("label", "\"label\"").replace("data", "\"data\"")
			map_json    = json.loads(map)
			maps_string = maps_string + map_json["label"] + " (" + str(map_json["data"]) + " Games) " 
			
			if (map_counter == 2):
				break
				
			map_counter += 1		
			
		player_games     = soup.select("table#ctl00_ContentPlaceHolder1_gridPlayerGames tr td")
		player_last_game = []
		
		for x in range(8):
			game_text = player_games[x].get_text()
			if (re.match("^[a-zA-Z0-9_]+ [0-9]+$", game_text) or re.match("^[0-9]+$", game_text)):
				player_last_game.append(re.split("\s+", str(game_text))[0])
				continue

			if (re.match(".*[a-zA-Z0-9_.]+\.jpg.*", str(player_games[x]))):
				player_last_game.append(re.sub("_[vV0-9_.]+\.jpg", "", re.findall("[a-zA-Z0-9_.]+\.jpg", str(player_games[x]))[0]))
		
		player_last_game[0] = player_last_game[0] + "(Winner) "
		player_last_game[1] = player_last_game[1] + "-"
		player_last_game[2] = player_last_game[2] + " "
		player_last_game[3] = player_last_game[3] + " "
		player_last_game[4] = "Map: " + player_last_game[4]
			
		last_game_string = ""
		for game_detail in player_last_game:
			last_game_string = last_game_string + game_detail
		
		return player_name, last_game_string, maps_string, player_profile, player_stats

	## printQLRanksFeatureSet - This method will print the attributes of the QLPlayer instance.	
	def printQLRanksFeatureSet(self):
		print "    QLRanksFeatureSet.printQLRanksFeatureSet()"
		print "        self.list_of_qlplayers: " + self.list_of_qlplayers
		
	## removeQLPlayer - This method removes a QLPlayer object from the list of QL players.
	## p              - The QLPlayer object to remove from the list.
	def removeQLPlayer(self, p):
		for player in self.list_of_qlplayers:
			if (player.name == p.name):
				self.list_of_qlplayers.remove(p)

	## sendQLPlayerLastGame - Sends the last game played by the specified player to chat.
	## player               - The object associated with the player whose info should be sent to chat.
	def sendQLPlayerLastGame(self, player):	
		self.parent.sendChatMessage("Last game by " + player.name + ": " + player.last_game)

	## sendQLPlayerMaps - Sends the top 3 maps played by the specified player to chat.
	## player           - The object associated with the player whose info should be sent to chat.
	def sendQLPlayerMaps(self, player):	
		self.parent.sendChatMessage("Top maps played by " + player.name + ": " + player.maps)

	## sendQLPlayerProfile - Sends the URL of the player's duel profile.
	## player              - The object associated with the player whose info should be sent to chat.
	def sendQLPlayerProfile(self, player):
		self.parent.sendChatMessage(player.name + "'s profile: " + player.profile)
		
	## sendQLPlayerStats - Sends the vital stats of the specified player to chat.
	## player            - The object associated with the player whose info should be sent to chat.
	def sendQLPlayerStats(self, player):
		self.parent.sendChatMessage("Vital stats for " + player.name + ": " + player.stats)

## End of QLRanksFeatureSet class.

## QLPlayer - This class contains various stats for a QL player across all tracked game types.
class QLPlayer():
	## __init__ - This method initializes the command instance.
	## self.name      - The username of the QL player.
	## self.last_game - The most recent game played by the player.
	## self.maps      - The 3 top played maps by the player across all game types.
	## self.profile   - The URL of the player's duel profile.
	## self.stats     - Vital stats about the player across all game types. Holds strings for each game type.
	##
	## player_info    - A tuple containing the information about the player.
	def __init__(self, player_info):
		self.name        = player_info[0]
		self.last_game   = player_info[1]
		self.maps        = player_info[2]
		self.profile     = player_info[3]
		self.stats       = player_info[4]
		
		#self.printQLPlayer()

	## printQLPlayer - This method will print the attributes of the QLPlayer instance.	
	def printQLPlayer(self):
		print "    QLPlayer.printQLPlayer()"
		print "        self.name: " + self.name
		print "        self.last_game: " + str(self.last_game)
		print "        self.maps: " + str(self.maps)
		print "        self.profile: " + self.profile
		print "        self.stats: " + self.stats

## End of QLPlayer class.
