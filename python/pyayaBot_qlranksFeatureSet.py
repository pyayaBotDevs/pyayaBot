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
import json, re, sys, urllib2

## Third-party imports.
import pyayaBot_main, pyayaBot_threading

from bs4 import BeautifulSoup

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

			## Give the chat feedback so they know it is wokring.
			self.parent.sendChatMessage("I am looking up \"" + player_name + "\" now...") 

			player_profile = "http://www.qlranks.com/duel/player/" + player_name
			soup           = BeautifulSoup(urllib2.urlopen(player_profile).read())

		#elif (len(command_list) == 4):
			#player_name    = command_list[3]

			# Give the chat feedback so they know it is wokring.
			#self.parent.sendChatMessage("I am looking up \"" + player_name + "\" now...") 

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

		player_last_game[0] = player_last_game[0] + " (Winner)"
		player_last_game[1] = player_last_game[1] + "-"
		player_last_game[2] = player_last_game[2] + " "
		player_last_game[3] = player_last_game[3] + " "
		player_last_game[4] = "| Map: " + player_last_game[4]

		last_game_string = player_last_game[0] + " VS " + player_last_game[3] + player_last_game[1] + player_last_game[2] + player_last_game[4]

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

	## sendQLPlayerInfo - Sends info about the  specified player to chat.
	## info_type        - The type of player info (lastgame, maps, profile, stats) to send to the chatroom.
	## player           - The object associated with the player whose info should be sent to chat.
	def sendQLPlayerInfo(self, info_type, player):
		if (info_type == "lastgame"):
			self.parent.sendChatMessage("Last game by " + player.name + ": " + player.last_game)
		elif (info_type == "maps"):
			self.parent.sendChatMessage("Top maps played by " + player.name + ": " + player.maps)
		elif (info_type == "profile"):
			self.parent.sendChatMessage(player.name + "'s profile: " + player.profile)
		elif (info_type == "stats"):		
			self.parent.sendChatMessage("Vital stats for " + player.name + ": " + player.stats)
		else:
			pyayaBot_threading.WriteLogMessageThread(self.parent.log, "system", pyayaBot_main.SystemMessage(self.parent.log, "WARNING", "Invalid info type \"" + info_type + "\" detected. Ignoring...")).join()

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

	## updateQLPlayer - This method will update the attributes of the QLPlayerInstance.
	## player_info    - A tuple containing the information about the player.
	def updateQLPlayer(self, player_info):
		self.name        = player_info[0]
		self.last_game   = player_info[1]
		self.maps        = player_info[2]
		self.profile     = player_info[3]
		self.stats       = player_info[4]		

## End of QLPlayer class.
