## pyayaBot_main.py
## Author(s): Daniel "Albinohat" Mercado
## The main body of a twitch bot which listens for IRC Messages and offers features from the pyayaBot_features module.

## TODO [ NOT STARTED ], [ IN-PROGRESS ], [ TESTING ] or [ DONE ]
##
## This is a list of things which need to be written or committed. ([ DONE ])
## Implement multi-threading [ DONE ]
#### Logging [ DONE ]
#### Message Parsing [ DONE ]
#### Line Parsing [ DONE ]
## Change configuration file format from INI to JSON. [ NOT STARTED ]
## Implement a timer to trigger the bot to send the MOTD. [ NOT STARTED ]
## Insert DEBUG-level system logging into existing methods. (Replace  '#' commented out print lines with writeToSystemLog calls) [ NOT STARTED ]



## BUG FIXES
##
## Fixed the removeUser method to use user.name rather than user.n
## Added a check that a message received from the twitch.tv IRC server is complete.
## Right-stripping all lines parsed from the twitch.tv IRC server and ignoring null lines.

## Standard Imports
import os, re, socket, sys, time

## Third-party Imports
import pyayaBot_featureSets, pyayaBot_threading

## Bot - This class contains the most basic operations of pyayaBot.
class Bot():
	## __init__ - This method sets up the bot using a configuration file, connects to the twitch IRC server and starts the main listening loop.
	## self.host                    - The IP of the twitch.tv IRC server.
	## self.port                    - The port of the twitch.tv IRC server.
	## self.nick                    - The nickname (username) of the Bot instance.
	## self.oauth                   - The password (OAuth token) of the Bot instance.
	## self.ident                   - The identity of the Bot instance. (Must be the same as nickname)
	## self.realname                - Used as a credits field. Please always initialize to give credits to Albinohat.
	## self.channel                 - The channel the bot will join. A single bot instance must join only one channel at a time. (For now)
	## self.log_dir                 - The absolute or relative paths to the directory in which log files will be stored.				
	## self.syslog_bitlist          - A bit mask supplied as a list of bools which determines what types of log entries to write.
	##                        Index - Value
	##					          0 - System > INFO
	##					          1 - System > WARNING
	##					          2 - System > ERROR
	##					          3 - System > DEBUG
	## self.log                     - A LogFairy object which will handle writing out log entries.
	## self.twitch                  - A socket object which will contain the IP/port pairs between the local machine and the twitch.tv IRC server.
	## self.list_of_feature_sets    - A list of strings denoting which feature	sets the bot will use.
	## self.list_of_users           - A list of User objects to track users in a channel.
	## self.list_of_admins          - A list of strings containing the usernames of admins. (Broadcast + albinohat)
	## self.list_of_ops             - A list of strings containing the usernames of channel operators.
	## self.bool_[name]_feature_set - A boolean tracking whether or not this bot instance will have access to the [name] feature set.
	##
	## connection_config_path       - The absolute or relative path to the connection configuration file to initialize the Bot instance.
	## channel_config_path          - The absolute or relative path to the channel configuration file to initialize the Bot instance.
	## syslog_bitlist               - The list of binary values controlling which system logging types are enabled.
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
		
		## Avoid re-adding a username to the list.
		for admin in self.list_of_admins:
			if (admin == n):
				return
	
		self.list_of_admins.append(n)
		pyayaBot_threading.writeToAdminLogThread(self, self.log.AdminMessage(self.log, "ADDED ADMIN", n))
		
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
		pyayaBot_threading.writeToAdminLogThread(self, self.log.AdminMessage(self.log, "ADDED OP", n))

		## Update the user object's isop boolean.
		for user in self.list_of_users:
			if (user.name == n):
				user.setIsOp(1)
				
		#self.printOps()
		
	## addUser - Adds the specified User object to the user list.
	## u       - A User object.
	def addUser(self, u):
		self.list_of_users.append(u)
		# Insert debug logging.
	
	## addUserFromJoinMessage - Creates and adds the specified user object to the list of users.
	## name - A username sent by the twitch.tv IRC server in a JOIN message.
	def addUserFromJoinMessage(self, name):
		## Check if the user is tracked. If not, add the user to the list.
		if (self.getIfKnownUser(name) == 0):
			self.addUser(self.User(self, name))	
			
	## addUsersFromNamesList - Creates and adds the specified User objects to the user list.
	## names_list            - A list of usernames sent by the twitch.tv IRC server in a NAMES list. (Message type 366)
	def addUsersFromNamesList(self, names_list):
		for name in names_list:
			## Format the name in the long-version used by twitch.
			name = name = ":" + name + "!" + name + "@" + name + ".tmi.twitch.tv"
			
			## Check if the user is tracked. If not, add the user to the list.
			if (self.getIfKnownUser(name) == 0):
				self.addUser(self.User(self, name))	
		
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
		
		pyayaBot_threading.writeToSystemLogThread(self, self.log.SystemMessage(self.log, "INFO", "Successfully connected to twitch.tv IRC server. (" + self.host + " Port " + str(self.port) + ")"))
		
	## initializeFeatureSets - This method initializes feature set objects.
	def initializeFeatureSets(self):
		## Initialize booleans to enable or disable feature sets.
		self.bool_basic_feature_set     = 0
		self.bool_osu_feature_set       = 0
		self.bool_quakelive_feature_set = 0
		self.bool_youtube_featre_set    = 0
		
		## Call the methods to initialize the specified feature sets in the list.
		for fs in self.list_of_feature_sets:
			## Initialize a BasicFeatureSet instance.
			if (fs == "BasicFeatureSet"):
				self.basic_feature_set = pyayaBot_featureSets.BasicFeatureSet(self)
				self.bool_basic_feature_set = 1
			elif (fs == "OsuFeatureSet"):
				## Instantiate OsuFeatureSet object here.
				self.bool_osu_feature_set = 1
			elif (fs == "QuakeLiveFeatureSet"):
				## Instantiate QuakeLiveFeatureSet object here.
				self.bool_quakelive_feature_set = 1			
			elif (fs == "YouTubeFeatureSet"):
				## Instantiate YouTubeFeatureSet object here.
				self.bool_youtube_feature_set = 1

		
	## listenLoop - This method enters an infinite loop and listens for text from the twitch.tv IRC Server.
	def listenLoop(self):
		while (1):
			## Split data received from the twitch.tv IRC server into lines.
			read_buffer = self.twitch.recv(9182)
			temp = read_buffer.split("\n", 1000)
			for line in temp:
				if (line != "" and line != "\n" and line != "\r\n"):
					print line
					pyayaBot_threading.parseLineFromTwitchThread(self, line.rstrip())
		
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
			
	## parseLineFromTwitch - This method will strip the ending white space from and parse a line of text form the twitch.tv IRC server, splitting it up and determining its log type and corresponding values.
	## line                - The message sent from listenLoop().
	def parseLineFromTwitch(self, line):		
		if (line == ""):
			pyayaBot_threading.writeToSystemLogThread(self, self.log.SystemMessage(self.log, "WARNING", "NULL message from twitch.tv IRC server."))
			return
	
		line_parts = line.split(" ", 3)
		
		if (re.match("[0-9]{3}", line_parts[1]) and line_parts[2] == "pyayabot"):
			type = line_parts[1]
			body = line_parts[3]
			pyayaBot_threading.writeToIRCLogThread(self, self.log.IRCMessage(self.log, type, body))
		
			## Create and add users from the NAMES list.
			if (line_parts[1] == "353"):
				names_list = line_parts[3][len(self.channel) + 5:]			
				self.addUsersFromNamesList(names_list)
				
		elif (line_parts[1] == "JOIN" and line_parts[2] == "#" + self.channel):
			type = line_parts[1]
			body = line_parts[0]
			pyayaBot_threading.writeToIRCLogThread(self, self.log.IRCMessage(self.log, type, body))
			
			self.addUserFromJoinMessage(body)
				
		elif (line_parts[1] == "PART" and line_parts[2] == "#" + self.channel):
			type = line_parts[1]
			body = line_parts[0]
			pyayaBot_threading.writeToIRCLogThread(self, self.log.IRCMessage(self.log, type, body))
			
			## Remove the user from the list of tracked users.
			self.removeUser(body)
		
		elif (line_parts[1] == "MODE"):
			type = line_parts[1]
			body = line_parts[3]
			
			mode_list = body.split(" ", 1)
			if (mode_list[0] == "+o"):
				self.addOp(mode_list[1])
			elif (mode_list[0] == "-o"):
				self.removeOp(mode_list[1])
			else:
				pyayaBot_threading.writeToSystemLogThread(self, self.log.SystemMessage(self.log, "WARNING", "Invalid MODE operation: \"" + mode_list[0] + "\"."))
				return
				
			pyayaBot_threading.writeToIRCLogThread(self, self.log.IRCMessage(self.log, type, body))
		
		elif (line_parts[0] == "PING"):
			print "PONG " + line_parts[1]
			self.twitch.send("PONG " + line_parts[1] + "\r\n")
			
			type = line_parts[1]
			body = "N/A"
			pyayaBot_threading.writeToIRCLogThread(self, self.log.IRCMessage(self.log, type, body))	
	
		elif (line_parts[1] == "PRIVMSG"):
			user = line_parts[0]
			body = line_parts[3][1:].rstrip()
			pyayaBot_threading.writeToChatLogThread(self, self.log.ChatMessage(self.log, user, body))
			
			## Check if the user is tracked. If not, add the user to the list.
			if (self.getIfKnownUser(user) == 0):
				self.addUser(self.User(self, user))
			
			## Parse the chat message from the user to determine if a command was issued.
			if (self.bool_basic_feature_set == 1):
				if (self.basic_feature_set.checkIfCommand(body)):
					pyayaBot_threading.executeCommandThread(self, self.basic_feature_set.Command(user, body))
			
		else:
			pyayaBot_threading.writeToSystemLogThread(self, self.log.SystemMessage(self.log, "WARNING", "Unknown message type received from twitch.tv IRC server: \"" + line_parts[1] + "\"."))	

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
				
				## Update the user object's isadmin boolean.
				for user in self.list_of_users:
					if (user.name == n):
						user.setIsAdmin(0)
				
				pyayaBot_threading.writeToAdminLogThread(self, self.log.AdminMessage(self.log, "REMOVED ADMIN", n))
						
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

				## Update the user object's isop boolean.
				for user in self.list_of_users:
					if (user.name == n):
						user.setIsOp(0)
				
				pyayaBot_threading.writeToAdminLogThread(self, self.log.AdminMessage(self.log, "REMOVED OP", n))

		#self.printOps()
		
	## removeUser - Removes the user with the username specified from the list of users.
	## n          - The username of the user to remove.	
	def removeUser(self, n):
		for user in self.list_of_users:
			if (user.name == n):
				self.list_of_users.remove(user.name)
				break				
				
	## sendChatMessage - Sends a message to the twitch server as well as STDOUT.
	## t               - The text to be sent as a string.
	def sendChatMessage(self, t):
		print ":pyayabot!pyayabot@pyayabot.tmi.twitch.tv PRIVMSG #" + self.channel + " :" + t
		self.twitch.send("PRIVMSG #" + self.channel + " :" + t + "\r\n")
		pyayaBot_threading.writeToChatLogThread(self, self.log.ChatMessage(self.log, ":pyayabot!pyayabot@pyayabot.tmi.twitch.tv", t))
		
	## This method gracefully disconnects the bot from the channel and exits.
	def shutdownBot(self):
		self.sendChatMessage("Shutting down...")
		self.twitch.close()
		pyayaBot_threading.writeToSystemLogThread(self, self.log.SystemMessage(self.log, "INFO", "Bot shutdown via chat."))
		
		## Write the closing HTML tags to the log files.
		self.log.writeLogFooters(self.log.system_log_path)
		self.log.writeLogFooters(self.log.chat_log_path)
		self.log.writeLogFooters(self.log.irc_log_path)
		self.log.writeLogFooters(self.log.admin_log_path)
		
		## Shut the bot down. (Kills the last 2 threads (parseLineFromTwitchThread and mainThread)
		sys.exit()
		sys.exit()
	
	## Bot.User - Contains information and methods for users in chat.
	class User():
		## __init__ - Initialize the attributes of a User object.
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
			## Initialize the isadmin, isbroadcaster and isop booleans.
			self.setIsBroadcaster(self.checkIsBroadcaster())
			self.setIsAdmin(self.checkIsAdmin())
			self.setIsOp(self.checkIsOp())

			#self.printUser()
			
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
	## __init__ - This method initialized the LogFairy instance.
	## self.date            - The current date.
	## self.time            - The current time.
	## self.system_log_path - The absolute or relative path to the system log file.
	## self.chat_log_path   - The absolute or relative path to the chat log file.
	## self.irc_log_path    - The absolute or relative path to the IRC log file.
	## self.admin_log_path  - The absolute or relative path to the admin log file.
	##
	## channel              - The channel the Bot has joined. Passed in from Bot.__init__().
	## log_dir              - The directory in which to save the three log files.
	## syslog_bitlist       - The list of binary values controlling which system logging types are enabled passed in from Bot.__init__().
	def __init__(self, channel, log_dir, syslog_bitlist):
		self.date, self.time = self.getCurrentDateAndTime()
		self.syslog_bitlist  = syslog_bitlist
		
		## Append the current date to the log dir to separate logs by day.
		log_dir = log_dir + "/" + self.date + "/" + channel

		## Call the method to initialize (create) log files.
		self.initializeLogs(channel, log_dir)
		
		#self.printLogFairy()

	## getCurrentTimeAndTime - This method returns the current date and time as a couple of strings..
	## 0 - The current date.
	## 1 - The current time to the second.
	def getCurrentDateAndTime(self):
		return time.strftime("%Y-%m-%d", time.localtime()), time.strftime("%H-%M-%S", time.localtime())
		
	## This method initializes the chat log files.
	## log_dir - The directory passed-in form __init__ in which to create the log files.
	## channel - The channel passed-in from __init__ which the Bot has joined.
	def initializeLogs(self, channel, log_dir):
		## Verify the log directory specified in the config file exists. If it doesn't try to create it.
		try:
			if (os.path.isdir(log_dir) == 0):
				try:
					os.makedirs(log_dir)
					
				except WindowsError:
					print "    pyayaBot.LogFairy.__init__(): Unable to create log directory: \"" + log_dir + "\""
					sys.exit()
					
		except WindowsError:
			print "    pyayaBot.LogFairy.__init__(): Unable to check existence of log directory: \"" + log_dir + "\""
			sys.exit()

		## log_count value is tracked separately for each log type to ensure the most accurate recreation of events possible.		
			
		## Open the handle to the system log file, write the headers, top row and log the action to the system log.
		for log_count in range(100):
			try:
				self.system_log_path = log_dir + "/pyayaBot_" + channel + "_systemlog_" + str(log_count + 1) + ".html"
				
				if (os.path.isfile(self.system_log_path) == 0):
					system_log_handle = open(self.system_log_path, "w+")
					break
				
			except IOError:
				print "    pyayaBot.LogFairy.__init__(): Unable to open file: \"" + self.system_log_path + ".\""
				sys.exit()
		
		self.writeLogHeaders(self.system_log_path)
		self.writeLogColumnNames(self.system_log_path)
		
		self.writeToSystemLog(self.SystemMessage(self, "INFO", "SYSTEM LOG CREATED"))

		## Open the handle to the chat log file, write the headers, top row and log the action to the system log.		
		for log_count in range(100):
			try:
				self.chat_log_path = log_dir + "/pyayaBot_" + channel + "_chatlog_" + str(log_count + 1) + ".html"
				
				if (os.path.isfile(self.chat_log_path) == 0):
					chat_log_handle = open(self.chat_log_path, "w+")
					break
				
			except IOError:
				print "    pyayaBot.LogFairy.__init__(): Unable to open file: \"" + self.chat_log_path + ".\""
				sys.exit()
		
		self.writeLogHeaders(self.chat_log_path)
		self.writeLogColumnNames(self.chat_log_path)
		
		self.writeToSystemLog(self.SystemMessage(self, "INFO", "CHAT LOG CREATED"))
		
		## Open the handle to the IRC log file, write the headers, top row and log the action to the system log.		
		for log_count in range(100):		
			try:
				self.irc_log_path = log_dir + "/pyayaBot_" + channel + "_irclog_" + str(log_count + 1) + ".html"
				if (os.path.isfile(self.irc_log_path) == 0):
					irc_log_handle = open(self.irc_log_path, "w+")
					break
					
			except IOError:
				print "    pyayaBot.LogFairy.__init__(): Unable to open file: \"" + self.irc_log_path + ".\""		
				sys.exit()
				
		self.writeLogHeaders(self.irc_log_path)
		self.writeLogColumnNames(self.irc_log_path)
		
		self.writeToSystemLog(self.SystemMessage(self, "INFO", "IRC LOG CREATED"))

		## Open the handle to the admin log file, write the headers, top row and log the action to the system log.		
		for log_count in range(100):		
			try:
				self.admin_log_path = log_dir + "/pyayaBot_" + channel + "_adminlog_" + str(log_count + 1) + ".html"
				
				if (os.path.isfile(self.admin_log_path) == 0):
					admin_log_handle = open(self.admin_log_path, "w+")
					break
					
			except IOError:
				print "    pyayaBot.LogFairy.__init__(): Unable to open file: \"" + self.admin_log_path + ".\""		
				sys.exit()

		self.writeLogHeaders(self.admin_log_path)
		self.writeLogColumnNames(self.admin_log_path)
		
		self.writeToSystemLog(self.SystemMessage(self, "INFO", "ADMIN LOG CREATED"))
		
	## Prints out the attributes of a LogFairy instance.
	def printLogFairy(self):
		print "    LogFairy.printLogFairy()"
		print "        self.date: " + self.date
		print "        self.time: " + self.time
		print "        self.system_log_path: " + self.system_log_path
		print "        self.chat_log_path: " + self.chat_log_path
		print "        self.irc_log_path: " + self.irc_log_path
		print "        self.admin_log_path: " + self.admin_log_path
		
	## writeLogColumnNames - Writes the top row of the log file with the column names.
	## log_path - The path to the log file to be created and add headers.
	def writeLogColumnNames(self, log_path):
		write_handle = open(log_path, "a")
		
		write_handle.write("	<tr>\n")
		write_handle.write("		<td height=\"17\" align=\"left\">Date</td>\n")
		write_handle.write("		<td align=\"left\">Time</td>\n")
		
		## Label the third column according to the type of log.
		if ("systemlog" in log_path):
			write_handle.write("		<td align=\"left\">Level</td>\n")
		elif ("chatlog" in log_path):
			write_handle.write("		<td align=\"left\">User</td>\n")
		elif ("irclog" in log_path):
			write_handle.write("		<td align=\"left\">Type</td>\n")
		elif ("adminlog" in log_path):
			write_handle.write("		<td align=\"left\">Action</td>\n")
		else:
			write_handle.write("      <td align=\"left\">ERROR</td>\n")
			self.writeToSystemLog(self.SystemMessage(self, "ERROR", "Invalid log found type while writing top row."))
			sys.exit()

		write_handle.write("		<td align=\"left\">Body</td>\n")
		write_handle.write("	</tr>\n"	)
		
		write_handle.close()
	
	## writeLogFooters - Writes the HTML tags to the end of the log files.
	def writeLogFooters(self, log_path):
		write_handle = open(log_path, "a")
		
		write_handle.write("</table>\n")
		write_handle.write("<!-- ************************************************************************** -->\n")
		write_handle.write("</body>\n\n")
		write_handle.write("</html>\n")
	
	## writeLogHeaders - Writes the HTML & CSS tags to the top of the log files.
	## log_path - The path to the log file to be created and add headers.
	def writeLogHeaders(self, log_path):
		write_handle = open(log_path, "w+")
		
		write_handle.write("<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0 Transitional//EN\">\n\n")
		write_handle.write("<html>\n")
		write_handle.write("<head>\n")
		write_handle.write("	<meta http-equiv=\"content-type\" content=\"text/html; charset=windows-1252\">\n")
		write_handle.write("<title></title>\n")
		write_handle.write("	<meta name=\"generator\" content=\"LibreOffice 4.2.5.2 (Windows)\">\n")
		write_handle.write("	<meta name=\"created\" content=\"0;0\">\n")
		write_handle.write("	<meta name=\"changed\" content=\"0;0\">\n\n")	
		write_handle.write("	<style type=\"text/css\"><!-- \n")
		write_handle.write("		body,div,table,thead,tbody,tfoot,tr,th,td,p { font-family:\"Liberation Sans\"; font-size:x-small }\n\n")
		write_handle.write("		-->\n")
		write_handle.write("	</style>\n\n")
		write_handle.write("</head>\n\n")
		write_handle.write("<body text=\"#000000\">\n")
		write_handle.write("<table cellspacing=\"0\" border=\"2\">\n")
		write_handle.write("<colgroup width=\"79\"></colgroup>\n")
		write_handle.write("<colgroup width=\"69\"></colgroup>\n")
		write_handle.write("<colgroup width=\"299\"></colgroup>\n")
		write_handle.write("<colgroup width=\"749\"></colgroup>\n")

		write_handle.close()

	## writeToAdminLog - Opens, writes an entry to and then closes the chat log file.
	## m              - A ChatMessage object containing the values to write into the chat log.
	def writeToAdminLog(self, m):
		write_handle = open(self.admin_log_path, "a")
		
		write_handle.write("	<tr>\n")
		write_handle.write("		<td height=\"17\" align=\"left\">" + m.date + "</td>\n")
		write_handle.write("		<td align=\"left\">" + m.time + "</td>\n")		
		write_handle.write("		<td align=\"left\">" + m.action + "</td>\n")
		write_handle.write("		<td align=\"left\">" + m.body + "</td>\n")
		write_handle.write("	</tr>\n")
		
		write_handle.close()

	## writeToChatLog - Opens, writes an entry to and then closes the chat log file.
	## m              - A ChatMessage object containing the values to write into the chat log.
	def writeToChatLog(self, m):
		write_handle = open(self.chat_log_path, "a")
		
		write_handle.write("	<tr>\n")
		write_handle.write("		<td height=\"17\" align=\"left\">" + m.date + "</td>\n")
		write_handle.write("		<td align=\"left\">" + m.time + "</td>\n")		
		write_handle.write("		<td align=\"left\">" + m.user + "</td>\n")
		write_handle.write("		<td align=\"left\">" + m.body + "</td>\n")
		write_handle.write("	</tr>\n")			
		
		write_handle.close()
		
	## writeToIRCLog - Opens, writes an entry to and then closes the IRC log file.
	## m             - An IRCMessage object containing the values to write into the IRC log.
	def writeToIRCLog(self, m):
		write_handle = open(self.irc_log_path, "a")
		
		write_handle.write("	<tr>\n")
		write_handle.write("		<td height=\"17\" align=\"left\">" + m.date + "</td>\n")
		write_handle.write("		<td align=\"left\">" + m.time + "</td>\n")		
		write_handle.write("		<td align=\"left\">" + m.type + "</td>\n")
		write_handle.write("		<td align=\"left\">" + m.body + "</td>\n")
		write_handle.write("	</tr>\n")			
		
		write_handle.close()

	## writeToSystemLog - Opens, writes an entry to and then closes the IRC log file.
	## m                - A SystemMessage object containing the values to write into the system log.
	def writeToSystemLog(self, m):
		## Only write the log entry if it is enabled by the bitlist.
		if ((self.syslog_bitlist[0] == "1" and m.level == "INFO") or (self.syslog_bitlist[1] == "1" and m.level == "WARNING") or (self.syslog_bitlist[2] == "1" and m.level == "ERROR") or (self.syslog_bitlist[3] == "1" and m.level == "DEBUG")):
			write_handle = open(self.system_log_path, "a")
		
		write_handle.write("	<tr>\n")
		write_handle.write("		<td height=\"17\" align=\"left\">" + m.date + "</td>\n")
		write_handle.write("		<td align=\"left\">" + m.time + "</td>\n")		
		write_handle.write("		<td align=\"left\">" + m.level + "</td>\n")
		write_handle.write("		<td align=\"left\">" + m.body + "</td>\n")
		write_handle.write("	</tr>\n")			
		
		write_handle.close()

	## LogFairy.AdminMessage - Describes an object which contains information about administrative changes. (Admin/Op adds/removes timeouts/bans)
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
			
			#self.printAdminMessage()
			
		## Print out the attributes of this LogFairy.AdminMessage instance.
		def printAdminMessage(self):
			print "    LogFairy.AdminMessage.printAdminMessage()"
			print "        self.date: " + self.date
			print "        self.time: " + self.time
			print "        self.action: " + self.action
			print "        self.body: " + self.body

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
			
			#self.printChatMessage()
			
		## Print out the attributes of this LogFairy.ChatMessage instance.
		def printChatMessage(self):
			print "    LogFairy.ChatMessage.printChatMessage()"
			print "        self.date: " + self.date
			print "        self.time: " + self.time
			print "        self.user: " + self.user
			print "        self.body: " + self.body
			
	## End of LogFairy.ChatMessage class		
		
	## LogFairy.IRCMessage - Describes an object which contains information IRC messages from the twitch.tv IRC server.
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
			
			#self.printIRCMessage()
			
		## Print out the attributes of this LogFairy.IRCMessage instance.
		def printIRCMessage(self):
			print "    LogFairy.IRCMessage.printIRCMessage()"
			print "        self.date: " + self.date
			print "        self.time: " + self.time
			print "        self.type: " + self.type
			print "        self.body: " + self.body
			
	## End of LogFairy.IRCMessage class
	
	## LogFairy.SystemMessage - Describes an object which contains information about system messages.
	class SystemMessage():
		## __init__ - This method initializes the SystemMessage object.
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
			
			#self.printSystemMessage()

		## Print out the attributes of this LogFairy.SystemMessage instance.
		def printSystemMessage(self):
			print "    LogFairy.SystemMessage.printSystemMessage()"
			print "        self.date: " + self.date
			print "        self.time: " + self.time
			print "        self.level: " + self.level
			print "        self.body: " + self.body			
			
	## End of LogFairy.SystemMessage class
		
## End of LogFairy class
