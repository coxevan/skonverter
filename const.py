"""
File contains constant values for the Skonverter tool.
"""

VERSION = 0.5

BONE_DELTA = 2 # The amount of distance each bone should be moved to determine weighting.
FAILURE_THRESHOLD = 0 # How many bones can fail before user is prompted with warning

# Slows down the processes a good bit, but displays some useful information in regards to actual weighting without 
# having to save out the files and parse. Lots of printing. Probably needs to be handled better/spit out easier to read info, but for
# the purposes of the tool, it works as it is now.
DEBUG = False

FILE_PREFERENCE = True # We prefer to use the file passed in if both data and filepath are passed in during initialzation of the script.

# Should the weighting be normalized? Really, this shouldn't be ever changed, but if the situation arises, this is here.
NORMALIZE = True
