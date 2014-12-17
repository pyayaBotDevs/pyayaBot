## pyayaBot_basicFeatureSet.py 
## Author(s): Daniel "Albinohat" Mercado
## This module contains all of the interactive features of the Basic Feature Set.

## TODO [ NOT STARTED ], [ IN-PROGRESS ], [ TESTING ] or [ DONE ]
##
## Implement a !help command to link to the GitHub README. [ NOT STARTED ]
##    Of course this means I also need to make the command reference.
## Implement chat messages letting users know when a feature set's commands are unavailable. [ NOT STARTED ]
##

## BUG FIXES
##

## Standard Imports
import json, re, time

## Third-party imports.
import pyayaBot_main, pyayaBot_qlranksFeatureSet, pyayaBot_threading

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
		if (re.match("^[!@$].+$", t) and self.parent.bool_basic_feature_set == 1):
			return 1
		else:
			return 0

	## checkIfEnabled - This method checks whether or not the feature set is enabled.           
	def checkIfEnabled(self):
		if (self.parent.bool_basic_feature_set == 1):
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
						pyayaBot_threading.WriteLogMessageThread(self.parent.log, "system", pyayaBot_main.SystemMessage(self.parent.log, "INFO", "ADMIN-level SHUTDOWNBOT command issued by " + c.user)).join()
						self.parent.shutdownBot()

				## MOD-level commands - Verify that the User is an op.
				elif (c.level == "OP" and (user.bool_isop == 1 or user.bool_isadmin == 1)):
					## SAVE COMMANDS - These commands save live configuration settings to files to be reused later.
					if (re.match("^save", c.name.lower())):
						## SAVE CHANNEL CONFIG - This command saves the current channel configuration.
						if (re.match("^save\s+channel\s+config$", c.name.lower())):
							self.saveFeatureSetConfig(c)
							self.parent.qlranks_feature_set.saveFeatureSetConfig(c)
	
							self.parent.sendChatMessage("Channel configuration saved Successfully!!")

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
					elif (re.match("^yo$", c.name.lower())):
						self.parent.sendChatMessage("Adrian!")
						pyayaBot_threading.WriteLogMessageThread(self.parent.log, "system", pyayaBot_main.SystemMessage(self.parent.log, "INFO", "OP-level YO command issued by " + c.user)).join()

				## USER-level commands - No User verification required.
				## Update the user's timer for flood protection.
				elif ((c.level == "USER") and (time.time() - user.last_command_time > self.global_cooldown) and (time.time() - user.last_command_time > self.user_cooldown)):
					## BUG COMMAND - Sends the bug report URL to the chat.
					if (re.match("^bug$", c.name.lower())):
						self.parent.sendChatMessage("Bugs and feature requests can be submitted here: https://github.com/pyayaBotDevs/pyayaBot/issues/new")

					## HELP COMMAND - Sends the command reference URL to the chat.
					elif (re.match("^help$", c.name.lower())):
						self.parent.sendChatMessage("pyayaBot Command Reference: http://goo.gl/eh41Vu")

					## MOTD COMMAND - Sends the MOTD to the chat.
					elif (re.match("^motd$", c.name.lower())):
						self.sendMotd()
			
					else:
						bool_valid_command = 0	

					if (bool_valid_command == 1):
						user.updateLastCommandTime()
						
				else:
					pyayaBot_threading.WriteLogMessageThread(self.parent.log, "system", pyayaBot_main.SystemMessage(self.parent.log, "WARNING", "INVALID-level command \"" + c.name + "\" issued by " + c.user + ". Ignoring.")).join()


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
		
	## saveFeatureSetConfig - This method saves the current channel settings to the config file.
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
						pyayaBot_threading.WriteLogMessageThread(self.parent.log, "system", pyayaBot_main.SystemMessage(self.parent.log, "WARNING", "Invalid BasicFeatureSet configuration key \"" + key + "\" detected. Ignoring...")).join()

		json.dump(config_json, config_path, indent=4)

		#self.parent.sendChatMessage("Successfully saved the Basic Feature Set configuration.")
		pyayaBot_threading.WriteLogMessageThread(self.parent.log, "system", pyayaBot_main.SystemMessage(self.parent.log, "INFO", "Successfully saved the BasicFeatureSet configuration.")).join()

	## sendMotd - Sends the message of the day to chat.
	def sendMotd(self):
		self.parent.sendChatMessage(self.getMotd())

	## setMotd - Changes the current message of the day.
	## c       - The command object containing the user and new MOTD text.
	def setMotd(self, c):
		new_value = re.split("\s+", c.name, 2)[2].strip()
		if (len(new_value) > 10 and len(new_value) < 500):
			self.motd = new_value
			self.parent.sendChatMessage("MOTD updated successfully!")
			pyayaBot_threading.WriteLogMessageThread(self.parent.log, "system", pyayaBot_main.SystemMessage(self.parent.log, "INFO", "OP-level MOTD SET command issued by " + c.user + ". New value: " + self.motd + ".")).join()
		
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
			pyayaBot_threading.WriteLogMessageThread(self.parent.log, "system", pyayaBot_main.SystemMessage(self.parent.log, "INFO", "OP-level SET COOLDOWN GLOBAL command issued by " + c.user + ". New value: " + str(self.global_cooldown) + ".")).join()
		
		else:
			self.parent.sendChatMessage("Invalid SET COOLDOWN GLOBAL command. Syntax: @set cooldown global [Number]")
			self.parent.sendChatMessage("Number must be between 0 and 3600.")

	## setCooldownMotd - Changes the time the bot waits between sending the MOTD.
	## c            - The command object containing the user and new MOTD timer.
	def setCooldownMotd(self, c):
		new_value = re.split("\s+", c.name, 3)[3]

		if (new_value.isdigit() and (int(new_value) >= 300 and int(new_value) <= 3600)):
			self.motd_cooldown = float(new_value)
			self.parent.send_motd_thread.updateDelay(self.motd_cooldown)
			self.parent.sendChatMessage("MOTD cooldown updated successfully!")
			pyayaBot_threading.WriteLogMessageThread(self.parent.log, "system", pyayaBot_main.SystemMessage(self.parent.log, "INFO", "OP-level SET COOLDOWN MOTD command issued by " + c.user + ". New value: " + str(self.motd_cooldown) + ".")).join()

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
			pyayaBot_threading.WriteLogMessageThread(self.parent.log, "system", pyayaBot_main.SystemMessage(self.parent.log, "INFO", "OP-level SET COOLDOWN USER command issued by " + c.user + ". New value: " + str(self.user_cooldown) + ".")).join()
		
		else:
			self.parent.sendChatMessage("Invalid SET COOLDOWN USER command. Syntax: @set cooldown user [Number]")
			self.parent.sendChatMessage("Number must be between 0 and 3600.")

	## toggleMotd - This methods toggles whether or not the MOTD should be sent to chat.
	## c               - The command object containing the user and new cooldown.
	def toggleMotd(self, c):
		if (self.bool_motd_enabled == 1):
			self.bool_motd_enabled = 0
			self.parent.sendChatMessage("MOTD Disabled.")
			pyayaBot_threading.WriteLogMessageThread(self.parent.log, "system", pyayaBot_main.SystemMessage(self.parent.log, "INFO", "OP-level TOGGLE MOTD command issued by " + c.user + ". New value: " + str(self.bool_motd_enabled) + ". (Disabled)")).join()
		
		else:
			self.bool_motd_enabled = 1
			self.parent.sendChatMessage("MOTD Enabled.")
			pyayaBot_threading.WriteLogMessageThread(self.parent.log, "system", pyayaBot_main.SystemMessage(self.parent.log, "INFO", "OP-level TOGGLE MOTD command issued by " + c.user + ". New value: " + str(self.bool_motd_enabled) + ". (Enabled)")).join()
		
		self.parent.send_motd_thread.updateBool(self.bool_motd_enabled)
		
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
