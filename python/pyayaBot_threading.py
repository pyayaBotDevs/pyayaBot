## pyayaBot_threading.py
## Author(s): Daniel "Albinohat" Mercado
## This module contains the special thread subclasses used by pyayaBot.

## TODO [ NOT STARTED ], [ IN-PROGRESS ], [ TESTING ] or [ DONE ]
## Implement addQLPlayerThread class [ IN-PROGRESS ]
## Merge the 4 addQLPlayerAndSendQLPlayerXThread classes into one class. [ NOT STARTED ]
## Merge the 4 writeToXLogThread classes into one class.

## BUG FIXES
## 

## BACKLOG [ NOT STARTED ], [ IN-PROGRESS ], [ TESTING ] or [ DONE ]
##

## Standard imports
import threading, time

## Third-party imports
import pyayaBot_main

## addQLPlayerThreadAndSendQLPlayerLastGame - A thread which initializes a QLPlayer object by parsing a QLRanks webpage and sends the QL player's last game to the chat.
class addQLPlayerAndSendQLPlayerLastGameThread(threading.Thread):
	## __init__ - Initializes the attributes of the parseLineFromTwitchThread instance.
	## self.grand_parent - The pyayaBot_main.Bot instance which spawned this thread.
	## self.thread_id    - A unique ID assigned to each thread.
	## self.player_obj   - The newly created object to pass to the add method.
	def __init__(self, grand_parent, player_obj):
		threading.Thread.__init__(self)
		self.grand_parent = grand_parent
		self.thread_id    = threading.activeCount() + 1
		self.player_obj   = player_obj
		
		self.start()

	## run - This method calls the pyayaBot_featureSets.QLRanksFeatureSet.addQLPlayer and pyayaBot_featureSets.QLRanksFeatureSet.sendQLPlayerLastGame methods.
	def run(self):
		self.grand_parent.qlranks_feature_set.addQLPlayer(self.player_obj)
		self.grand_parent.qlranks_feature_set.sendQLPlayerLastGame(self.player_obj)

## End of AddQLPlayerThreadAndSendQLPlayerLastGameThread class

## AddQLPlayerAndSendQLPlayerMapThread - A thread which initializes a QLPlayer object by parsing a QLRanks webpage and sends the QL player's top 3 most played maps to the chat.
class AddQLPlayerAndSendQLPlayerMapThread(threading.Thread):
	## __init__ - Initializes the attributes of the parseLineFromTwitchThread instance.
	## self.grand_parent - The pyayaBot_main.Bot instance which spawned this thread.
	## self.thread_id    - A unique ID assigned to each thread.
	## self.player_obj   - The newly created object to pass to the add method.
	def __init__(self, grand_parent, player_obj):
		threading.Thread.__init__(self)
		self.grand_parent = grand_parent
		self.thread_id    = threading.activeCount() + 1
		self.player_obj   = player_obj
		
		self.start()

	## run - This method calls the pyayaBot_featureSets.QLRanksFeatureSet.addQLPlayer and pyayaBot_featureSets.QLRanksFeatureSet.sendQLPlayerMaps methods.
	def run(self):
		self.grand_parent.qlranks_feature_set.addQLPlayer(self.player_obj)
		self.grand_parent.qlranks_feature_set.sendQLPlayerMaps(self.player_obj)

## End of AddQLPlayerThreadAndSendQLPlayerMapsThread class
		
## AddQLPlayerAndSendQLPlayerProfileThread - A thread which initializes a QLPlayer object by parsing a QLRanks webpage and sends the QL player's duel profile URL to the chat.
class AddQLPlayerAndSendQLPlayerProfileThread(threading.Thread):
	## __init__ - Initializes the attributes of the parseLineFromTwitchThread instance.
	## self.grand_parent - The pyayaBot_main.Bot instance which spawned this thread.
	## self.thread_id    - A unique ID assigned to each thread.
	## self.player_obj   - The newly created object to pass to the add method.
	def __init__(self, grand_parent, player_obj):
		threading.Thread.__init__(self)
		self.grand_parent = grand_parent
		self.thread_id    = threading.activeCount() + 1
		self.player_obj   = player_obj
		
		self.start()

	## run - This method calls the pyayaBot_featureSets.QLRanksFeatureSet.addQLPlayer and pyayaBot_featureSets.QLRanksFeatureSet.sendQLPlayerProfile methods.
	def run(self):
		self.grand_parent.qlranks_feature_set.addQLPlayer(self.player_obj)
		self.grand_parent.qlranks_feature_set.sendQLPlayerProfile(self.player_obj)

## End of AddQLPlayerThreadAndSendQLPlayerProfileThread class
		
## AddQLPlayerAndSendQLPlayerStatsThread - A thread which initializes a QLPlayer object by parsing a QLRanks webpage and sends the QL player's vital stats to the chat.
class AddQLPlayerAndSendQLPlayerStatsThread(threading.Thread):
	## __init__ - Initializes the attributes of the parseLineFromTwitchThread instance.
	## self.grand_parent - The pyayaBot_main.Bot instance which spawned this thread.
	## self.thread_id    - A unique ID assigned to each thread.
	## self.player_obj   - The newly created object to pass to the add method.
	def __init__(self, grand_parent, player_obj):
		threading.Thread.__init__(self)
		self.grand_parent = grand_parent
		self.thread_id    = threading.activeCount() + 1
		self.player_obj   = player_obj
		
		self.start()

	## run - This method calls the pyayaBot_featureSets.QLRanksFeatureSet.addQLPlayer and pyayaBot_featureSets.QLRanksFeatureSet.sendQLPlayerStats methods.
	def run(self):
		self.grand_parent.qlranks_feature_set.addQLPlayer(self.player_obj)
		self.grand_parent.qlranks_feature_set.sendQLPlayerStats(self.player_obj)

## End of AddQLPlayerThreadAndSendQLPlayerStatsThread class

## ExecuteCommandThread - A thread which parses through and executes a command.
class ExecuteCommandThread(threading.Thread):
	## __init__ - Initializes the attributes of the parseLineFromTwitchThread instance.
	## self.parent    - The pyayaBot_main.Bot instance which spawned this thread.
	## self.thread_id - A unique ID assigned to each thread.
	## self.command   - The command to execute as a Command object.
	def __init__(self, parent, command):
		threading.Thread.__init__(self)
		self.parent    = parent
		self.thread_id = threading.activeCount() + 1
		self.command   = command
		
		self.start()

	## run - This method calls the pyayaBot_featureSets.BasicFeatureSet.executeCommand method.
	def run(self):
		self.parent.basic_feature_set.executeCommand(self.command)

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
	## self.parent      - The pyayaBot_main.Bot instance which spawned this thread.
	## self.thread_id   - A unique ID assigned to each thread.
	## self.delay       - The amount of time to wait before sending the MOTD.
	## self.bool_update - A boolean tracking whether or not to reset the loop with the new delay.
	def __init__(self, parent, delay):
		threading.Thread.__init__(self)
		self.parent      = parent
		self.thread_id   = threading.activeCount() + 1
		self.delay       = delay
		self.bool_update = 0
		
		self.start()

	## run - This method calls the pyayaBot_featureSets.BasicFeatureSet.sendMotd method.
	def run(self):
		while (1):
			for x in range(int(self.delay)):
				time.sleep(1)
				if (self.parent.bool_shutdown == 1):
					return

			self.parent.basic_feature_set.sendMotd()

	## updateDelay - Updates the amount of time to wait before sending the MOTD.
	def updateDelay(self, delay):
		self.delay = delay

## End of the SendMotdThread class.

## WriteToAdminLogThread - A thread which writes an entry to the Admin log file.
class WriteToAdminLogThread(threading.Thread):
	## __init__ - Initializes the attributes of the parseLineFromTwitchThread instance.
	## self.parent    - The pyayaBot_main.Bot instance which spawned this thread.
	## self.thread_id - A unique ID assigned to each thread.
	## self.line      - The line of text to be parsed.
	def __init__(self, parent, message):
		threading.Thread.__init__(self)	
		self.parent    = parent
		self.thread_id = threading.activeCount() + 1
		self.message   = message

		self.start()

	## run - This method calls the pyayaBot_main.LogFairy.writeToAdminLog method.
	def run(self):
		self.parent.log.writeToAdminLog(self.message)

## End of WriteToAdminlogThread class.

## WriteToChatLogThread - A thread which writes an entry to the chat log file.
class WriteToChatLogThread(threading.Thread):
	## __init__ - Initializes the attributes of the parseLineFromTwitchThread instance.
	## self.parent    - The pyayaBot_main.Bot instance which spawned this thread.
	## self.thread_id - A unique ID assigned to each thread.
	## self.line      - The line of text to be parsed.
	def __init__(self, parent, message):
		threading.Thread.__init__(self)	
		self.parent    = parent
		self.thread_id = threading.activeCount() + 1
		self.message   = message

		self.start()

	## run - This method calls the pyayaBot_main.LogFairy.writeToChatLog method.
	def run(self):
		self.parent.log.writeToChatLog(self.message)

## End of WriteToChatlogThread class.

## WriteToIRClogThread - A thread which writes an entry to the IRC log file.
class WriteToIRCLogThread(threading.Thread):
	## __init__ - Initializes the attributes of the parseLineFromTwitchThread instance.
	## self.parent    - The pyayaBot_main.Bot instance which spawned this thread.
	## self.thread_id - A unique ID assigned to each thread.
	## self.line      - The line of text to be parsed.
	def __init__(self, parent, message):
		threading.Thread.__init__(self)	
		self.parent    = parent
		self.thread_id = threading.activeCount() + 1
		self.message   = message

		self.start()

	## run - This method calls the pyayaBot_main.LogFairy.writeToIRCLog method.
	def run(self):
		self.parent.log.writeToIRCLog(self.message)

## End of WriteToIRClogThread class.

## WriteToSystemLogThread - A thread which writes an entry to the System log file.
class WriteToSystemLogThread(threading.Thread):
	## __init__ - Initializes the attributes of the parseLineFromTwitchThread instance.
	## self.parent    - The pyayaBot_main.Bot instance which spawned this thread.
	## self.thread_id - A unique ID assigned to each thread.
	## self.line      - The line of text to be parsed.
	def __init__(self, parent, message):
		threading.Thread.__init__(self)
		self.parent    = parent
		self.thread_id = threading.activeCount() + 1
		self.message   = message
		self.start()

	## run - This method calls the pyayaBot_main.LogFairy.writeToSystemLog method.
	def run(self):
		self.parent.log.writeToSystemLog(self.message)

## End of WriteToSystemlogThread class.
