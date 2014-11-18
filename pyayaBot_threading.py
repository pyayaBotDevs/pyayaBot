## pyayaBot_threading.py
## Author(s): Daniel "Albinohat" Mercado
## This module contains the special thread subclasses used by pyayaBot.

## TODO [ NOT STARTED ], [ IN-PROGRESS ], [ TESTING ] or [ DONE ]
## Looking lonely on the dance floor.

## Standard imports
import threading

## Third-party imports
import pyayaBot_main

## executeCommandThread - A thread which parses through and executes a command.
class executeCommandThread(threading.Thread):
	## __init__ - Initializes the attributes of the parseLineFromTwitchThread instance.
	## self.parent    - The pyayaBot_main.Bot instance which spawned this thread.
	## self.thread_id - A unique ID assigned to each thread.
	## self.command   - The command to execute as a Command object.
	def __init__(self, parent, command):
		threading.Thread.__init__(self)
		self.parent    = parent
		self.thread_id = threading.activeCount() + 1
		self.command   = command
		self.run()
		
	## run - This method calls the parseLineFromTwitch method.
	def run(self):
		self.parent.basic_feature_set.executeCommand(self.command)

## end of executeCommandThread class.	

## parseLineFromTwitchThread - A thread which parses through a line of text from the twitch.tv IRC server.
class parseLineFromTwitchThread(threading.Thread):
	## __init__ - Initializes the attributes of the parseLineFromTwitchThread instance.
	## self.parent    - The pyayaBot_main.Bot instance which spawned this thread.
	## self.thread_id - A unique ID assigned to each thread.
	## self.line      - The line of text to be parsed from the twitch.tv IRC server.
	def __init__(self, parent, line):
		threading.Thread.__init__(self)
		self.parent    = parent
		self.thread_id = threading.activeCount() + 1
		self.line      = line
		self.run()
	
	## run - This method calls the parseLineFromTwitch method.
	def run(self):
		self.parent.parseLineFromTwitch(self.line)

## end of parseLineFromTwitchThread class.	
		
## writeToAdminLogThread - A thread which writes an entry to the Admin log file.
class writeToAdminLogThread(threading.Thread):
	## __init__ - Initializes the attributes of the parseLineFromTwitchThread instance.
	## self.parent    - The pyayaBot_main.Bot instance which spawned this thread.
	## self.thread_id - A unique ID assigned to each thread.
	## self.line      - The line of text to be parsed.
	def __init__(self, parent, message):
		threading.Thread.__init__(self)	
		self.parent    = parent
		self.thread_id = threading.activeCount() + 1
		self.message   = message
		self.run()
		
	def run(self):
		self.parent.log.writeToAdminLog(self.message)
		
## End of writeToAdminlogThread class.
		
## writeToChatLogThread - A thread which writes an entry to the chat log file.
class writeToChatLogThread(threading.Thread):
	## __init__ - Initializes the attributes of the parseLineFromTwitchThread instance.
	## self.parent    - The pyayaBot_main.Bot instance which spawned this thread.
	## self.thread_id - A unique ID assigned to each thread.
	## self.line      - The line of text to be parsed.
	def __init__(self, parent, message):
		threading.Thread.__init__(self)	
		self.parent    = parent
		self.thread_id = threading.activeCount() + 1
		self.message   = message
		self.run()
		
	def run(self):
		self.parent.log.writeToChatLog(self.message)
		
## End of writeToChatlogThread class.

## writeToIRClogThread - A thread which writes an entry to the IRC log file.
class writeToIRCLogThread(threading.Thread):
	## __init__ - Initializes the attributes of the parseLineFromTwitchThread instance.
	## self.parent    - The pyayaBot_main.Bot instance which spawned this thread.
	## self.thread_id - A unique ID assigned to each thread.
	## self.line      - The line of text to be parsed.
	def __init__(self, parent, message):
		threading.Thread.__init__(self)	
		self.parent    = parent
		self.thread_id = threading.activeCount() + 1
		self.message   = message
		self.run()
		
	def run(self):
		self.parent.log.writeToIRCLog(self.message)
		
## End of writeToIRClogThread class.

## writeToSystemLogThread - A thread which writes an entry to the System log file.
class writeToSystemLogThread(threading.Thread):
	## __init__ - Initializes the attributes of the parseLineFromTwitchThread instance.
	## self.parent    - The pyayaBot_main.Bot instance which spawned this thread.
	## self.thread_id - A unique ID assigned to each thread.
	## self.line      - The line of text to be parsed.
	def __init__(self, parent, message):
		threading.Thread.__init__(self)	
		self.parent    = parent
		self.thread_id = threading.activeCount() + 1
		self.message   = message
		self.run()
		
	def run(self):
		self.parent.log.writeToSystemLog(self.message)
		
## End of writeToSystemlogThread class.
