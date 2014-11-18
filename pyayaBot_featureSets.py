## pyayaBot_featureSets.py 
## Author(s): Daniel "Albinohat" Mercado
## This module contains all of the interactive feature sets for pyayaBot.

## TODO [ NOT STARTED ], [ IN-PROGRESS ], [ TESTING ] or [ DONE ]
##
## ==All Feature Sets==
## Implement multi-threading [ DONE ]
##   Command executions [ DONE ]
##
## Insert DEBUG-level system logging into existing methods. (Replace  '#' commented out print lines with writeToSystemLog calls) [ NOT STARTED ]
##
## ==BasicFeatureSet==
## Implement kick/ban detection. [ NOT STARTED ]
## Insert Admin logging into kick/ban detection. [ NOT STARTED ]
##
## ==OsuFeatureSet==
## Implement displaying metadata of a YouTube video upon seeing an osu! beatmap link. [ NOT STARTED ]
##
## ==QuakeLiveFeatureSet==
## Implement Challonge.com integration [ NOT STARTED ]
## Implement QLRanks integration [ NOT STARTED ]
##
## ==YouTubeFeatureSet==
## Implement displaying metadata of a YouTube video upon seeing a YouTube video link in chat. [ NOT STARTED ]

## BUG FIXES
## Fixed a bug where sending unexpected admin-level or op-level could cause a crash.

## Standard Imports
import re

## Third-party imports.
import pyayaBot_main
from bs4 import BeautifulSoup

## BasicFeatureSet - Contains methods which supply non-game-specific features in a channel.
## self.parent     - A handle to the parent Bot object.
## self.motd       - The message of the day. 
## self.motd_timer - The time to wait between sending the motd to chat.
class BasicFeatureSet():
	## __init__    - Initialize the attributes of a User object.
	## self.parent - A handle to the parent Bot object.
	def __init__(self, parent):
		self.parent     = parent
		self.motd       = "Good day! We hope you enjoy your stay here on " + self.parent.channel + "!"
		self.motd_timer = 0
	
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
					if (c.name == "SHUTDOWNBOT"):
						self.parent.log.writeToSystemLog(self.parent.log.SystemMessage(self.parent.log, "INFO", "ADMIN-level SHUTDOWNBOT command issued by " + c.user))
						self.parent.shutdownBot()
				
				## MOD-level commands - Verify that the User is an op.
				if (c.level == "OP" and user.bool_isop == 1):
					## YO Command - Simple example of bot responding to user input.
					if (c.name == "YO"):
						self.parent.sendChatMessage("Adrian!")
						self.parent.log.writeToSystemLog(self.parent.log.SystemMessage(self.parent.log, "INFO", "OP-level YO command issued by " + c.user))

					## MOTD Commands
					## SET - Calls the setMotd method to change the message of the day.
					if (c.name[0:9] == "MOTD SET "):
						self.setMotd(c)
					
					## TIMER - Sets the time the bot waits between saying the message of the day. 
					elif (c.name[0:11] == "MOTD TIMER "):	
						self.setMotdTimer(c)
				
				## USER-level commands - No User verification required.
				if (c.level == "USER"):
					if (c.name == "MOTD"):
						self.sendMotd()
		
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
			self.motd = c.name[9:]
			self.parent.sendChatMessage("MOTD updated successfully!")
			self.parent.log.writeToSystemLog(self.parent.log.SystemMessage(self.parent.log, "INFO", "OP-level MOTD SET command issued by " + c.user))
		else:
			self.parent.sendChatMessage("Invalid MOTD SET command. Syntax: @MOTD SET [Message]")
			self.parent.sendChatMessage("Message must be between 10 and 250 characters.")

	## setMotdTimer - Changes the time the bot waits between sending the MOTD.
	## c            - A command instance containing the new time (in seconds) to wait between sending the MOTD.
	def setMotdTimer(self, c):
		c.name = c.name.lstrip().rstrip()
		if (c.name[11:].isdigit() and (int(c.name[11:]) > 0 and int(c.name[11:]) <= 3600)):
			self.motd_timer = c.name[11:0]
			self.parent.sendChatMessage("MOTD timer updated successfully!")
			self.parent.log.writeToSystemLog(self.parent.log.SystemMessage(self.parent.log, "INFO", "OP-level MOTD TIMER command issued by " + c.user))
		else:
			self.parent.sendChatMessage("Invalid MOTD TIMER command. Syntax: @MOTD SET [Number]")
			self.parent.sendChatMessage("Number must be between 0 and 3600.")

	## BasicFeatureSet.Command - Contains the text and level of a command.
	class Command():
		## __init__   - This method initializes the command instance.
		## self.user  - The user who issued the command.
		## self.name  - The name of the command without the prefix. (!, @ or #)
		## self.level - The level of access required to execute the command. (USER, MOD or ADMIN)
		## u          - The user who sent the text. Sent from BasicFeatureSet.parseLineFromChat as a string.
		## t          - The text sent from BasicFeatureSet.parseLineFromChat as a string.
		def __init__(self, u, t):
			self.user = u
			
			t_list = t.split(" ", 3)
			
			## Make the command upper case.
			if (len(t_list) == 1):
				self.name = t_list[0][1:].upper()
			elif (len(t_list) == 3 and t_list[0].upper() == "@MOTD"):
				self.name = t_list[0].upper() + " " + t_list[1].upper() + " " + t_list[2]
			else:
				self.name = "INVALID"
			if (t[0] == "!"):
				self.level = "USER"
			elif (t[0] == "@"):
				self.level = "OP"
			elif (t[0] == "$"):
				self.level = "ADMIN"
		
			#self.printCommand()
		
		## printCommand - This method will print the attributes of the BasicFeatureSet.Command instance.
		def printCommand(self):
			print "    BasicFeatureSet.Command.printCommand()"
			print "        self.user = " + self.user
			print "        self.name = " + self.name
			print "        self.level = " + self.level
	
	## End of BasicFeatureSet.Command class.
	
## End of BasicFeatureSet class.
			