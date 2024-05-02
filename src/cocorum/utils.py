#!/usr/bin/env python3
"""Rumble API utilities

S.D.G."""

import calendar
import time
from .localvars import *

def parse_timestamp(timestamp):
    """Parse a Rumble timestamp to seconds since Epoch"""
    return calendar.timegm(time.strptime(timestamp[:-6], TIMESTAMP_FORMAT)) #Trims off the 6 TODO characters at the end

def stream_id_10_to_36(stream_id_b10):
    """Convert a chat ID to the corresponding stream ID"""
    stream_id = ""
    base_len = len(STREAM_ID_BASE)
    while stream_id_b10:
        stream_id = STREAM_ID_BASE[stream_id_b10 % base_len] + stream_id
        stream_id_b10 //= base_len

    return stream_id

def stream_id_36_to_10(stream_id):
    """Convert a stream ID to the corresponding chat ID"""
    return int(stream_id, len(STREAM_ID_BASE))

def stream_id_36_and_10(stream_id):
    """Figure out if a stream ID is base 36 or 10, and return both forms in that order"""
    #It is base 10
    if isinstance(stream_id, int) or (isinstance(stream_id, str) and stream_id.isnumeric()):
        return stream_id_10_to_36(stream_id), int(stream_id)

    #It is base 36:
    return stream_id, stream_id_36_to_10(stream_id)

def stream_id_ensure_b36(stream_id):
    """No matter wether a stream ID is base 36 or 10, return 36"""
    #It is base 10
    if isinstance(stream_id, int) or (isinstance(stream_id, str) and stream_id.isnumeric()):
        return stream_id_10_to_36(stream_id)

    #It is base 36:
    return stream_id

def stream_id_ensure_b10(stream_id):
    """No matter wether a stream ID is base 36 or 10, return 10"""
    #It is base 10
    if isinstance(stream_id, int) or (isinstance(stream_id, str) and stream_id.isnumeric()):
        return int(stream_id)

    #It is base 36:
    return stream_id_36_to_10(stream_id)
