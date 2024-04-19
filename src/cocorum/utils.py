#!/usr/bin/env python3
#Rumble API utilities
#S.D.G.

import calendar
import time
from .localvars import *

def parse_timestamp(timestamp):
    """Parse a Rumble timestamp to seconds since Epoch"""
    return calendar.timegm(time.strptime(timestamp[:-6], TIMESTAMP_FORMAT)) #Trims off the 6 TODO characters at the end

def id_chat_to_stream(chat_id):
    """Convert a chat ID to the corresponding stream ID"""
    stream_id = ""
    base_len = len(STREAM_ID_BASE)
    while chat_id:
        stream_id = STREAM_ID_BASE[chat_id % base_len] + stream_id
        chat_id //= base_len

    return stream_id

def id_stream_to_chat(stream_id):
    """Convert a stream ID to the corresponding chat ID"""
    return int(stream_id, len(STREAM_ID_BASE))
