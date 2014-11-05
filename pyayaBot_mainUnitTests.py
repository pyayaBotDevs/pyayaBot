## pyayaBot_mainUnitTests.py

import pyayaBot_main, sys

test_config  = "./config_albinohat.ini"
test_int     = 7
test_bitmask = list(bin(test_int)[2:].zfill(4))

print "test_bitmask = " + str(test_bitmask)

sys.exit()
test_pyaya = pyayaBot_main.Bot(test_config, test_bitmask)