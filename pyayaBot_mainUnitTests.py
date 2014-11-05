## pyayaBot_mainUnitTests.py

import pyayaBot_main, sys

## Initialize test variables.
test_config  = "./config_albinohat.ini"

## This into will be turned a list of binary values to control lagging.
## INFO Logging    - Add 8
## WARNING Logging - Add 4
## ERROR Logging   - Add 2
## DEBUG Logging   - Add 1
## i.e) 15 -> All logging turned on. (Default behavior)
##       7 -> WARNING & ERROR Logging only.

test_int     = 7

## Turn the int given into a list of bools.
test_bitmask = list(bin(test_int)[2:].zfill(4))



test_pyaya = pyayaBot_main.Bot(test_config, test_bitmask)
