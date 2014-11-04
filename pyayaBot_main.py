##pyayaBot_main.py
##The main body of a Twitch bot which listens for IRC Bodys.

## TODO
## Objectify Messages [ DONE ] 
## Add method to print a single Eser object

##Socket library
import socket, re, sys, time, os, subprocess

## Bot - This class contains the most basic operations of pyayaBot.
class Bot():
	## __init__      - This method sets up the bot using a configuration file, connects to the Twitch IRC server and starts the main listening loop.
	## self.host     - The IP of the Twitch.TV IRC server.
	## self.port     - The port of the Twitch.TV IRC server.
	## self.nick     - The nickname (username) of the Bot instance.
	## self.oauth    - The password (OAuth token) of the Bot instance.
	## self.ident    - The identity of the Bot instance. (Must be the same as nickname)
	## self.realname - Used as a credits field. Please always initialize to give credits to Albinohat.
	## self.channel  - The chatroom the bot will join. A single bot instance must join only one channel at a time. (For now)
	## self.log_dir  - The absolute or relative paths to the directory in which log files will be stored.				
	## self.log      - A LogFairy object which will handle writing out log entries.
	## self.twitch   - A socket object which will contain the IP/port pairs between the local machine and the Twitch.TV IRC server.
	## config_path   - The absolute or relative path to the configuration file to initialize the Bot instance.
	def __init__(self, config_path):
		self.realname = "pyayaBot by https://github.com/pyayaBotDevs"
			
		## Call the method to parse the configuration file.
		self.parseConfigFile(config_path)
		
		## Initialize the LogFairy object using the log directory.
		self.log = LogFairy(self.channel, self.log_dir)
		
		## Call the method to connect to the Twitch.TV IRC server.
		self.connectToTwitch()
		
		## Call the method to listen for messages from the Twitch.TV IRC server.
		self.listenLoop()
		
	## connectToTwitch - This method connects to the Twitch IRC server and joins the configured channel.
	def connectToTwitch(self):
		##Open the connection to Twitch IRC
		self.twitch = socket.socket()
		self.twitch.connect((self.host, self.port))
		self.twitch.send("PASS %s\r\n" % self.oauth) 
		self.twitch.send("NICK %s\r\n" % self.nick)
		self.twitch.send("USER %s %s bla :%s\r\n" % (self.ident, self.host, self.realname))
		self.twitch.send("JOIN %s\r\n" % self.channel)

	## listenLoop - This method enters an infinite loop and listens for text from the Twitch.TV IRC Server.
	def listenLoop(self):
		while (1):
			## Split data received from the Twitch.TV IRC server into lines.
			self.read_buffer = self.twitch.recv(4096)
			self.temp = self.read_buffer.split("\n", 10000)
			self.readbuffer = self.temp.pop()
			for line in self.temp:
				print line
				self.parseLineFromTwitch(line)
				
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
		elif (line_parts[1] == "PART"):
			type = line_parts[1]
			body = line_parts[0].rstrip()
			self.log.writeToIRCLog(self.log.IRCMessage(self.log, type, body))
		elif (line_parts[1] == "MODE"):
			type = line_parts[1]
			body = (line_parts[2] + " " + line_parts[3]).rstrip()
			self.log.writeToIRCLog(self.log.IRCMessage(self.log, type, body))
		elif (line_parts[0] == "PING"):
			type = line_parts[1]
			body = "N/A"
			self.log.writeToIRCLog(self.log.IRCMessage(self.log, type, body))	
		elif (line_parts[1] == "PRIVMSG"):
			user = line_parts[1]
			body = line_parts[3].rstrip()
			self.log.writeToChatLog(self.log.ChatMessage(self.log, user, body))

	## parseConfigFile - This method opens the configuration file and parses it to ensure the correct values are set to initialize the Bot instance.
	def parseConfigFile(self, config_path):
		try:
			config_file = open(config_path, "r")
		except IOError:
			print "    pyayaBot.Bot.parseConfigFile(): Unable to open file: \"" + c + ".\""
		
		for line in config_file:
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
			elif (self.line_list[0] == "LOG_DIR"):
				self.log_dir = self.line_list[1].rstrip()
			else:
				print "    pyayaBot.Bot.parseConfigFile(): Invalid config entry: \"" + self.line_list[0] + ".\""
		
		if (self.host == "" or self.port == 0 or self.nick == "" or self.oauth == "" or self.channel == ""):
			print "    pyayaBot.Bot.parseConfigFile(): One of more configuration entries were not set."
			print "    Please verify the configuration file's contents and try again."
			sys.exit()
		
		config_file.close()

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
	def __init__(self, channel, log_dir):
		self.date, self.time = self.getCurrentDateAndTime()

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
			self.system_log = open(log_dir + "\\pyayaBot_" + channel + "_systemlog_" + self.date + "_" + self.time + ".csv", "w+")
		except IOError:
			print "    pyayaBot.LogFairy.__init__(): Unable to open file: \"" + log_dir + "\\pyayaBot_systemlog_" + self.date + "_" + self.time + ".csv.\""
			sys.exit()

		self.system_log.write("Date,Time,Level,Body\n")
		self.writeToSystemLog(self.SystemMessage(self, "INFO","SYSTEM LOG CREATED"))

		## Open the handle to the chat log file, write the header row and log the action to the system log.		
		try:
			self.chat_log = open(log_dir + "\\pyayaBot_" + channel + "_chatlog_" + self.date + "_" + self.time + ".csv", "w+")
		except IOError:
			print "    pyayaBot.LogFairy.__init__(): Unable to open file: \"" + log_dir + "\\pyayaBot_chatlog_" + self.date + "_" + self.time + ".csv.\""
			sys.exit()
			
		self.chat_log.write("Date,Time,User,Body\n")
		self.writeToSystemLog(self.SystemMessage(self, "INFO","CHAT LOG CREATED"))
		
		## Open the handle to the IRC log file, write the header row and log the action to the system log.		
		try:
			self.irc_log = open(log_dir + "\\pyayaBot_" + channel + "_irclog_" + self.date + "_" + self.time + ".csv", "w+")
		except IOError:
			print "    pyayaBot.LogFairy.__init__(): Unable to open file: \"" + log_dir + "\\pyayaBot_irclog_" + self.date + "_" + self.time + ".csv.\""		
			sys.exit()

		self.irc_log.write("Date,Time,Type,Body\n")
		self.writeToSystemLog(self.SystemMessage(self, "INFO","IRC LOG CREATED"))
	
	## getCurrentTimeAndTime - This method returns the current date and time as a tuple of strings..
	## 0 - The current date.
	## 1 - The current time to the second.
	def getCurrentDateAndTime(self):
		return time.strftime("%Y-%m-%d", time.localtime()), time.strftime("%H-%M-%S", time.localtime())
	
	## writeToChatLog - Writes an entry to the chat log file.
	## message - A ChatMessage object containing the values to write into the chat log.
	def writeToChatLog(self, message):
		self.chat_log.write(message.date + "," + message.time + "," + message.user + "," + message.body + "\n")

	## writeToIRCLog - Writes an entry to the IRC log file.
	## message - An IRCMessage object containing the values to write into the IRC log.
	def writeToIRCLog(self, message):
		self.irc_log.write(message.date + "," + message.time + "," + message.type + "," + message.body + "\n")

	## writeToSystemLog - Writes an entry to the IRC log file.
	## message - A SystemMessage object containing the values to write into the system log.
	def writeToSystemLog(self, message):
		self.system_log.write(message.date + "," + message.time + "," + message.level + "," + message.body + "\n")

	## LogFairy.ChatMessage class - This class describes an object which contains information about system, IRC and chat Bodys.
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
		
	## LogFairy.IRCMessage class - This class describes an object which contains information about system, IRC and chat Bodys.
	class IRCMessage():
		## __init__ - This method initializes the IRCMessage object.
		## self.date - The current date.
		## self.time - The current time.
		## self.type - The type of message. (###, NAMES, JOIN, PART, MOD, DEMOD)
		## self.body - The body of the message.
		## parent    - A handle to the parent LogFairy instance calling method.
		def __init__(self, parent, type, Body):
			## Initialize and set the time & date for this IRCMessage object.
			self.date, self.time = LogFairy.getCurrentDateAndTime(parent)
			
			## Initialize the type and body of the IRCMessage object.
			self.type = type
			self.body = Body
	
	## End of LogFairy.IRCMessage class
	
	## LogFairy.SystemMessage class - This class describes an object which contains information about system, IRC and chat Bodys.
	class SystemMessage():
		## __init__   - This method initializes the IRCMessage object.
		## self.date  - The current date.
		## self.time  - The current time.
		## self.level - The level (Severity) of the message. (INFO, WARNING, ERROR)
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

##User class - Contains information and methods for users in chat.
class User():
	##__init__ - Initialize the attributes of a User object.
	## self.name - The username of the user.
	## self.bool_isop - A boolean tracking whether the user is a channel operator.
	## self.bool_isadmin - A boolean tracking whether the user is the broadcaster. (stream owner)
	## self.last_command_time - The number of seconds since the last bot command was issued.
	## self.spam_count - A counter which keeps track of the number of times a user has spammed. (Sent bot commands too quickly)
	## self.timeout_count - A counter which keeps track of how many times the user has been timed out in chat.
	def __init__(self, name):
		#print "        In User class Object! Hit __init__\n"
		self.name               = name
		self.bool_isop          = 0
		self.bool_isbroadbaster = 0		
		self.last_command_time  = 0
		self.spam_count         = 1
		self.timeout_count      = 0
		self.checkIfOp()
		self.checkIfAdmin()
	
	##checkIfOp - Checks whether this user is an operator.
	def checkIfOp(self):
		for op in op_list:
			if (self.name == op):
				self.bool_isop == 1
				break
		#if(self.bool_isop == 1):
		#	print "    In User class Object! " + self.name + " is an op!\n"
		#else:
		#	print "    In User class Object! " + self.name + " is not an op!\n"

	##checkIfAdmin - Checks whether this user is an administrator.
	def checkIfAdmin(self):
		if (self.name == CHANNEL[1:] or self.name == "albinohat"):
			self.bool_isadmin = 1
			admin_list.append(self.name)
		#if(self.bool_isadmin == 1):
		#	print "    In User class Object! " + self.name + " is an admin!\n"
		#else:
		#	print "    In User class Object! " + self.name + " is not an admin!\n"
			
	##updateTimer - Updates the last time a user successfully issued a bot command.
	##              Also resets spam coutner. This is used for flood protection.
	def updateTimer(self):
		self.last_command_time = time.time()
		self.spam_count        = 0

	##printUser - Prints the user's public attributes.
	def printUser(self):
		print "        In User.printUser"
		print "            self.name: " + self.name
		print "            self.bool_isop: " + str(self.bool_isop)
		print "            self.bool_isadmin: " + str(self.bool_isadmin)		
		print "            self.last_command_time: " + str(self.last_command_time)
		print "            self.spam_count: " + str(self.spam_count)
		print "            self.timeout_count: " + str(self.timeout_count) + "\n"

## End of User class

## End of pyayaBot_main.py
