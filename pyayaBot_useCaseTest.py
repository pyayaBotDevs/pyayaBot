## pyayaBot_useCaseTest.py
## This script deploys an instance of pyayaBot using hard-coded values and is a system-wide test.

import pyayaBot_main, sys

if (len(sys.argv) != 3):
	print "    Syntax error. Usage: pyayaBot_useCaseTest.py channel_name ini|json"
	sys.exit()

## Initialize test variables.
test_connection_config = "./connection_config." + sys.argv[2]
test_channel_config    = "./channel_config_" + sys.argv[1] + "." + sys.argv[2]

## This int will be turned a list of binary values to control lagging.
## INFO Logging    - Add 8
## WARNING Logging - Add 4
## ERROR Logging   - Add 2
## DEBUG Logging   - Add 1
## i.e) 15 -> All logging turned on. (Default Behavior)`
##       6 -> WARNING & ERROR Logging only.
test_bitmask = 14

## Turn the int given into a list of bools.
test_bitlist = list(bin(test_bitmask)[2:].zfill(4))

test_pyaya   = pyayaBot_main.Bot(test_connection_config, test_channel_config, sys.argv[2], test_bitlist)
