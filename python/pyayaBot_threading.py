## pyayaBot_threading.py
## Author(s): Daniel "Albinohat" Mercado
## This module contains the special thread subclasses used by pyayaBot.

## TODO [ NOT STARTED ], [ IN-PROGRESS ], [ TESTING ] or [ DONE ]
## 

## BUG FIXES
## 

## BACKLOG [ NOT STARTED ], [ IN-PROGRESS ], [ TESTING ] or [ DONE ]
## 

## Standard imports
import threading, time

## Third-party imports
import pyayaBot_main, pyayaBot_basicFeatureSet, pyayaBot_qlranksFeatureSet

## ExecuteCommandThread - A thread which parses through and executes a command.
class ExecuteCommandThread(threading.Thread):
	## __init__ - Initializes the attributes of the parseLineFromTwitchThread instance.
	## self.parent      - The pyayaBot_main.Bot instance which spawned this thread.
	## self.feature_set - The feature set whose executeCommand method should be called.
	## self.thread_id   - A unique ID assigned to each thread.
	## self.command     - The command to execute as a Command object.
	def __init__(self, parent, feature_set, command):
		threading.Thread.__init__(self)
		self.parent      = parent
		self.feature_set = feature_set
		self.thread_id   = threading.activeCount() + 1
		self.command     = command

		self.start()

	## run - This method calls the executeCommand method of the specified feature set.
	def run(self):
		if (self.feature_set == "basic"):
			self.parent.basic_feature_set.executeCommand(self.command)
		elif (self.feature_set == "qlranks"):
			self.parent.qlranks_feature_set.executeCommand(self.command)
	
## End of ExecuteCommandThread class.	

## ParseLineFromTwitchThread - A thread which parses through a line of text from the twitch.tv IRC server.
class ParseLineFromTwitchThread(threading.Thread):
	## __init__ - Initializes the attributes of the parseLineFromTwitchThread instance.
	## self.parent    - The pyayaBot_main.Bot instance which spawned this thread.
	## self.thread_id - A unique ID assigned to each thread.
	## self.line      - The line of text to be parsed from the twitch.tv IRC server.
	def __init__(self, parent, line):
		threading.Thread.__init__(self)
		self.parent    = parent
		self.thread_id = threading.activeCount() + 1
		self.line      = line

		self.start()

	## run - This method calls the parseLineFromTwitch method.
	def run(self):
		self.parent.parseLineFromTwitch(self.line)

## End of ParseLineFromTwitchThread class.	

## SendMotdThread - A thread which sends the MOTD to the chat.
class SendMotdThread(threading.Thread):
	## __init__ - Initializes the attributes of the parseLineFromTwitchThread instance.
	## self.parent            - The pyayaBot_main.Bot instance which spawned this thread.
	## self.thread_id         - A unique ID assigned to each thread.
	## self.delay             - The amount of time to wait before sending the MOTD.
	## self.bool_motd_enabled - A boolean tracking whether or not to send the MOTD to the chat.
	def __init__(self, parent, delay, bool_motd_enabled):
		threading.Thread.__init__(self)
		self.parent            = parent
		self.thread_id         = threading.activeCount() + 1
		self.delay             = delay
		self.bool_motd_enabled = bool_motd_enabled

		self.start()

	## run - This method calls the pyayaBot_featureSets.BasicFeatureSet.sendMotd method.
	def run(self):
		while (1):
			for x in range(int(self.delay)):
				time.sleep(1)
				if (self.parent.bool_shutdown == 1):
					return

			if (self.bool_motd_enabled == 1):
				self.parent.basic_feature_set.sendMotd()

	## updateDelay - Updates the amount of time to wait before sending the MOTD.
	## delay       - The amount of time to wait before sending the MOTD.
	def updateDelay(self, delay):
		self.delay = delay

	## updateBool - Updates the boolean tracking whether or not to send the MOTD to chat.
	## bool       - The new value (0 or 1) to set.
	def updateBool(self, bool):
		self.bool_motd_enabled = bool

## End of the SendMotdThread class.

## SendQLPlayerInfoThread - A thread which initializes a QLPlayer object by parsing a QLRanks webpage and sends info about that player to the chatroom.
class SendQLPlayerInfoThread(threading.Thread):
	## __init__ - Initializes the attributes of the parseLineFromTwitchThread instance.
	## self.grand_parent - The pyayaBot_main.Bot instance which spawned this thread.
	## self.info_type    - The type of player info (lastgame, maps, profile, stats) to send to the chatroom.
	## self.thread_id    - A unique ID assigned to each thread.
	## self.player_obj   - The newly created object to pass to the add method.
	def __init__(self, grand_parent, info_type, player_obj):
		threading.Thread.__init__(self)
		self.grand_parent = grand_parent
		self.info_type    = info_type
		self.thread_id    = threading.activeCount() + 1
		self.player_obj   = player_obj

		self.start()

	## run - This method calls the pyayaBot_qlranksFeatureSet.QLRanksFeatureSet.sendQLPlayerInfo method.
	def run(self):
		self.grand_parent.qlranks_feature_set.sendQLPlayerInfo(self.info_type, self.player_obj)

## End of SendQLPlayerInfoThread class

## WriteLogMessageThread - A thread which writes an entry to the a log file.
class WriteLogMessageThread(threading.Thread):
	## __init__ - Initializes the attributes of the parseLineFromTwitchThread instance.
	## self.log       - The pyayaBot_main.LogFairy instance which will handle logging.
	## self.thread_id - A unique ID assigned to each thread.
	## self.line      - The line of text to be parsed.
	## self.log_type  - Which of the 4 (Admin, Chat, IRC, System) log files to which the message should be written.
	def __init__(self, log, log_type, message):
		threading.Thread.__init__(self)	
		self.log       = log
		self.thread_id = threading.activeCount() + 1
		self.log_type  = log_type
		self.message   = message

		self.start()

	## run - This method calls the pyayaBot_main.LogFairy.writeToAdminLog method.
	def run(self):	
		self.log.writeLogMessage(self.log_type, self.message)

## End of WriteLogMessageThread class.
