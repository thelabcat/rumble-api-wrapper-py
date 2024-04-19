#!/usr/bin/env python3
#Rumble API utilities
#S.D.G.

import calendar
import time
from .localvars import *

def parse_timestamp(timestamp):
    """Parse a Rumble timestamp to seconds since Epoch"""
    return calendar.timegm(time.strptime(timestamp[:-6], TIMESTAMP_FORMAT)) #Trims off the 6 TODO characters at the end
