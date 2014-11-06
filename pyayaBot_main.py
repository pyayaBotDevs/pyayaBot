##pyayaBot_main.py
##The main body of a Twitch bot which listens for IRC Messages and offers features from the pyayaBot_features module.

## TODO
## Objectify Messages [ DONE ] 
## Write method to allow bot to send chat messages. [ DONE ]
## Reimplement user management. [ IN-PROGRESS ]
## Reimplement the admin list. [ DONE ]
## Implement system logging bitmask. [ DONE ]
## Implement feature sets into the __init__ of Bot class. [ DONE ]
## Update configuration file format to support feature sets and comments. [ DONE ]
## Insert system logging into existing methods. [ IN-PROGRESS ]
## Insert IRC logging into existing methods. [ DONE ]
## Insert chat logging into existing methods. [ DONE ]
## Insert debug logging into existing methods.
## Implement 4th log for bans/timeouts.

## Imports
import pyayaBot_featureSets, socket, re, sys, time, os, subprocess

## Bot - This class contains the most basic operations of pyayaBot.
class Bot():
	## __init__                  - This method sets up the bot using a configuration file, connects to the Twitch IRC server and starts the main listening loop.
	## self.host                 - The IP of the Twitch.TV IRC server.
	## self.port                 - The port of the Twitch.TV IRC server.
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
	## self.twitch               - A socket object which will contain the IP/port pairs between the local machine and the Twitch.TV IRC server.
	## self.list_of_feature_sets - A list of strings denoting which feature	sets the bot will use.
	## self.list_of_users        - A list of User objects to track users in a channel.
	## self.list_of_admins       - A list of strings containing the usernames of admins. (Broadcast + albinohat)
	## self.list_of_ops          - A list of strings containing the usernames of channel operators.
	## config_path               - The absolute or relative path to the configuration file to initialize the Bot instance.
	## syslog_bitlist            - The list of binary values controlling which system logging types are enabled.
	def __init__(self, config_path, syslog_bitlist):
		## Initialize the credits, logging bitmask and lists of users and ops.
		self.realname             = "pyayaBot by https://github.com/pyayaBotDevs"
		self.syslog_bitlist       = syslog_bitlist
		self.list_of_feature_sets = []
		self.list_of_users        = []
		self.list_of_admins       = []
		self.list_of_ops          = []

		## Call the method to parse the configuration file.
		self.parseConfigFile(config_path)
		
		## Initialize the LogFairy object using the log directory.
		self.log = LogFairy(self.channel, self.log_dir, self.syslog_bitlist)
		
		## Call the method to connect to the Twitch.TV IRC server.
		self.connectToTwitch()
		
		## Call the method to initialize the various feature set objects.
		self.initializeFeatureSets()
				
		## Call the method to listen for messages from the Twitch.TV IRC server.
		self.listenLoop()
	
	## addAdmin - Adds a username to the list of administrators (Broadcaster + others)
	## n        - The username of the user to add to the list.
	def addAdmin(self, n):
		self.list_of_admins.append(n)
		
	## addOp - Adds a username to the list of operators (mods).
	## n     - The username of the user to add to the list.
	def addOp(self, n):
		self.list_of_ops.append(n)
		
	## addUser - Adds the specified username to the list of operators (mods).
	## u       - A User object.
	def addUser(self, u):
		self.list_of_users.append(u)
	
	## checkIfKnownUser - This method will loop through the list of User objects.
	## It returns 0 if the user is not tracked in the list of users.
	## It returns 1 if the user is tracked in the list of users.
	## n                - The username of someone in the channel to check.
	def checkIfKnownUser(self, n):
		bool_known = 0
		for user in self.list_of_users:
			if (n == user.name):
				bool_known = 1
				break
		
		return bool_known
		
	## connectToTwitch - This method connects to the Twitch IRC server and joins the configured channel.
	def connectToTwitch(self):
		##Open the connection to Twitch IRC
		self.twitch = socket.socket()
		self.twitch.connect((self.host, self.port))
		self.twitch.send("PASS %s\r\n" % self.oauth) 
		self.twitch.send("NICK %s\r\n" % self.nick)
		self.twitch.send("USER %s %s bla :%s\r\n" % (self.ident, self.host, self.realname))
		self.twitch.send("JOIN #%s\r\n" % self.channel)
		
		self.log.writeToSystemLog(self.log.SystemMessage(self.log, "INFO", "Successfully connected to Twitch.TV IRC Server. (" + self.host + " Port " + str(self.port) + ")"))
		
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
		
	## listenLoop - This method enters an infinite loop and listens for text from the Twitch.TV IRC Server.
	def listenLoop(self):
		read_buffer = ""
		while (1):
			## Split data received from the Twitch.TV IRC server into lines.
			read_buffer = self.twitch.recv(4096)
			temp = read_buffer.split("\n", 10000)
			for line in temp:
				if (line != "" and line != "\n" and line != "\r\n"):
					print line
					self.parseLineFromTwitch(line.rstrip())
		
	## parseConfigFile - This method opens the configuration file and parses it to ensure the correct values are set to initialize the Bot instance.
	def parseConfigFile(self, config_path):
		try:
			config_file = open(config_path, "r")
		except IOError:
			print "    pyayaBot.Bot.parseConfigFile(): Unable to open file: \"" + config_path + ".\""
			sys.exit()
			
		for line in config_file:
			## Do not parse comment lines.
			if (line[0] == "#" or line == ""):
				continue
			self.line_list = line.split("=", 1)
			if (self.line_list[0] == "HOST"):
				self.host = self.line_list[1].rstrip()
			elif (self.line_list[0] == "PORT"):
				self.port = int(self.line_list[1].rstrip(), base=10)
			elif (self.line_list[0] == "NICK"):
				self.nick = self.line_list[1].rstrip()
				self.ident = self.nick
			elif (self.line_list[0] == "PASS"):
				self.oauth = self.line_list[1].rstrip()
			elif (self.line_list[0] == "CHANNEL"):
				self.channel = self.line_list[1].rstrip()
			elif (self.line_list[0] == "FEATURESET"):
				self.list_of_feature_sets.append(self.line_list[1].rstrip())
			elif (self.line_list[0] == "LOG_DIR"):
				self.log_dir = self.line_list[1].rstrip()
			else:
				print "    pyayaBot.Bot.parseConfigFile(): Invalid config entry: \"" + self.line_list[0] + ".\""
		
		if (self.host == "" or self.port == 0 or self.nick == "" or self.oauth == "" or self.channel == ""):
			print "    pyayaBot.Bot.parseConfigFile(): One or more configuration entries were not set."
			print "    Please verify the configuration file's contents and try again."
			sys.exit()
		
		config_file.close()
			
	## parseLineFromTwitch - This method will parse a line of text form the Twitch.TV IRC server, splitting it up and determining its log type and corresponding values.
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
			if (self.checkIfKnownUser(body) == 0):
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
			self.twitch.send("PONG + " + line + "\r\n")
			
			type = line_parts[1]
			body = "N/A"
			self.log.writeToIRCLog(self.log.IRCMessage(self.log, type, body))	
	
		elif (line_parts[1] == "PRIVMSG"):
			user = line_parts[0]
			body = line_parts[3][1:].rstrip()
			self.log.writeToChatLog(self.log.ChatMessage(self.log, user, body))
			
			## Check if the user is tracked. If not, add the user to the list.
			if (self.checkIfKnownUser(user) == 0):
				self.addUser(self.User(self, user))
			
			## Parse the chat message from the user to determine if a command was issued.
			if (self.bool_basic_feature_set == 1):
				self.basic_feature_set.parseLineFromChat(user, body)
			
		else:
			self.log.writeToSystemLog(self.log.SystemMessage(self.log, "WARNING", "Unknown message type received from Twitch.TV IRC Server."))
	
	## printUsers - Calls the Bot.User.printUser method of each User object.
	def printUsers(self):
		for user in self.list_of_users:
			user.printUser()
		
	## removeAdmin - Removes the username specified from the list of administrators (broadcaster + others)
	## n           - The username to remove.
	def removeAdmin(self):
		self.list_of_admins.remove(n)
		
	## removeOp - Removes the username specified from the list of operators (mods).
	## n        - The username to remove.
	def removeOp(self, n):
		self.list_of_ops.remove(n)
	
	## removeUser - Removes the user with the username specified from the list of users.
	## n        - The username of the user to remove.	
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
			self.checkIfBroadcaster()
			self.checkIfAdmin()
			self.checkIfOp()
		
		## checkIfAdmin - This method checks whether this user is an administrator.
		def checkIfAdmin(self):
			## The broadcaster of a channel is always an administrator.
			## For debugging purposes, I will always be an administrator.
			if ("albinohat" in self.name or self.checkIfBroadcaster()):
				self.bool_isadmin = 1
				return

			for admin in self.parent.list_of_admins:
				if (admin in self.name):
					self.bool_isadmin = 1
					break
		
		## checkIfBroadcaster - Checks whether this user is the broadcaster.
		def checkIfBroadcaster(self):
			if ((self.parent.channel in self.name)):
				self.bool_isbroadbaster = 1
				self.parent.addAdmin(self.name)

		## checkIfOp - Checks whether this user is an operator.
		def checkIfOp(self):
			for op in self.parent.list_of_ops:
				if (op in self.name):
					self.bool_isop = 1
					break
									
		## updateTimer - Updates the last time a user successfully issued a bot command.
		## Also resets spam counter. This is used for flood protection.
		def updateTimer(self):
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
	
	## getCurrentTimeAndTime - This method returns the current date and time as a couple of strings..
	## 0 - The current date.
	## 1 - The current time to the second.
	def getCurrentDateAndTime(self):
		return time.strftime("%Y-%m-%d", time.localtime()), time.strftime("%H-%M-%S", time.localtime())
	
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
			
	## LogFairy.ChatMessage - Describes an object which contains information about system, IRC and chat Bodys.
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
		
	## LogFairy.IRCMessage - Describes an object which contains information about system, IRC and chat Bodys.
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
	
	## LogFairy.SystemMessage - Describes an object which contains information about system, IRC and chat Bodys.
	class SystemMessage():
		## __init__   - This method initializes the IRCMessage object.
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
			self.body = Body

	## End of LogFairy.SystemMessage class
		
## End of LogFairy class
