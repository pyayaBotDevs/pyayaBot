## pyayaBot_qlranksFeatureSet.py 
## Author(s): Daniel "Albinohat" Mercado
## This module contains all of the interactive features of the QLRanks Feature Set.

## TODO [ NOT STARTED ], [ IN-PROGRESS ], [ TESTING ] or [ DONE ]
## Add support to store information about a player in all gametypes.

## BACKLOG [ NOT STARTED ], [ IN-PROGRESS ], [ TESTING ] or [ DONE ]
##

## BUG FIXES
##

## Standard Imports
import json, re, sys, time, urllib2

## Third-party imports.
import pyayaBot_main, pyayaBot_threading

from bs4 import BeautifulSoup

## This class contains methods which supply information related to the game Quake Live.
class QLRanksFeatureSet():
	## __init__ - This method initializes the command instance.
	## self.parent        - A handle to the parent Bot object.
	## self.best_of_count - The number of games in a match.
	##
	## fs                     - The QLRanksFeatureSet dictionary containing the settings.
	def __init__(self, parent, fs):
		self.parent            = parent
		self.best_of_count     = fs["best_of_count"]

	## addQLPlayer - This method adds a QLPlayer object to the list of QL players.
	## p           - The QLPlayer object to add to the list.
	def addQLPlayer(self, p):
		for player in self.list_of_qlplayers:
			if (player.name == p.name):
				return

		self.list_of_qlplayers.append(p)

	## parseLineFromChat - This method parses through a line of chat (A single chat message) to see if it contains a command.
	## t                 - The line of text to parse.
	def checkIfCommand(self, t):
		if (re.match("^[!@$]qlranks", t)):
			return 1
		else:
			return 0

	## checkIfEnabled - This method checks whether or not the feature set is enabled.           
	def checkIfEnabled(self):
		if (self.parent.bool_qlranks_feature_set == 1):
			return 1
		else:
			return 0

	## checkIfKnownQLPlayer - Returns whether or not the player requested has been cached in the list of QL players.
	## p                    - The name of the player to check.
	def checkIfKnownQLPlayer(self, p):
		for player in self.list_of_qlplayers:
			if (player.name == p):
				return 1

		return 0

	## executeCommand - This method executes a command typed by a user.
	## This method will contain logic to handle QLRanks commands.
	## c              - The command to execute as a Command object.
	def executeCommand(self, c):
		bool_valid_command = 1

		## Look up the User object associated with the username who sent the command.
		for user in self.parent.list_of_users:
			if (user.name == c.user):
				## ADMIN-level commands - Verify that the User is an admin.
				if (c.level == "ADMIN" and user.bool_isadmin == 1):
					print "placeholder"

				## MOD-level commands - Verify that the User is an op.
				elif (c.level == "OP" and (user.bool_isop == 1 or user.bool_isadmin == 1)):
					if (re.match("^qlranks\s+set\s+match\s+bo[13579]+$", c.name.lower())):
						self.setMatchBestOf(c)
						
				## USER-level commands - No User verification required.
				## Update the user's timer for flood protection.
				elif ((c.level == "USER") and (time.time() - user.last_command_time > self.parent.basic_feature_set.global_cooldown) and (time.time() - user.last_command_time > self.parent.basic_feature_set.user_cooldown)):
					## QLRANK LASTGAME COMMAND - Sends info about a player's last played game to the chat.
					if (re.match("^qlranks\s+lastgame\s+[a-zA-Z0-9_]+$", c.name.lower())):
						pyayaBot_threading.SendQLPlayerInfoThread(self.parent, "lastgame", QLPlayer(self.parent.qlranks_feature_set.parseQLRankPage(self.parent.qlranks_feature_set.getQLPlayerSoup(c.name)))).join()

					## QLRANK LASTMATCH COMMAND - Sends info about a player's last played match to the chat.
					elif (re.match("^qlranks\s+lastmatch\s+[a-zA-Z0-9_]+\s+[a-zA-Z0-9_]+$", c.name.lower())):
						pyayaBot_threading.SendQLPlayerInfoThread(self.parent, "lastmatch", QLPlayer(self.parent.qlranks_feature_set.parseQLRankPage(self.parent.qlranks_feature_set.getQLPlayerSoup(c.name)))).join()

					## QLRANK MAPS COMMAND	- Sends a player's 3 most played maps to the chat.
					elif (re.match("^qlranks\s+maps\s+[a-zA-Z0-9_]+$", c.name.lower())):
						pyayaBot_threading.SendQLPlayerInfoThread(self.parent, "maps", QLPlayer(self.parent.qlranks_feature_set.parseQLRankPage(self.parent.qlranks_feature_set.getQLPlayerSoup(c.name)))).join()
				
					## QLRANK PROFILE COMMAND - Sends the URL to a player's QLRanks profile to the chat.
					elif (re.match("^qlranks\s+profile\s+[a-zA-Z0-9_]+$", c.name.lower())):
						pyayaBot_threading.QLPlayerInfoThread(self.parent, "profile", QLPlayer(self.parent.qlranks_feature_set.parseQLRankPage(self.parent.qlranks_feature_set.getQLPlayerSoup(c.name)))).join()
					
					## QRL STATS COMMAND - Sends a player's vitial stats to the chat.
					elif (re.match("^qlranks\s+stats\s+[a-zA-Z0-9_]+$", c.name.lower())):
						pyayaBot_threading.SendQLPlayerInfoThread(self.parent, "stats", QLPlayer(self.parent.qlranks_feature_set.parseQLRankPage(self.parent.qlranks_feature_set.getQLPlayerSoup(c.name)))).join()

					else:
						bool_valid_command = 0
	
					if (bool_valid_command == 1):
						user.updateLastCommandTime()
						
				else:
					pyayaBot_threading.WriteLogMessageThread(self.parent.log, "system", pyayaBot_main.SystemMessage(self.parent.log, "WARNING", "INVALID-level command \"" + c.name + "\" issued by " + c.user + ". Ignoring.")).join()

	## getQLPlayerName - This method returns the name of a given player from a QL command.
	## command_text    - The command text containing name of the player to lookup.
	def getQLPlayerName(self, command_text):
		command_list = re.split("\s+", command_text, 3)

		if (len(command_list) == 3):
			player_name = command_list[2]

		elif (len(command_list) == 4):
			player_name = command_list[2]

		else:
			## This should never execute but is here as a fail-safe. The regex matching in BasicFeatureSet.executeCommand should prevent this from being hit.
			self.parent.sendChatMessage("Invalid QLRANK command: Syntax: !qlrank (stats|maps|lastgame|lastmatch) [Player]") 
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
			player_name = command_list[2]

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
			opponent_name  = ""

			## Give the chat feedback so they know it is wokring.
			self.parent.sendChatMessage("I am looking up \"" + player_name + "\" now...") 

			player_profile = "http://www.qlranks.com/duel/player/" + player_name
			soup           = BeautifulSoup(urllib2.urlopen(player_profile).read())

		## lastmatch takes 2 names.
		elif (len(command_list) == 4):
			player_name    = command_list[2]
			opponent_name  = command_list[3]

			## Give the chat feedback so they know it is wokring.
			self.parent.sendChatMessage("I am looking up \"" + player_name + "\" now...") 

			player_profile = "http://www.qlranks.com/duel/player/" + player_name		
			soup           = BeautifulSoup(urllib2.urlopen(player_profile).read())

		else:
			## This should never execute but is here as a fail-safe. The regex matching in BasicFeatureSet.executeCommand should prevent this from being hit.
			self.parent.sendChatMessage("Invalid QLRANK command: Syntax: !qrl (stats|maps|lastgame) [Player]") 
			self.parent.sendChatMessage("Player must be a QL player's name.")
			sys.exit()

		return player_name, opponent_name, player_profile, soup

	## parseQLRankpage - This method uses BeautifulSoup to parse through HTML pages to extract information about the player.
	## player_tuple    - A tuple containing the player's name, profile and soup of their profile.
	def parseQLRankPage(self, player_tuple):
		player_name    = player_tuple[0]
		opponent_name  = player_tuple[1]
		player_profile = player_tuple[2]
		soup           = player_tuple[3]

		## The player does not exist. Send an error to chat and exit the current thread.
		if (str(soup.title).find(player_name) == -1):
			self.parent.sendChatMessage("No player with name " + player_name + " was found on QLRanks.") 
			sys.exit()

		## Get the vital stats from the stats div and format it nicely for chat.
		player_stats_string = re.sub("(TS %: [0-9]+| \([0-9]+\)| Ladder: [a-zA-Z]+)", "", soup.select("div #stats")[0].get_text().replace("World Rank", "WR").replace("Elo:", "| Elo:").replace("Duels Tracked:", "| Duels:").replace("Win %:", "| Win %:"))

		## Get the top 3 maps played from the inline JS.
		maps_string  = ""
		map_counter  = 0
		player_maps  = re.findall("({label: \"[a-zA-Z0-9_ ]+\", data: [0-9]+\})", str(soup.select("body form div script")))

		for map in player_maps:
			map         = map.replace("label", "\"label\"").replace("data", "\"data\"")
			map_json    = json.loads(map)
			maps_string = maps_string + map_json["label"] + " (" + str(map_json["data"]) + ") " 

			if (map_counter == 2):
				break

			map_counter += 1		

		player_games             = soup.select("table#ctl00_ContentPlaceHolder1_gridPlayerGames tr td")
		player_current_game      = []
		last_match_string        = ""
		last_game_string         = ""
		current_game_string_list = []

		for w in range(self.best_of_count):
			player_current_game = []	
			for x in range(8):
				game_text = player_games[(w * 8) + x].get_text()
				if (re.match("^[a-zA-Z0-9_]+ [0-9]+$", game_text) or re.match("^-?[0-9]+$", game_text)):
					player_current_game.append(re.split("\s+", str(game_text))[0])
					continue

				if (re.match(".*[a-zA-Z0-9_.]+\.jpg.*", str(player_games[(w * 8) + x]))):
					player_current_game.append(re.sub("_[vV0-9_.]+\.jpg", "", re.findall("[a-zA-Z0-9_.]+\.jpg", str(player_games[(w * 8) + x]))[0]))

			if (len(player_current_game) < 5):
				continue

			player_current_game[0] = player_current_game[0] + " "
			player_current_game[1] = player_current_game[1] + " - "
			player_current_game[2] = player_current_game[2] + " "
			player_current_game[3] = player_current_game[3] + " "
			player_current_game[4] = player_current_game[4] + ": "

			current_game_string = player_current_game[4] + player_current_game[0] + player_current_game[1] + player_current_game[2] + player_current_game[3] + "| "
			
			if (w == 0):
				last_game_string = current_game_string

			## The opponent has changed. Stop counting matches.
			if (current_game_string.lower().find(opponent_name.lower()) == -1 and opponent_name != "" and len(last_match_string) > 0):
				print "derp"
				break
			
			if (current_game_string.lower().find(opponent_name.lower()) != -1):
				current_game_string_list.append(current_game_string)

		for game in current_game_string_list:
			last_match_string = last_match_string + game
		
		## Seed the QLPlayer instance. Remove the extra | from the end of the last game and match strings.
		return player_name, last_game_string[:-3], last_match_string[:-3], maps_string, player_profile, player_stats_string

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

	## saveFeatureSetConfig - This method saves the current feature set settings to the config file.
	## c                    - The command object containing the user and new MOTD text.
	def saveFeatureSetConfig(self, c):
		pyayaBot_threading.WriteLogMessageThread(self.parent.log, "system", pyayaBot_main.SystemMessage(self.parent.log, "INFO", "OP-level SAVE CHANNEL CONFIG command issued by " + c.user + ".")).join()

		try:
			config_json = json.load(open(self.parent.channel_config_path))
			
		except IOError:
			print "    pyayaBot_basicFeatureSet.BasicFeatureSet.saveChannelConfig(): Unable to open file: \"" + config_path + ".\""
			self.parent.sendChatMessage("Unable to open the channel configuration file. Unable to save the channel configuration.")
			pyayaBot_threading.WriteLogMessageThread(self.parent.log, "system", pyayaBot_main.SystemMessage(self.parent.log, "ERROR", "Unable to open the channel configuration file. Unable to save the channel configuration.")).join()

		except ValueError:
			print "    pyayaBot_basicFeatureSet.BasicFeatureSet.saveChannelConfig(): Invalid JSON detected."
			self.parent.sendChatMessage("Invalid configuration file format. Unable to save the channel configuration.")
			pyayaBot_threading.WriteToLogMessageThread(self.parent.log, "system", pyayaBot_main.SystemMessage(self.parent.log, "ERROR", "Invalid configuration file format. Unable to save the channel configuration.")).join()

		try:
			config_path = open(self.parent.channel_config_path, "w")

		except IOError:
			print "    pyayaBot_basicFeatureSet.BasicFeatureSet.saveChannelConfig(): Unable to open file: \"" + config_path + ".\""
			self.parent.sendChatMessage("Unable to open the channel configuration file. Unable to save the channel configuration.")
			pyayaBot_threading.WriteLogMessageThread(self.parent.log, "system", pyayaBot_main.SystemMessage(self.parent.log, "ERROR", "Unable to open the channel configuration file. Unable to save the channel configuration.")).join()

		## Parse through each of the key value pairs of the entire JSON payload.
		for fs in config_json["feature_sets"]:
			if (fs["name"] == "QLRanksFeatureSet"):
				for key, value in fs.iteritems():				
					if (key == "best_of_count"):
						fs["best_of_count"] = self.parent.qlranks_feature_set.best_of_count
					else:
						pyayaBot_threading.WriteLogMessageThread(self.parent.log, "system", pyayaBot_main.SystemMessage(self.parent.log, "WARNING", "Invalid QLRanksFeatureSet configuration key \"" + key + "\" detected. Ignoring...")).join()

		json.dump(config_json, config_path, indent=4)

		self.parent.sendChatMessage("Successfully saved the QLRanks Feature Set configuration.")
		pyayaBot_threading.WriteLogMessageThread(self.parent.log, "system", pyayaBot_main.SystemMessage(self.parent.log, "INFO", "Successfully saved the QLRanksFeatureSet configuration.")).join()

	## sendQLPlayerInfo - Sends info about the  specified player to chat.
	## info_type        - The type of player info (lastgame, maps, profile, stats) to send to the chatroom.
	## player           - The object associated with the player whose info should be sent to chat.
	def sendQLPlayerInfo(self, info_type, player):
		if (info_type == "lastgame"):
			self.parent.sendChatMessage(player.last_game)
		elif (info_type == "lastmatch"):
			self.parent.sendChatMessage(player.last_match)		
		elif (info_type == "maps"):
			self.parent.sendChatMessage(player.maps)
		elif (info_type == "profile"):
			self.parent.sendChatMessage(player.profile)
		elif (info_type == "stats"):		
			self.parent.sendChatMessage(player.stats)
		else:
			pyayaBot_threading.WriteLogMessageThread(self.parent.log, "system", pyayaBot_main.SystemMessage(self.parent.log, "WARNING", "Invalid info type \"" + info_type + "\" detected. Ignoring...")).join()

	## setMatchBestOf - This method sets the number of games within a match.
	## command_text    - The command text containing name of the player to lookup.
	def setMatchBestOf(self, c):
		new_value = int(re.split("\s+", c.name, 3)[3][2:])
		
		if (new_value > 0 and new_value < 11):
			self.best_of_count = new_value
			self.parent.sendChatMessage("Best Of Count updated successfully!")
			pyayaBot_threading.WriteLogMessageThread(self.parent.log, "system", pyayaBot_main.SystemMessage(self.parent.log, "INFO", "OP-level QLRANKS SET MATCH BO# command issued by " + c.user + ". New value: " + str(self.best_of_count) + ".")).join()
		else:
			self.parent.sendChatMessage("Invalid QLRANKS SET MATCH BO# command. Syntax: @qlranks set match bo[Number]")
			self.parent.sendChatMessage("Number must be 1, 3, 5, 7 or 9.")

## End of QLRanksFeatureSet class.

## QLPlayer - This class contains various stats for a QL player across all tracked game types.
class QLPlayer():
	## __init__ - This method initializes the command instance.
	## self.name       - The username of the QL player.
	## self.last_game  - The most recent game played by the player.
	## self.last_match - The last match played by the player. Limited by the best of counter and a change of opponent.
	## self.maps       - The 3 top played maps by the player across all game types.
	## self.profile    - The URL of the player's duel profile.
	## self.stats      - Vital stats about the player across all game types. Holds strings for each game type.
	##
	## player_info    - A tuple containing the information about the player.
	def __init__(self, player_info):
		self.name        = player_info[0]
		self.last_game   = player_info[1]
		self.last_match  = player_info[2]
		self.maps        = player_info[3]
		self.profile     = player_info[4]
		self.stats       = player_info[5]

		#self.printQLPlayer()

	## printQLPlayer - This method will print the attributes of the QLPlayer instance.	
	def printQLPlayer(self):
		print "    QLPlayer.printQLPlayer()"
		print "        self.name: " + self.name
		print "        self.last_game: " + self.last_game
		print "        self.last_match: " + self.last_match
		print "        self.maps: " + self.maps
		print "        self.profile: " + self.profile
		print "        self.stats: " + self.stats

	## updateQLPlayer - This method will update the attributes of the QLPlayerInstance.
	## player_info    - A tuple containing the information about the player.
	def updateQLPlayer(self, player_info):
		self.name        = player_info[0]
		self.last_game   = player_info[1]
		self.last_match  = player_info[2]
		self.maps        = player_info[3]
		self.profile     = player_info[4]
		self.stats       = player_info[5]		

## End of QLPlayer class.
