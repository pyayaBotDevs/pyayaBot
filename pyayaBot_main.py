##pyayaBot_main.py
##The main body of a twitch bot which listens for IRC Messages and offers features from the pyayaBot_features module.

## TODO
## Objectify Messages [ DONE ]
## Print out PONGs. [ DONE ]
## Write method to allow bot to send chat messages. [ DONE ]
## Reimplement user management. [ DONE ]
## Reimplement the admin list. [ DONE ]
## Write methods to print out the admin and op lists. [ DONE ]
## Implement system logging bitmask. [ DONE ]
## Implement feature sets into the __init__ of Bot class. [ DONE ]
## Update configuration file format and parser to support feature sets and comments. [ DONE ]
## Split the configuration file into connection_config and channel_config [ DONE ]
## Insert system logging into existing methods. [ DONE ]
## Insert IRC logging into existing methods. [ DONE ]
## Insert chat logging into existing methods. [ DONE ]
## Implement 4th log for administrative tasks. (add/removal of ops/admins + bans/timeouts.) [ DONE ]
## Insert admin logging into existing methods. [ DONE ]
## Insert DEBUG-level system logging into existing methods. (Replace  '#' commented out print lines with writeToSystemLog calls) [ NOT STARTED ]
## Split the checkIf methods of the User class to getters and setters.

## Imports
import pyayaBot_featureSets, socket, re, sys, time, os, subprocess

## Bot - This class contains the most basic operations of pyayaBot.
class Bot():
	## __init__                  - This method sets up the bot using a configuration file, connects to the twitch IRC server and starts the main listening loop.
	## self.host                 - The IP of the twitch.tv IRC server.
	## self.port                 - The port of the twitch.tv IRC server.
	## self.nick                 - The nickname (username) of the Bot instance.
	## self.oauth                - The password (OAuth token) of the Bot instance.
	## self.ident                - The identity of the Bot instance. (Must be the same as nickname)
	## self.realname             - Used as a credits field. Please always initialize to give credits to Albinohat.
	## self.channel              - The channel the bot will join. A single bot instance must join only one channel at a time. (For now)
	## self.log_dir              - The absolute or relative paths to the directory in which log files will be stored.				
	## self.syslog_bitlist       - A bit mask supplied as a list of bools which determines what types of log entries to write.
	##                     Index - Value
	##					       0 - System > INFO
	##					       1 - System > WARNING
	##					       2 - System > ERROR
	##					       3 - System > DEBUG
	## self.log                  - A LogFairy object which will handle writing out log entries.
	## self.twitch               - A socket object which will contain the IP/port pairs between the local machine and the twitch.tv IRC server.
	## self.list_of_feature_sets - A list of strings denoting which feature	sets the bot will use.
	## self.list_of_users        - A list of User objects to track users in a channel.
	## self.list_of_admins       - A list of strings containing the usernames of admins. (Broadcast + albinohat)
	## self.list_of_ops          - A list of strings containing the usernames of channel operators.
	## connection_config_path    - The absolute or relative path to the connection configuration file to initialize the Bot instance.
	## channel_config_path       - The absolute or relative path to the channel configuration file to initialize the Bot instance.
	## syslog_bitlist            - The list of binary values controlling which system logging types are enabled.
	def __init__(self, connection_config_path, channel_config_path, syslog_bitlist):
		## Initialize the logging bitmask and lists of users and ops.	
		self.syslog_bitlist       = syslog_bitlist
		self.list_of_feature_sets = []
		self.list_of_users        = []
		## Admin list is maintained by the broadcaster. (ADMIN-level commands)
		self.list_of_admins       = []
		## Op list is maintained by the twitch.tv IRC server. (MODE messages)
		self.list_of_ops          = []
			
		## Call the method to parse the connection and channel configuration files.
		## This will initialize all required attributes to spin-up logging and connect to the twitch.tv IRC server.
		self.parseConnectionConfigFile(connection_config_path)
		self.parseChannelConfigFile(channel_config_path)
		
		## Initialize the LogFairy object using the log directory.
		self.log = LogFairy(self.channel, self.log_dir, self.syslog_bitlist)
		
		## Call the method to connect to the twitch.tv IRC server.
		self.connectToTwitch()
		
		## Call the method to initialize the various feature set objects.
		self.initializeFeatureSets()

		## Add the broadcaster and devs to the list of admins.
		self.addAdmin(self.channel)
		self.addAdmin("albinohat")
		self.addAdmin("wrongwarped")
		
		#self.printAdmins()
		#self.printOps()
		
		## Call the method to listen for messages from the twitch.tv IRC server.
		self.listenLoop()
	
	## addAdmin - Adds a username to the list of administrators (Broadcaster + others). 
	## Only adds the username if it isn't in the list yet.
	## n        - The username of the user to add to the list.
	def addAdmin(self, n):
		## Format the name in the long-version used by twitch.
		n = ":" + n + "!" + n + "@" + n + ".tmi.twitch.tv"
		
		## Avoid readding a username to the list.
		for admin in self.list_of_admins:
			if (admin == n):
				return
	
		self.list_of_admins.append(n)
		self.log.writeToAdminLog(self.log.AdminMessage(self.log, "ADDED ADMIN", n))
		
		## Update the user object's isadmin boolean.
		for user in self.list_of_users:
			if (user.name == n):
				user.setIsAdmin(1)
		
		#self.printAdmins()
		
	## addOp - Adds a username to the list of operators (mods). 
	## Only adds the username if it isn't in the list yet.
	## n     - The username of the user to add to the list.
	def addOp(self, n):
		## Format the name in the long-version used by twitch.
		n = ":" + n + "!" + n + "@" + n + ".tmi.twitch.tv"
		
		## Avoid readding a username to the list.
		for op in self.list_of_ops:
			if (op == n):
				return
		
		self.list_of_ops.append(n)
		self.log.writeToAdminLog(self.log.AdminMessage(self.log, "ADDED OP", n))

		## Update the user object's isop boolean.
		for user in self.list_of_users:
			if (user.name == n):
				user.setIsOp(1)
				
		#self.printOps()
		
	## addUser - Adds the specified username to the list of operators (mods).
	## u       - A User object.
	def addUser(self, u):
		self.list_of_users.append(u)
	
	## getIfKnownUser - This method will loop through the list of User objects.
	## It returns 0 if the user is not tracked in the list of users.
	## It returns 1 if the user is tracked in the list of users.
	## n                - The username of someone in the channel to check.
	def getIfKnownUser(self, n):
		bool_known = 0
		for user in self.list_of_users:
			if (n == user.name):
				bool_known = 1
				break
		
		return bool_known
		
	## connectToTwitch - This method connects to the twitch IRC server and joins the configured channel.
	def connectToTwitch(self):
		## Open the connection to twitch IRC and join the channel specified in the config file.
		self.twitch = socket.socket()
		self.twitch.connect((self.host, self.port))
		self.twitch.send("PASS %s\r\n" % self.oauth) 
		self.twitch.send("NICK %s\r\n" % self.nick)
		self.twitch.send("USER %s %s bla :%s\r\n" % (self.ident, self.host, self.realname))
		self.twitch.send("JOIN #%s\r\n" % self.channel)
		
		self.log.writeToSystemLog(self.log.SystemMessage(self.log, "INFO", "Successfully connected to twitch.tv IRC Server. (" + self.host + " Port " + str(self.port) + ")"))
		
	## initializeFeatureSets - This method initializes feature set objects.
	def initializeFeatureSets(self):
		## Initialize bools to enable or disable feature sets.
		self.bool_basic_feature_set = 0
		
		## Call the methods to initialize the specified feature sets in the list.
		for fs in self.list_of_feature_sets:
			## Initialize a BasicFeatureSet instance.
			if (fs == "BasicFeatureSet"):
				self.basic_feature_set = pyayaBot_featureSets.BasicFeatureSet(self)
				self.bool_basic_feature_set = 1
		
	## listenLoop - This method enters an infinite loop and listens for text from the twitch.tv IRC Server.
	def listenLoop(self):
		read_buffer = ""
		while (1):
			## Split data received from the twitch.tv IRC server into lines.
			read_buffer = self.twitch.recv(4096)
			temp = read_buffer.split("\n", 10000)
			for line in temp:
				if (line != "" and line != "\n" and line != "\r\n"):
					print line
					self.parseLineFromTwitch(line.rstrip())
		
	## parseChannelConfigFile - This method opens the channel configuration file and parses it to ensure the correct values are set to initialize the Bot instance.
	def parseChannelConfigFile(self, config_path):
		try:
			config_file = open(config_path, "r")
		except IOError:
			print "    pyayaBot.Bot.parseChannelConfigFile(): Unable to open file: \"" + config_path + ".\""
			sys.exit()
			
		for line in config_file:
			## Do not parse comment lines.
			if (line[0] == "#" or line == ""):
				continue
			self.line_list = line.split("=", 1)
			if (self.line_list[0] == "CHANNEL"):
				self.channel = self.line_list[1].rstrip()
			elif (self.line_list[0] == "FEATURESET"):
				self.list_of_feature_sets.append(self.line_list[1].rstrip())
			else:
				print "    pyayaBot.Bot.parseChannelConfigFile(): Invalid config entry: \"" + self.line_list[0] + ".\" Ignoring..."

		if (self.channel == "" or len(self.list_of_feature_sets) == 0):
			print "    pyayaBot.Bot.parseChannelConfigFile(): One or more configuration entries were not set."
			print "    Please verify the configuration file's contents and try again."
			sys.exit()
		
		config_file.close()
		
	## parseConnectionConfigFile - This method opens the connection configuration file and parses it to ensure the correct values are set to initialize the Bot instance.
	def parseConnectionConfigFile(self, config_path):
		try:
			config_file = open(config_path, "r")
		except IOError:
			print "    pyayaBot.Bot.parseConnectionConfigFile(): Unable to open file: \"" + config_path + ".\""
			sys.exit()
			
		for line in config_file:
			## Do not parse comment lines.
			if (line[0] == "#" or line == ""):
				continue
			self.line_list    = line.split("=", 1)
			if (self.line_list[0] == "HOST"):
				self.host     = self.line_list[1].rstrip()
			elif (self.line_list[0] == "PORT"):
				self.port     = int(self.line_list[1].rstrip(), base=10)
			elif (self.line_list[0] == "NICK"):
				self.nick     = self.line_list[1].rstrip()
				self.ident    = self.nick
			elif (self.line_list[0] == "PASS"):
				self.oauth    = self.line_list[1].rstrip()
			elif (self.line_list[0] == "REALNAME"):			
				self.realname = self.line_list[1].rstrip()
			elif (self.line_list[0] == "LOG_DIR"):			
				self.log_dir  = self.line_list[1].rstrip()				
			else:
				print "    pyayaBot.Bot.parseConnectionConfigFile(): Invalid config entry: \"" + self.line_list[0] + ".\" Ignoring..."

		if (self.host == "" or self.port == 0 or self.nick == "" or self.oauth == "" or self.realname == ""):
			print "    pyayaBot.Bot.parseConnectionConfigFile(): One or more configuration entries were not set."
			print "    Please verify the configuration file's contents and try again."
			sys.exit()
		
		config_file.close()
			
	## parseLineFromTwitch - This method will parse a line of text form the twitch.tv IRC server, splitting it up and determining its log type and corresponding values.
	## line                - The message sent from listenLoop().
	def parseLineFromTwitch(self, line):
		line_parts = line.split(" ", 3)
		if (re.match("[0-9]{3}", line_parts[1])):
			type = line_parts[1]
			body = line_parts[3].rstrip()
			self.log.writeToIRCLog(self.log.IRCMessage(self.log, type, body))
		
		elif (line_parts[1] == "JOIN"):
			type = line_parts[1]
			body = line_parts[0].rstrip()
			self.log.writeToIRCLog(self.log.IRCMessage(self.log, type, body))
			
			## Check if the user is tracked. If not, add the user to the list.
			if (self.getIfKnownUser(body) == 0):
				self.addUser(self.User(self, body))
				
		elif (line_parts[1] == "PART"):
			type = line_parts[1]
			body = line_parts[0].rstrip()
			self.log.writeToIRCLog(self.log.IRCMessage(self.log, type, body))
			
			## Remove the user from the list of tracked users.
			self.removeUser(body)
		
		elif (line_parts[1] == "MODE"):
			type = line_parts[1]
			body = line_parts[3].rstrip()
			
			mode_list = body.split(" ", 1)
			if (mode_list[0] == "+o"):
				self.addOp(mode_list[1])
			elif (mode_list[0] == "-o"):
				self.removeOp(mode_list[1])
			else:
				self.log.writeToSystemLog(self.log.SystemMessage(self.log, "WARNING", "Invalid MODE operation: \"" + mode_list[0] + ".\""))
			
			self.log.writeToIRCLog(self.log.IRCMessage(self.log, type, body))
		
		elif (line_parts[0] == "PING"):
			print "PONG " + line_parts[1]
			self.twitch.send("PONG " + line_parts[1] + "\r\n")
			
			type = line_parts[1]
			body = "N/A"
			self.log.writeToIRCLog(self.log.IRCMessage(self.log, type, body))	
	
		elif (line_parts[1] == "PRIVMSG"):
			user = line_parts[0]
			body = line_parts[3][1:].rstrip()
			self.log.writeToChatLog(self.log.ChatMessage(self.log, user, body))
			
			## Check if the user is tracked. If not, add the user to the list.
			if (self.getIfKnownUser(user) == 0):
				self.addUser(self.User(self, user))
			
			## Parse the chat message from the user to determine if a command was issued.
			if (self.bool_basic_feature_set == 1):
				self.basic_feature_set.parseLineFromChat(user, body)
			
		else:
			self.log.writeToSystemLog(self.log.SystemMessage(self.log, "WARNING", "Unknown message type received from twitch.tv IRC Server."))
	
	## printAdmins - Prints out list of admins.
	def printAdmins(self):
		print "    Bot.printAdmins()"
		for admin in self.list_of_admins:
			print "        " + admin
	
	## printFeatureSets - Prints out the list of feature sets.
	def printFeatureSets(self):
		print "    Bot.printFeatureSets()"
		for fs in self.list_of_feature_sets:
			print "        " + fs
	
	## printOps - Prints out the list of ops.
	def printOps(self):
		print "    Bot.printOps()"
		for op in self.list_of_ops:
			print "        " + op
	
	## printUsers - Calls the Bot.User.printUser method of each User object.
	def printUsers(self):
		for user in self.list_of_users:
			user.printUser()
		
	## removeAdmin - Removes the username specified from the list of administrators (broadcaster + others)
	## n           - The username to remove.
	def removeAdmin(self, n):
		## Format the name in the long-version used by twitch.
		n = ":" + n + "!" + n + "@" + n + ".tmi.twitch.tv"
		
		## Only remove a username which is in the list.
		for admin in self.list_of_admins:
			if (admin == n):
				self.list_of_admins.remove(n)
				self.log.writeToAdminLog(self.log.AdminMessage(self.log, "REMOVED ADMIN", n))
				
				## Update the user object's isadmin boolean.
				for user in self.list_of_users:
					if (user.name == n):
						user.setIsAdmin(0)
						
		#self.printAdmins()
		
	## removeOp - Removes the username specified from the list of operators (mods).
	## n        - The username to remove.
	def removeOp(self, n):
		## Format the name in the long-version used by twitch.
		n = ":" + n + "!" + n + "@" + n + ".tmi.twitch.tv"
		
		## Only remove a username which is in the list.
		for op in self.list_of_ops:
			if (op == n):
				self.list_of_ops.remove(n)
				self.log.writeToAdminLog(self.log.AdminMessage(self.log, "REMOVED OP", n))

				## Update the user object's isop boolean.
				for user in self.list_of_users:
					if (user.name == n):
						user.setIsOp(0)

		#self.printOps()
		
	## removeUser - Removes the user with the username specified from the list of users.
	## n          - The username of the user to remove.	
	def removeUser(self, n):
		for user in self.list_of_users:
			if (user.name == n):
				self.list_of_users.remove(user.n)
				break				
				
	## sendChatMessage - Sends a message to the twitch server as well as STDOUT.
	## t               - The text to be sent as a string.
	def sendChatMessage(self, t):
		print ":pyayabot!pyayabot@pyayabot.tmi.twitch.tv PRIVMSG #" + self.channel + " :" + t
		self.twitch.send("PRIVMSG #" + self.channel + " :" + t + "\r\n")
		self.log.writeToChatLog(self.log.ChatMessage(self.log, ":pyayabot!pyayabot@pyayabot.tmi.twitch.tv", t))
		
	## This method gracefully disconnects the bot from the channel and exits.
	def shutdownBot(self):
		self.sendChatMessage("Shutting down...")
		self.twitch.close()
		self.log.writeToSystemLog(self.log.SystemMessage(self.log, "INFO", "Bot shutdown via chat."))
		sys.exit()
		
	## Bot.User - Contains information and methods for users in chat.
	class User():
		## __init__               - Initialize the attributes of a User object.
		## self.parent            - A handle to the parent Bot object.
		## self.name              - The username of the user.
		## self.bool_isop         - A boolean tracking whether the user is a channel operator.
		## self.bool_isadmin      - A boolean tracking whether the user is the broadcaster. (stream owner)
		## self.last_command_time - The number of seconds since the last bot command was issued.
		## self.spam_count        - A counter which keeps track of the number of times a user has spammed. (Sent bot commands too quickly)
		## self.timeout_count     - A counter which keeps track of how many times the user has been timed out in chat.		
		def __init__(self, parent, name):
			self.parent             = parent
			self.name               = name
			self.bool_isadmin       = 0
			self.bool_isop          = 0
			self.bool_isbroadbaster = 0		
			self.last_command_time  = 0
			self.spam_count         = 1
			self.timeout_count      = 0
			
			## Check the broadcaster, admin and op statuses of the user.
			## Initialize the booleans.
			self.setIsBroadcaster(self.checkIsBroadcaster())
			self.setIsAdmin(self.checkIsAdmin())
			self.setIsOp(self.checkIsOp())

			self.printUser()
			
		## checkIsAdmin - Checks and returns whether or not this user is in the list of administrators.
		def checkIsAdmin(self):
			for admin in self.parent.list_of_admins:
				if (admin == self.name):
					#print "    " + self.name + " is an admin!"  
					return 1
			
			#print "    " + self.name + " is not an admin!" 
			return 0
		
		## checkIsBroadcaster - Checks and returns whether or not this user is the broadcaster.
		def checkIsBroadcaster(self):
			if ((":" + self.parent.channel + "!" + self.parent.channel + "@" + self.parent.channel + ".tmi.twitch.tv" == self.name)):
				#print "    " + self.name + " is the broadcaster!" 
				return 1
			else:
				#print "    " + self.name + " is not the broadcaster!" 
				return 0

		## checkIsOp - Checks and returns whether or not this user is in the list of operators.
		def checkIsOp(self):
			for op in self.parent.list_of_ops:
				if (op == self.name):
					#print "    " + self.name + " is an op!" 
					return 1
			
			#print "    " + self.name + " is not an op!" 
			return 0	
			
		## getIsAdmin - Returns whether or not this user is an administrator.
		def getIsAdmin(self):
			return self.bool_isadmin
		
		## getIsBroadcaster - Returns whether or not this user is the broadcaster.
		def getIsBroadcaster(self):
			return self.bool_isbroadbaster

		## getIsOp - Returns whether or not this user is an operator.
		def getIsOp(self):
			return self.bool_isop
	
		## updateCommandTime - Updates the last time a user successfully issued a bot command.
		## Also resets spam counter. This is used for flood protection.
		def updateCommandTime(self):
			self.last_command_time = time.time()
			self.spam_count        = 0

		## printUser - Prints the attributes of the Bot.User instance.
		def printUser(self):
			print "    Bot.User.printUser()"
			print "        self.name: " + self.name
			print "        self.bool_isadmin: " + str(self.bool_isadmin)
			print "        self.bool_isop: " + str(self.bool_isop)
			print "        self.bool_isbroadbaster: " + str(self.bool_isbroadbaster)		
			print "        self.last_command_time: " + str(self.last_command_time)
			print "        self.spam_count: " + str(self.spam_count)
			print "        self.timeout_count: " + str(self.timeout_count) + "\n"
	
		## setIsAdmin - Updates the value of the isadmin boolean.
		## b          - A boolean
		def setIsAdmin(self, b):
			self.bool_isadmin = b

		## setIsBroadcaster - Updates the value of the isbroadcaster boolean.
		## b                - A boolean		
		def setIsBroadcaster(self, b):
			self.bool_isbroadbaster = b

		## setIsOp - Updates the value of the isop boolean.
		## b       - A boolean
		def setIsOp(self, b):
			self.bool_isop = b

	## End of Bot.User class
		
## End of Bot class.

## LogFairy - This class contains code for writing chat and bot activities to a log.
class LogFairy():
	## __init__        - This method initialized the LogFairy instance.
	## self.date       - The current date.
	## self.time       - The current time.
	## self.irc_log    - A handle to a file located at the absolute or relative path to the IRC log file. (IRC Bodys excluding chat)
	## self.chat_log   - A handle to a file located at the absolute or relative path to the chat log file. (IRC chat Bodys)
	## self.system_log - A handle to a file located at the absolute or relative path to the system log file.
	## self.admin_log  - A handle to a file located at the absolute or relative path to the admin log file.
	## log_dir         - The directory in which to save the three log files.
	## syslog_bitlist  - The list of binary values controlling which system logging types are enabled passed in from Bot.__init__().
	def __init__(self, channel, log_dir, syslog_bitlist):
		self.date, self.time = self.getCurrentDateAndTime()
		self.syslog_bitlist  = syslog_bitlist
		
		## Verify the log directory specified in the config file exists. If it doesn't try to create it.
		try:
			if (os.path.isdir(log_dir) == 0):
				try:
					os.mkdir(log_dir)
				except WindowsError:
					print "    pyayaBot.LogFairy.__init__(): Unable to create log directory: \"" + log_dir + ".\""
					sys.exit()
					
		except WindowsError:
			print "    pyayaBot.LogFairy.__init__(): Unable to check existence of log directory: \"" + log_dir + ".\""
			sys.exit()
			
		## Open the handle to the system log file, write the header row and log the action to the system log.
		try:
			self.system_log = open(log_dir + "/pyayaBot_" + channel + "_systemlog_" + self.date + "_" + self.time + ".csv", "w+")
		except IOError:
			print "    pyayaBot.LogFairy.__init__(): Unable to open file: \"" + log_dir + "/pyayaBot_systemlog_" + self.date + "_" + self.time + ".csv.\""
			sys.exit()

		self.system_log.write("Date,Time,Level,Body\n")
		self.writeToSystemLog(self.SystemMessage(self, "INFO", "SYSTEM LOG CREATED"))

		## Open the handle to the chat log file, write the header row and log the action to the system log.		
		try:
			self.chat_log = open(log_dir + "/pyayaBot_" + channel + "_chatlog_" + self.date + "_" + self.time + ".csv", "w+")
		except IOError:
			print "    pyayaBot.LogFairy.__init__(): Unable to open file: \"" + log_dir + "/pyayaBot_chatlog_" + self.date + "_" + self.time + ".csv.\""
			sys.exit()
			
		self.chat_log.write("Date,Time,User,Body\n")
		self.writeToSystemLog(self.SystemMessage(self, "INFO", "CHAT LOG CREATED"))
		
		## Open the handle to the IRC log file, write the header row and log the action to the system log.		
		try:
			self.irc_log = open(log_dir + "/pyayaBot_" + channel + "_irclog_" + self.date + "_" + self.time + ".csv", "w+")
		except IOError:
			print "    pyayaBot.LogFairy.__init__(): Unable to open file: \"" + log_dir + "/pyayaBot_irclog_" + self.date + "_" + self.time + ".csv.\""		
			sys.exit()

		self.irc_log.write("Date,Time,Type,Body\n")
		self.writeToSystemLog(self.SystemMessage(self, "INFO", "IRC LOG CREATED"))

		## Open the handle to the admin log file, write the header row and log the action to the system log.		
		try:
			self.admin_log = open(log_dir + "/pyayaBot_" + channel + "_adminlog_" + self.date + "_" + self.time + ".csv", "w+")
		except IOError:
			print "    pyayaBot.LogFairy.__init__(): Unable to open file: \"" + log_dir + "/pyayaBot_adminlog_" + self.date + "_" + self.time + ".csv.\""		
			sys.exit()

		self.admin_log.write("Date,Time,Action,Body\n")
		self.writeToSystemLog(self.SystemMessage(self, "INFO", "IRC LOG CREATED"))
	
	## getCurrentTimeAndTime - This method returns the current date and time as a couple of strings..
	## 0 - The current date.
	## 1 - The current time to the second.
	def getCurrentDateAndTime(self):
		return time.strftime("%Y-%m-%d", time.localtime()), time.strftime("%H-%M-%S", time.localtime())
	
	## writeToAdminLog - Writes an entry to the chat log file.
	## m              - A ChatMessage object containing the values to write into the chat log.
	def writeToAdminLog(self, m):
		self.admin_log.write(m.date + "," + m.time + "," + m.action + "," + m.body + "\n")

	## writeToChatLog - Writes an entry to the chat log file.
	## m              - A ChatMessage object containing the values to write into the chat log.
	def writeToChatLog(self, m):
		self.chat_log.write(m.date + "," + m.time + "," + m.user + "," + m.body + "\n")

	## writeToIRCLog - Writes an entry to the IRC log file.
	## m             - An IRCMessage object containing the values to write into the IRC log.
	def writeToIRCLog(self, m):
		self.irc_log.write(m.date + "," + m.time + "," + m.type + "," + m.body + "\n")

	## writeToSystemLog - Writes an entry to the IRC log file.
	## m                - A SystemMessage object containing the values to write into the system log.
	def writeToSystemLog(self, m):
		## Only write the log entry if it is not block by the bitlist.
		if ((self.syslog_bitlist[0] == "1" and m.level == "INFO") or (self.syslog_bitlist[1] == "1" and m.level == "WARNING") or (self.syslog_bitlist[2] == "1" and m.level == "ERROR") or (self.syslog_bitlist[3] == "1" and m.level == "DEBUG")):
			self.system_log.write(m.date + "," + m.time + "," + m.level + "," + m.body + "\n")
	
	## LogFairy.AdminMessage - Describes an objection which contains information about 
	class AdminMessage():
		## __init__ - This method initializes the AdminMessage object.
		## self.date - The current date.
		## self.time - The current time.
		## self.user - The user who sent the message.
		## self.body - The body of the message.
		## parent    - A handle to the parent LogFairy instance calling method.	
		def __init__(self, parent, action, Body):
			## Initialize and set the time & date for this AdminMessage object.
			self.date, self.time = LogFairy.getCurrentDateAndTime(parent)
			
			## Initialize the user and body of the AdminMessage object.
			self.action = action
			self.body   = Body

	## LogFairy.ChatMessage - Describes an object which contains information about chat messages.
	class ChatMessage():
		## __init__ - This method initializes the ChatMessage object.
		## self.date - The current date.
		## self.time - The current time.
		## self.user - The user who sent the message.
		## self.body - The body of the message.
		## parent    - A handle to the parent LogFairy instance calling method.	
		def __init__(self, parent, user, Body):
			## Initialize and set the time & date for this ChatMessage object.
			self.date, self.time = LogFairy.getCurrentDateAndTime(parent)
			
			## Initialize the user and body of the ChatMessage object.
			self.user = user
			self.body = Body
	
	## End of LogFairy.ChatMessage class		
		
	## LogFairy.IRCMessage - Describes an object which contains information IRC messages from the twitch.tv IRC.
	class IRCMessage():
		## __init__ - This method initializes the IRCMessage object.
		## self.date - The current date.
		## self.time - The current time.
		## self.type - The type of message. (###, JOIN, PART, MODE, PRIVMSG)
		## self.body - The body of the message.
		## parent    - A handle to the parent LogFairy instance calling method.
		def __init__(self, parent, type, Body):
			## Initialize and set the time & date for this IRCMessage object.
			self.date, self.time = LogFairy.getCurrentDateAndTime(parent)
			
			## Initialize the type and body of the IRCMessage object.
			self.type = type
			self.body = Body
	
	## End of LogFairy.IRCMessage class
	
	## LogFairy.SystemMessage - Describes an object which contains information about system messages.
	class SystemMessage():
		## __init__   - This method initializes the SystemMessage object.
		## self.date  - The current date.
		## self.time  - The current time.
		## self.level - The level (Severity) of the message. (INFO, WARNING, DEBUG, ERROR)
		## self.body  - The body of the message.
		## parent     - A handle to the parent LogFairy instance calling method.	
		def __init__(self, parent, level, Body):
			## Initialize and set the time & date for this SystemMessage object.
			self.date, self.time = LogFairy.getCurrentDateAndTime(parent)
			
			## Initialize the level and body of the SystemMessage object.
			self.level = level
			self.body  = Body

	## End of LogFairy.SystemMessage class
		
## End of LogFairy class
