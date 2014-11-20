## pyayaBot_featureSets.py 
## Author(s): Daniel "Albinohat" Mercado
## This module contains all of the interactive feature sets for pyayaBot.

## TODO [ NOT STARTED ], [ IN-PROGRESS ], [ TESTING ] or [ DONE ]
##
## ==All Feature Sets==
## Implement multi-threading [ IN-PROGRESS ]
##   Command executions [ DONE ]
##
## Insert DEBUG-level system logging into existing methods. (Replace  '#' commented out print lines with writeToSystemLog calls) [ NOT STARTED ]
##
## ==BasicFeatureSet==
## Implement log threading. [ NOT STARTED ]
## Implement command flood protection on a global basis. [ DONE ] 
## Implement command flood protection on a per-user basis. [ DONE ]
## Rework MOTD SET into a SET [setting] [ IN PROGRESS ]
##    Second word is what you are setting. Third + will be the new value.
## Rework MOTD TIMER into a SET TIMER [type] command [NOT STARTED ]
##
## ==ModerationFeatureSet==
## Implement kick/ban detection. [ NOT STARTED ]
## Requires joining #jtv [ NOT STARTED ] (Work also required in main)
## Insert Admin logging into timeout/ban detection. [ NOT STARTED ]
##
## ==OsuFeatureSet==
## Implement displaying metadata of a YouTube video upon seeing an osu! beatmap link. [ NOT STARTED ]
##
## ==QuakeLiveFeatureSet==
## Implement Challonge.com integration [ NOT STARTED ]
## Implement QLRanks integration [ IN-PROGRESS ]
##    Implement !qlplayer command [ IN-PROGRESS ]
##      Implement QLPlayer class [ IN-PROGRESS ]
##
## ==YouTubeFeatureSet==
## Implement displaying metadata of a YouTube video upon seeing a YouTube video link in chat. [ NOT STARTED ]

## BUG FIXES
## Fixed a bug where all commands were subject to cooldowns. Should be user only.

## Standard Imports
import re, time

## Third-party imports.
import pyayaBot_main
from bs4 import BeautifulSoup

## BasicFeatureSet - Contains methods which supply non-game-specific features in a channel.
class BasicFeatureSet():
	## __init__    - Initialize the attributes of a User object.
	## self.parent          - A handle to the parent Bot object.
	## self.motd            - The message of the day. 
	## self.motd_timer      - The time to wait between sending the MOTD to chat.
	## self.global_cooldown - The amount of time that must pass before any user can issue consecutive commands.
	## self.user_cooldown   - The amount of time that must pass before a specific user may issue consecutive commands.
	def __init__(self, parent):
		self.parent          = parent
		self.motd            = "Good day! We hope you enjoy your stay here on " + self.parent.channel + "!"
		self.motd_timer      = 60.000
		self.global_cooldown = 0.000
		self.user_cooldown   = 0.000

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
		## Look up the User object associated with the username who sent the command.
		for user in self.parent.list_of_users:
			if (user.name == c.user):
				## ADMIN-level commands - Verify that the User is an admin.
				if (c.level == "ADMIN" and user.bool_isadmin == 1):
					if (re.match("^shutdown$", c.name.lower())):
						self.parent.log.writeToSystemLog(pyayaBot_main.SystemMessage(self.parent.log, "INFO", "ADMIN-level SHUTDOWNBOT command issued by " + c.user))
						self.parent.shutdownBot()

				## MOD-level commands - Verify that the User is an op.
				elif (c.level == "OP" and (user.bool_isop == 1 or user.bool_isadmin == 1)):
					## YO Command - Simple example of bot responding to user input.
					if (re.match("yo", c.name.lower())):
						self.parent.sendChatMessage("Adrian!")
						self.parent.log.writeToSystemLog(pyayaBot_main.SystemMessage(self.parent.log, "INFO", "OP-level YO command issued by " + c.user))

					## SET Commands
					if (re.match("^set", c.name.lower())):
						## SET MOTD - Calls the setMotd method to change the message of the day.
						if (re.match("^set motd ", c.name.lower())):
							self.setMotd(c)

						## SET TIMER Commands
						## SET TIMER MOTD - Sets the time the bot waits between saying the message of the day. 
						elif (re.match("^set timer motd ", c.name.lower())):
							self.setMotdTimer(c)

						elif (re.match("^set cooldown global ", c.name.lower())):	
							self.setGlobalCooldown(c)

						elif (re.match("^set cooldown user ", c.name.lower())):
							self.setUserCooldown(c)

				## USER-level commands - No User verification required.
				## Update the user's timer for flood protection.
				elif ((c.level == "USER") and (time.time() - user.last_command_time > self.global_cooldown) and (time.time() - user.last_command_time > self.user_cooldown)):
					bool_valid_command = 1

					## BasicFeatureSet commands.
					if (re.match("^motd$", c.name.lower())):
						self.sendMotd()

					## QuakeLiveFeatureSet commands.
					elif (re.match("^qlplayer stats (duel|ca|tdm|ctf|ffa) [a-zA-Z_]+", c.name.lower())):
						if (self.parent.quakelive_feature_set.checkIfKnownQLPlayer(c.name) == 0):
							print "placeholder"
						self.parent.quakelive_feature_set.getQLRPlayerStats(c)
					elif (re.match("^qlplayer topmaps (duel|ca|tdm|ctf|ffa) [a-zA-Z_]+", c.name.lower())):
						if (self.parent.quakelive_feature_set.checkIfKnownQLPlayer(c.name) == 0):
							print "placeholder"
						self.parent.quakelive_feature_set.getQLRPlayerMaps(c)
					elif (re.match("^qlplayer recentgames (duel|ca|tdm|ctf|ffa) [a-zA-Z_]+", c.name.lower())):
						if (self.parent.quakelive_feature_set.checkIfKnownQLPlayer(c.name) == 0):
							print "placeholder"
						self.parent.quakelive_feature_setgetQLRPlayerRecentGames(c)
					else:
						bool_valid_command = 0

					if (bool_valid_command == 1):
						user.updateLastCommandTime()

				else:
					self.parent.log.writeToSystemLog(pyayaBot_main.SystemMessage(self.parent.log, "WARNING", "INVALID-level command \"" + c.name + "\" issued by " + c.user + ". Ignoring."))

	## getMotd - Returns the message of the day.
	def getMotd(self):
		return self.motd

	## getMotdTimer - Returns the time the bot waits before saying the MOTD to chat.
	def getMotdTimer(self):
		return self.motd_timer

	## printBasicFeatureSet - Prints the attributes of the printBasicFeatureSet instance.
	def printBasicFeatureSet(self):
		print "    BasicFeatureSet.printBasicFeatureSet()"
		print "        self.parent: " + str(self.parent)
		print "        self.motd: " + self.motd
		print "        self.motd_timer: " + str(self.motd_timer)

	## sendMotd - Sends the message of the day to chat.
	def sendMotd(self):
		self.parent.sendChatMessage(self.getMotd())

	## setMotd - Changes the current message of the day.
	## c       - A command instance containing the new message to set as the message of the day.
	def setMotd(self, c):
		if (len(c.name) > 18 and len(c.name) < 260):
			self.motd = c.name.split(" ", 2)[2]
			self.parent.sendChatMessage("MOTD updated successfully!")
			pyayaBot_main.LogFairy.writeToSystemLog(pyayaBot_main.SystemMessage(self.parent.log, "INFO", "OP-level MOTD SET command issued by " + c.user))
		else:
			self.parent.sendChatMessage("Invalid SET MOTD command. Syntax: @set motd [Message]")
			self.parent.sendChatMessage("Message must be between 10 and 250 characters.")

	## setGlobalCooldown - Change the cooldown time between command executions globally.
	## c                 - A command instance containing the new time (in seconds) to wait between sending the MOTD.
	def setGlobalCooldown(self, c):
		new_value = c.name.split(" ", 3)[3]

		if (new_value.isdigit() and (int(new_value) >= 0 and int(new_value) <= 3600)):
			self.global_cooldown = float(new_value)
			
			self.parent.sendChatMessage("Global cooldown updated successfully!")
			self.parent.log.writeToSystemLog(pyayaBot_main.SystemMessage(self.parent.log, "INFO", "OP-level SET COOLDOWN GLOBAL command issued by " + c.user))
		else:
			self.parent.sendChatMessage("Invalid SET COOLDOWN GLOBAL command. Syntax: @set cooldown global [Number]")
			self.parent.sendChatMessage("Number must be between 0 and 3600.")

	## setUserCooldown - Change the cooldown time between command executions for users.
	## c               - A command instance containing the new time (in seconds) to wait between sending the MOTD.
	def setUserCooldown(self, c):
		new_value = c.name.split(" ", 3)[3]

		if (new_value.isdigit() and (int(new_value) >= 0 and int(new_value) <= 3600)):
			self.user_cooldown = float(new_value)

			self.parent.sendChatMessage("User cooldown updated successfully!")
			self.parent.log.writeToSystemLog(pyayaBot_main.SystemMessage(self.parent.log, "INFO", "OP-level SET COOLDOWN USER command issued by " + c.user))
		else:
			self.parent.sendChatMessage("Invalid SET COOLDOWN USER command. Syntax: @set cooldown user [Number]")
			self.parent.sendChatMessage("Number must be between 0 and 3600.")

	## setMotdTimer - Changes the time the bot waits between sending the MOTD.
	## c            - A command instance containing the new time (in seconds) to wait between sending the MOTD.
	def setMotdTimer(self, c):
		new_value = c.name.split(" ", 3)[3]

		if (new_value.isdigit() and (int(new_value) >= 300 and int(new_value) <= 3600)):
			self.motd_timer = float(new_value)
			self.parent.send_motd_thread.updateDelay(self.motd_timer)

			self.parent.sendChatMessage("MOTD timer updated successfully!")
			self.parent.log.writeToSystemLog(pyayaBot_main.SystemMessage(self.parent.log, "INFO", "OP-level SET TIMER MOTD command issued by " + c.user))
		else:
			self.parent.sendChatMessage("Invalid SET TIMER MOTD command. Syntax: @set timer motd [Number]")
			self.parent.sendChatMessage("Number must be between 300 and 3600.")
			
## End of BasicFeatureSet class.

## Command - Contains the text and level of a command.
class Command():
	## __init__ - This method initializes the command instance.
	## self.user  - The user who issued the command.
	## self.name  - The name of the command without the prefix. (!, @ or #)
	## self.level - The level of access required to execute the command. (USER, MOD or ADMIN)
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
		print "        self.user = " + self.user
		print "        self.name = " + self.name
		print "        self.level = " + self.level

## End of Command class.			

## This class contains methods which supply information related to the game Quake Live.
class QuakeLiveFeatureSet():
	## __init__ - This method initializes the command instance.
	## self.parent            - A handle to the parent Bot object.
	## self.list_of_qlplayers - Contains known QLPlayer objects. This allows the bot to cache player info before needlessly reparsing player pages.
	def __init__(self, parent):
		self.list_of_qlplayers = []

	## checkIfKnownQLPlayer - Returns whether or not the player requested has been cached in the list of QL players.
	def checkIfKnownQLPlayer(self, name):
		for player in self.list_of_qlplayers:
			if (player == name):
				return 1

		return 0

	## getQLRPlayerMaps - Returns the [number] most played maps for the given user.
	## c                - A command instance containing the player name and
	def getQLRPlayerMaps(self, c):
		print "Placeholder"

	## getQLRPlayerStats - Returns the vital stats the play specified.
	def getQLRPlayerStats(self, c):
		print "Placeholder"

	## getQLRPlayerRecentMatches - Returns [number] of the player's most recent matches.
	def getQRLPlayerRecentMatches(self, c):
		print "Placeholder"

	## parseQLRankpage - This method uses BeautifulSoup to parse through HTML pages to extract information about the player.
	def parseQLRankpage(self, c):
		print "placeholder"

## End of QuakeLiveFeatureSet class.

## QLPlayer - This class contains various stats for a QL player across all tracked game types.
class QLPlayer():
	## __init__ - This method initializes the command instance.
	## self.name        - The username of the QL player.
	## self.stats       - Vital stats about the player across all game types. Holds strings for each game type.
	## self.maps        - The top played maps by the player across all game types.
	## self.recentgames - The recent games played by the player.
	def __init__():
		self.name = "Placeholder"

## End of QLPlayer class.
