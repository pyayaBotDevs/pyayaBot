## pyayaBot_featureSets.py 
## This module contains all of the interactive feature sets for pyayaBot.

## Imports
import pyayaBot_main, re

## BasicFeatureSet - Contains methods which supply non-game-specific features in a channel.
## self.parent     - A handle to the parent Bot object.
class BasicFeatureSet():
	## __init__    - Initialize the attributes of a User object.
	## self.parent - A handle to the parent Bot object.
	def __init__(self, parent):
		self.parent = parent

	## executeCommand - This method executes a command typed by a user.
	## This method will contain logic to handle basic commands.
	## c              - The command to execute as a Command object.
	def executeCommand(self, c):
		## Admin level commands.
		if (c.level == "ADMIN"):
			## Look up the User object associated with the username who sent the command.
			for user in self.parent.list_of_users:
				if (user.name in c.user):
					## Verify that the User is an admin.
					if (user.bool_isadmin == 1):
						if (c.name == "SHUTDOWNBOT"):
							self.parent.log.writeToSystemLog(self.parent.log.SystemMessage(self.parent.log, "INFO", "ShutDownBot command issued by " + c.user))
							self.parent.shutdownBot()
		
	## parseLineFromChat - This method parses through a line of chat (A single chat message) to see if it contains a command.
	## u                 - The user who sent the line of text.
	## t                 - The line of text to parse.
	def parseLineFromChat(self, u, t):
		bool_iscommand = 0
		if (re.match("^[!@#][a-zA-Z0-9]+$", t)):
			bool_iscommand = 1

		## Only try to execute a command if the line of text fits the command syntax.
		if (bool_iscommand == 1):
			self.executeCommand(self.Command(u, t))
	
	## BasicFeatureSet.Command - Contains the text and level of a command.
	class Command():
		## __init__   - This method initializes the command instance.
		## self.user  - The user who issued the command.
		## self.name  - The name of the command without the prefix. (!, @ or #)
		## self.level - The level of access required to execute the command. (USER, MOD or ADMIN)
		## t          - The text sent from BasicFeatureSet.parseLineFromChat as a string.
		def __init__(self, u, t):
			self.user = u
			self.name = t[1:].upper()
			if (t[0] == "!"):
				self.level = "USER"
			elif (t[0] == "@"):
				self.level = "MOD"
			elif (t[0] == "#"):
				self.level = "ADMIN"
			
		## printCommand - This method will print the attributes of the BasicFeatureSet.Command instance.
		def printCommand(self):
			print "    BasicFeatureSet.Command.printCommand()"
			print "        self.user = " + self.user
			print "        self.name = " + self.name
			print "        self.level = " + self.level
	
	## End of BasicFeatureSet.Command class.
	
## End of BasicFeatureSet class.
			