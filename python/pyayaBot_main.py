## pyayaBot_main.py
## Author(s): Daniel "Albinohat" Mercado
## The main body of a twitch bot which listens for IRC Messages and offers features from the pyayaBot_features module.

## TODO [ NOT STARTED ], [ IN-PROGRESS ], [ TESTING ] or [ DONE ]
##

## BACKLOG [ NOT STARTED ], [ IN-PROGRESS ], [ TESTING ] or [ DONE ]
##
## Insert DEBUG-level system logging into existing methods. (Replace  '#' commented out print lines with writeLogMessage calls) [ NOT STARTED ]

## BUG FIXES
##

## Standard Imports
import json, os, re, socket, sys, time

## Third-party Imports
import pyayaBot_basicFeatureSet, pyayaBot_qlranksFeatureSet, pyayaBot_threading

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
	## self.channel_config_path     - The path to the channel configuration file. This can be edited via chat.
	## self.log_root                - The absolute or relative paths to the directory in which log files will be stored.
	## self.syslog_bitlist          - A bit mask supplied as a list of bools which determines what types of log entries to write.
	##                        Index - Value
	##                            0 - System > INFO
	##                            1 - System > WARNING
	##                            2 - System > ERROR
	##                            3 - System > DEBUG
	## self.log                     - A LogFairy object which will handle writing out log entries.
	## self.twitch                  - A socket object which will contain the IP/port pairs between the local machine and the twitch.tv IRC server.
	## self.list_of_feature_sets    - A list of dictionaries denoting which feature sets the bot will use as well as settings.
	## self.list_of_users           - A list of User objects to track users in a channel.
	## self.list_of_admins          - A list of strings containing the usernames of admins. (Broadcast + albinohat)
	## self.list_of_ops             - A list of strings containing the usernames of channel operators.
	## self.bool_[name]_feature_set - A boolean tracking whether or not this bot instance will have access to the [name] feature set.
	## self.bool_shutdown           - A boolean tracking whether or not the shut-down command has been issued.
	##
	## connection_config_path       - The absolute or relative path to the connection configuration file to initialize the Bot instance.
	## channel_config_path          - The absolute or relative path to the channel configuration file to initialize the Bot instance.
	## syslog_bitlist               - The list of binary values controlling which system logging types are enabled.
	def __init__(self, connection_config_path, channel_config_path, syslog_bitlist):
		print "                                ____        _     ____       _"
		print "                               |  _ \      | |   |  _ \     | |"
		print "  _ __  _   _  __ _ _   _  __ _| |_) | ___ | |_  | |_) | ___| |_ __ _"
		print " | '_ \| | | |/ _` | | | |/ _` |  _ < / _ \| __| |  _ < / _ \ __/ _` |"
		print " | |_) | |_| | (_| | |_| | (_| | |_) | (_) | |__ | |_) |  __/ |_| (_||"
		print " | .__/ \__, |\__,_|\__, |\__,_|____/ \___/ \__| |____/ \___|\__\__,_|"
		print " | |     __/ |       __/ |"
		print " |_|    |___/       |___/"

		print "\nInitializing Bot instance."

		## Initialize the channel configuration path, logging bit list, shut-down boolean, and lists of feature sets, admins, users and ops.
		self.channel_config_path  = channel_config_path
		self.syslog_bitlist       = syslog_bitlist
		self.bool_shutdown        = 0
		self.list_of_feature_sets = []
		self.list_of_users        = []
		## Admin list is maintained by the broadcaster. (ADMIN-level commands)
		self.list_of_admins       = []
		## Op list is maintained by the twitch.tv IRC server. (MODE messages)
		self.list_of_ops          = []

		print "\nParsing configuration files. Format: JSON..."

		## Call the methods to parse the connection and channel configuration files.
		## This will initialize all required attributes to spin-up logging, connect to the twitch.tv IRC server as well as initialize feature sets..	

		self.parseConnectionJson(connection_config_path)
		self.parseChannelJson(channel_config_path)

		print "Successfully parsed configuration files!"
		print "\nInitializing LogFairy..."

		## Initialize the LogFairy object using the log directory.
		self.log = LogFairy(self.channel, self.log_root, self.syslog_bitlist)

		print "Successfully initialized LogFairy!"
		print "\nConnecting to twitch.tv IRC server. (" + self.host + " Port " + str(self.port) + ")..."

		## Call the method to connect to the twitch.tv IRC server.
		self.connectToTwitch()

		print "Successfully connected to twitch.tv IRC server. (" + self.host + " Port " + str(self.port) + ")!"
		print "\nInitializing feature sets..."

		## Call the method to initialize the various feature set objects.
		self.initializeFeatureSets()
		
		print "Successfully initialized feature sets!"
		print "\nSeeding administrator list with broadcaster and development team..."

		## Add the broadcaster and devs to the list of admins.
		self.addAdmin(self.channel)
		self.addAdmin("albinohat")
		self.addAdmin("wrongwarped")

		print "Successfully seeded administrator list!"
		print "\nSuccessfully initialized Bot instance. All systems are GO!\n"

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
		pyayaBot_threading.WriteLogMessageThread(self.log, "admin", AdminMessage(self.log, "ADDED ADMIN", n))
		
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

		## Avoid reading a username to the list.
		for op in self.list_of_ops:
			if (op == n):
				return

		self.list_of_ops.append(n)
		pyayaBot_threading.WriteLogMessageThread(self.log, "admin", AdminMessage(self.log, "ADDED OP", n))

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
			self.addUser(User(self, name))

	## addUsersFromNamesList - Creates and adds the specified User objects to the user list.
	## names_list            - A list of usernames sent by the twitch.tv IRC server in a NAMES list. (Message type 366)
	def addUsersFromNamesList(self, names_list):
		for name in names_list:
			## Format the name in the long-version used by twitch.
			name = name = ":" + name + "!" + name + "@" + name + ".tmi.twitch.tv"

			## Check if the user is tracked. If not, add the user to the list.
			if (self.getIfKnownUser(name) == 0):
				self.addUser(User(self, name))	

	## connectToTwitch - This method connects to the twitch IRC server and joins the configured channel.
	def connectToTwitch(self):
		## Open the connection to twitch IRC and join the channel specified in the configuration file.
		self.twitch = socket.socket()
		try:
			self.twitch.connect((self.host, self.port))
		except socket.error:
			print "Failed to connect to twitch.tv IRC server. (" + self.host + " Port " + str(self.port) + ")!"
			pyayaBot_threading.WriteLogMessageThread(self.log, "system", SystemMessage(self.log, "ERROR", "Failed to connect to twitch.tv IRC server. (" + self.host + " Port " + str(self.port) + ")"))
			self.shutdownBot()

		self.twitch.send("PASS %s\r\n" % self.oauth) 
		self.twitch.send("NICK %s\r\n" % self.nick)
		self.twitch.send("USER %s %s bla :%s\r\n" % (self.ident, self.host, self.realname))
		self.twitch.send("JOIN #%s\r\n" % self.channel)

		pyayaBot_threading.WriteLogMessageThread(self.log, "system", SystemMessage(self.log, "INFO", "Successfully connected to twitch.tv IRC server. (" + self.host + " Port " + str(self.port) + ")"))

	## getIfKnownUser - This method will loop through the list of User objects.
	##                  It returns 0 if the user is not tracked in the list of users.
	##                  It returns 1 if the user is tracked in the list of users.
	## n              - The username of someone in the channel to check.
	def getIfKnownUser(self, n):
		bool_known = 0
		for user in self.list_of_users:
			if (n == user.name):
				bool_known = 1
				break

		return bool_known		
	
	## initializeFeatureSets - This method initializes feature set objects.
	def initializeFeatureSets(self):
		## Initialize booleans to enable or disable feature sets.
		self.bool_basic_feature_set     = 0
		self.bool_osu_feature_set       = 0
		self.bool_qlranks_feature_set   = 0
		self.bool_youtube_featre_set    = 0	

		## Call the methods to initialize the specified feature sets in the list.
		for fs in self.list_of_feature_sets:
			## Initialize a BasicFeatureSet instance.
			if (fs["name"] == "BasicFeatureSet"):
				print "\nDetected BasicFeatureSet. Initializing..."
				self.basic_feature_set      = pyayaBot_basicFeatureSet.BasicFeatureSet(self, fs)
				self.bool_basic_feature_set = 1
				## Start the child thread to periodically send the MOTD.
				self.send_motd_thread       = pyayaBot_threading.SendMotdThread(self, self.basic_feature_set.motd_cooldown, self.basic_feature_set.bool_motd_enabled)

				print "BasicFeatureSet initialized!\n"
			
			elif (fs["name"] == "OsuFeatureSet"):
				## Instantiate OsuFeatureSet object here.
				print "placeholder"
			
			elif (fs["name"] == "QLRanksFeatureSet"):
				print "Detected QLRanksFeatureSet. Initializing..."
				## Instantiate QLRanksFeatureSet object here.
				self.qlranks_feature_set      = pyayaBot_qlranksFeatureSet.QLRanksFeatureSet(self, fs)
				self.bool_qlranks_feature_set = 1
				print "QLRanksFeatureSet initialized!\n"

			elif (fs["name"] == "YouTubeFeatureSet"):
				## Instantiate YouTubeFeatureSet object here.
				print "placeholder"
			
			else:
				print "\nInvalid feature set \"" + fs["name"] + "\" detected. Ignoring...\n"
				pyayaBot_threading.WriteLogMessageThread(self.log, "system", SystemMessage(self.log, "WARNING", "Invalid feature set \"" + fs["name"] + "\" detected. Ignoring."))

	## listenLoop - This method enters an infinite loop and listens for text from the twitch.tv IRC Server.
	def listenLoop(self):
		while (self.bool_shutdown == 0):
			## Split data received from the twitch.tv IRC server into lines.
			read_buffer = self.twitch.recv(4096)
			temp = read_buffer.split("\n", 1000)
			for line in temp:
				if (line != "" and line != "\n" and line != "\r\n"):
					print line.strip()
					parse_line_from_twitch_thread = pyayaBot_threading.ParseLineFromTwitchThread(self, line.strip()).join()

	## parseChannelJson - This method opens the channel configuration file and parses it to ensure the correct values are set to initialize the Bot instance.
	def parseChannelJson(self, config_path):
		bool_listen_only = 1
		try:
			config_json = json.load(open(config_path))

		except IOError:
			print "    pyayaBot.Bot.parseChannelConfigJson(): Unable to open file: \"" + config_path + ".\""
			sys.exit()
			
		except ValueError:
			print "    pyayaBot.Bot.parseChannelConfigJson(): Invalid JSON detected."
			sys.exit()

		## Parse through each of the key value pairs of the entire JSON payload.
		for key, value in config_json.iteritems():
			if (key == "channel"):
				self.channel = value

			elif (key == "feature_sets"):
				## Parse through each JSON object contained in the feature_sets list.
				for fs in config_json["feature_sets"]:
					current_feature_set = {}
					for key, value in fs.iteritems():
						if (key == "name" and value == "BasicFeatureSet"):
							bool_listen_only = 0
						current_feature_set.update({key: value})
					
					## Add the dictionary containing all the feature set settings to the list of feature sets.
					self.list_of_feature_sets.append(current_feature_set)					
			else:
				print "    pyayaBot.Bot.parseChannelJson(): Invalid channel config entry: \"" + key + " -> " + value + ".\" Ignoring..."

		if (self.channel == "" or len(self.list_of_feature_sets) == 0):
			print "    pyayaBot.Bot.parseChannelJson(): One or more configuration entries were not set."
			print "    Please verify the configuration file's contents and try again."
			sys.exit()

		if (bool_listen_only == 1):
			print "\nBasicFeatureSet was not detected."
			print "This instance of pyayaBot is in listen-only mode. Local shut-down required.\n"

	## parseConnectionJson - This method opens the connection configuration JSON file and parses it to ensure the correct values are set to initialize the Bot instance.
	def parseConnectionJson(self, config_path):
		try:
			config_json = json.load(open(config_path))

		except IOError:
			print "    pyayaBot.Bot.parseConnectionJson(): Unable to open file: \"" + config_path + ".\""
			sys.exit()

		for key, value in config_json.iteritems():
			if (key == "host"):
				self.host = value
			elif (key == "port"):
				self.port = value
			elif (key == "nick"):
				self.nick = value
				self.ident = self.nick
			elif (key == "pass"):
				self.oauth = value
			elif (key == "realname"):
				self.realname = value
			elif (key == "log_root"):
				self.log_root = value
			else:
				print "    pyayaBot.Bot.parseConnectionJson(): Invalid config entry: \"" + key + ".\" Ignoring..."

		if (self.host == "" or self.port == 0 or self.nick == "" or self.oauth == "" or self.realname == "" or self.log_root == ""):
			print "    pyayaBot.Bot.parseConnectionJson(): One or more configuration entries were not set."
			print "    Please verify the configuration file's contents and try again."
			sys.exit()

	## parseLineFromTwitch - This method will strip the ending white space from and parse a line of text form the twitch.tv IRC server, splitting it up and determining its log type and corresponding values.
	## line                - The message sent from listenLoop().
	def parseLineFromTwitch(self, line):		
		if (line == ""):
			pyayaBot_threading.WriteLogMessageThread(self.log, "system", SystemMessage(self.log, "WARNING", "NULL message from twitch.tv IRC server. Ignoring.")).join()
			return

		line_parts = line.split(" ", 3)
		if (len(line_parts) < 2):
			pyayaBot_threading.WriteLogMessageThread(self.log, "system", SystemMessage(self.log, "WARNING", "Fragmented message \"" + line + "\" from twitch.tv IRC server. Ignoring.")).join()
			return

		elif (len(line_parts) == 2):
			if (line_parts[0] == "PING"):
				print "PONG " + line_parts[1]
				self.twitch.send("PONG " + line_parts[1] + "\r\n")

				type = line_parts[1]
				body = "N/A"
				pyayaBot_threading.WriteLogMessageThread(self.log, "irc", IRCMessage(self.log, type, body))	.join()

		elif (len(line_parts) == 3):
			if (line_parts[1] == "JOIN" and line_parts[2] == "#" + self.channel):
				type = line_parts[1]
				body = line_parts[0]
				pyayaBot_threading.WriteLogMessageThread(self.log, "irc", IRCMessage(self.log, type, body)).join()

				self.addUserFromJoinMessage(body)

			elif (line_parts[1] == "PART" and line_parts[2] == "#" + self.channel):
				type = line_parts[1]
				body = line_parts[0].strip()
				pyayaBot_threading.WriteLogMessageThread(self.log, "irc", IRCMessage(self.log, type, body)).join()

				## Remove the user from the list of tracked users.
				self.removeUser(body)

		elif (len(line_parts) == 4):
			if (re.match("[0-9]{3}", line_parts[1]) and line_parts[2] == "pyayabot"):
				type = line_parts[1]
				body = line_parts[3]
				pyayaBot_threading.WriteLogMessageThread(self.log, "irc", IRCMessage(self.log, type, body)).join()

				## Create and add users from the NAMES list.
				if (line_parts[1] == "353"):
					names_list = line_parts[3][len(self.channel) + 5:]
					self.addUsersFromNamesList(names_list)

			elif (line_parts[1] == "MODE"):
				type = line_parts[1]
				body = line_parts[3]

				mode_list = body.split(" ", 1)
				if (mode_list[0] == "+o"):
					self.addOp(mode_list[1])
				elif (mode_list[0] == "-o"):
					self.removeOp(mode_list[1])
				else:
					pyayaBot_threading.WriteLogMessageThread(self.log, "system", SystemMessage(self.log, "WARNING", "Invalid MODE operation: \"" + mode_list[0] + "\". Ignoring.")).join()
					return

				pyayaBot_threading.WriteLogMessageThread(self.log, "irc", IRCMessage(self.log, type, body)).join()

			elif (line_parts[1] == "PRIVMSG"):
				user = line_parts[0]
				body = line_parts[3][1:].rstrip()
				pyayaBot_threading.WriteLogMessageThread(self.log, "chat", ChatMessage(self.log, user, body)).join()

				## Check if the user is tracked. If not, add the user to the list.
				if (self.getIfKnownUser(user) == 0):
					self.addUser(User(self, user))

				## Parse the chat message from the user to determine if a command was issued.
				if (self.basic_feature_set.checkIfCommand(body) and self.basic_feature_set.checkIfEnabled()):
					pyayaBot_threading.ExecuteCommandThread(self, "basic", pyayaBot_basicFeatureSet.Command(user, body)).join()
			
				if (self.qlranks_feature_set.checkIfCommand(body) and self.qlranks_feature_set.checkIfEnabled()):
					pyayaBot_threading.ExecuteCommandThread(self, "qlranks", pyayaBot_basicFeatureSet.Command(user, body)).join()
		
			else:
				pyayaBot_threading.WriteLogMessageThread(self.log, "system", SystemMessage(self.log, "WARNING", "Unknown message type received from twitch.tv IRC server: \"" + line_parts[1] + "\". Ignoring.")).join()
		else:
			pyayaBot_threading.WriteLogMessageThread(self.log, "system", SystemMessage(self.log, "WARNING", "Unexpected # of words in message \"" + line + " \". Ignoring")).join()

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

				pyayaBot_threading.WriteLogMessageThread(self.log, "admin", AdminMessage(self.log, "REMOVED ADMIN", n)).join()

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

				pyayaBot_threading.WriteLogMessage(self, "admin", AdminMessage(self.log, "REMOVED OP", n)).join()

		#self.printOps()

	## removeUser - Removes the user with the username specified from the list of users.
	## n          - The username of the user to remove.	
	def removeUser(self, n):
		for user in self.list_of_users:
			if (user.name == n):
				self.list_of_users.remove(user)
				break

	## sendChatMessage - Sends a message to the twitch server as well as STDOUT.
	## t               - The text to be sent as a string.
	def sendChatMessage(self, t):
		print ":pyayabot!pyayabot@pyayabot.tmi.twitch.tv PRIVMSG #" + self.channel + " :" + t
		self.twitch.send("PRIVMSG #" + self.channel + " :" + t + "\r\n")
		pyayaBot_threading.WriteLogMessageThread(self.log, "chat", ChatMessage(self.log, ":pyayabot!pyayabot@pyayabot.tmi.twitch.tv", t)).join()

	## This method gracefully disconnects the bot from the channel and exits.
	def shutdownBot(self):
		self.bool_shutdown = 1
		self.sendChatMessage("Shutting down...")
		self.twitch.close()
		pyayaBot_threading.WriteLogMessageThread(self.log, "system", SystemMessage(self.log, "INFO", "Bot shut-down via chat.")).join()

		## Write the closing HTML tags to the log files.
		self.log.writeLogFooters(self.log.system_log_path)
		self.log.writeLogFooters(self.log.chat_log_path)
		self.log.writeLogFooters(self.log.irc_log_path)
		self.log.writeLogFooters(self.log.admin_log_path)

		print "\nWaiting on the following threads to return...\n"
		for thread in pyayaBot_threading.threading.enumerate():
			print str(thread)

		sys.exit()

## End of Bot class.

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

	## printUser - Prints the attributes of the User instance.
	def printUser(self):
		print "    User.printUser()"
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

	## updateLastCommandTime - Updates the last time a user successfully issued a bot command.
	## Also resets spam counter. This is used for flood protection.
	def updateLastCommandTime(self):
		self.last_command_time = time.time()
		self.spam_count        = 0

## End of Bot.User class

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
		for log_count in range(1000):
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

		pyayaBot_threading.WriteLogMessageThread(self, "system", SystemMessage(self, "INFO", "SYSTEM LOG CREATED"))

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

		pyayaBot_threading.WriteLogMessageThread(self, "system", SystemMessage(self, "INFO", "CHAT LOG CREATED"))

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

		pyayaBot_threading.WriteLogMessageThread(self, "system", SystemMessage(self, "INFO", "IRC LOG CREATED"))

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

		pyayaBot_threading.WriteLogMessageThread(self, "system", SystemMessage(self, "INFO", "ADMIN LOG CREATED"))

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
			pyayaBot_threading.WriteLogMessageThread(self, "system", SystemMessage(self, "ERROR", "Invalid log found type while writing top row."))
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

	## writeLogMessage - Opens, writes an entry to and then closes a log file.
	## message         - A SystemMessage object containing the values to write into a log file.
	## log_type        - Which of the 4 (Admin, Chat, IRC, System) log files to which the message should be written.
	def writeLogMessage(self, log_type, message):
		## Open the correct file and set the value of the third column based on the log type.
		if (log_type == "admin"):
			column_three = message.action
			write_handle = open(self.admin_log_path, "a")
		elif (log_type == "chat"):
			write_handle = open(self.chat_log_path, "a")
			column_three = message.user
		elif (log_type == "irc"):
			column_three = message.type
			write_handle = open(self.irc_log_path, "a")		
		## Only write the log entry if it is enabled by the bitlist.
		elif ((log_type == "system") and (self.syslog_bitlist[0] == "1" and message.level == "INFO") or (self.syslog_bitlist[1] == "1" and message.level == "WARNING") or (self.syslog_bitlist[2] == "1" and message.level == "ERROR") or (self.syslog_bitlist[3] == "1" and message.level == "DEBUG")):
			column_three = message.level
			write_handle = open(self.system_log_path, "a")
		else:
			pyayaBot_threading.WriteLogMessageThread(self, "system", "WARNING", "Invalid log type \"" + log_type + "\" found while writing a message.")
			return

		write_handle.write("	<tr>\n")
		write_handle.write("		<td height=\"17\" align=\"left\">" + message.date + "</td>\n")
		write_handle.write("		<td align=\"left\">" + message.time + "</td>\n")
		write_handle.write("		<td align=\"left\">" + column_three + "</td>\n")
		write_handle.write("		<td align=\"left\">" + message.body + "</td>\n")
		write_handle.write("	</tr>\n")			

		write_handle.close()

## End of LogFairy class

## AdminMessage - Describes an object which contains information about administrative changes. (Admin/Op adds/removes timeouts/bans)
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

	## Print out the attributes of this AdminMessage instance.
	def printAdminMessage(self):
		print "    AdminMessage.printAdminMessage()"
		print "        self.date: " + self.date
		print "        self.time: " + self.time
		print "        self.action: " + self.action
		print "        self.body: " + self.body

## End of AdminMessage class.

## ChatMessage - Describes an object which contains information about chat messages.
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

	## Print out the attributes of this ChatMessage instance.
	def printChatMessage(self):
		print "    ChatMessage.printChatMessage()"
		print "        self.date: " + self.date
		print "        self.time: " + self.time
		print "        self.user: " + self.user
		print "        self.body: " + self.body

## End of ChatMessage class

## IRCMessage - Describes an object which contains information IRC messages from the twitch.tv IRC server.
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

	## Print out the attributes of this IRCMessage instance.
	def printIRCMessage(self):
		print "    IRCMessage.printIRCMessage()"
		print "        self.date: " + self.date
		print "        self.time: " + self.time
		print "        self.type: " + self.type
		print "        self.body: " + self.body

## End of IRCMessage class

## SystemMessage - Describes an object which contains information about system messages.
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

	## Print out the attributes of this SystemMessage instance.
	def printSystemMessage(self):
		print "    SystemMessage.printSystemMessage()"
		print "        self.date: " + self.date
		print "        self.time: " + self.time
		print "        self.level: " + self.level
		print "        self.body: " + self.body

## End of SystemMessage class
