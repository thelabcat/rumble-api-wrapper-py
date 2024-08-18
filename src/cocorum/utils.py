#!/usr/bin/env python3
"""Rumble API utilities

This submodule provides some utilities for working with the APIs:
- Timestamp parsing
- Converting stream IDs from base 36 to base 10 and vice versa
- Ensuring a stream ID is one of those two bases, converting if necessary

S.D.G."""

import calendar
import time
from .localvars import *

def parse_timestamp(timestamp):
    """Parse a Rumble timestamp to seconds since Epoch"""
    return calendar.timegm(time.strptime(timestamp[:-6], TIMESTAMP_FORMAT)) #Trims off the 6 TODO characters at the end

def stream_id_10_to_36(stream_id_b10):
    """Convert a chat ID to the corresponding stream ID"""
    stream_id_b10 = int(stream_id_b10)
    stream_id = ""
    base_len = len(STREAM_ID_BASE)
    while stream_id_b10:
        stream_id = STREAM_ID_BASE[stream_id_b10 % base_len] + stream_id
        stream_id_b10 //= base_len

    return stream_id

def stream_id_36_to_10(stream_id):
    """Convert a stream ID to the corresponding chat ID"""
    return int(stream_id, len(STREAM_ID_BASE))

def stream_id_36_and_10(stream_id, assume_10 = False):
    """Convert a stream ID to base 36 and 10.
If assume_10 is set to False, will assume a string is base 36 even if it looks like base 10"""
    #It is base 10
    if isinstance(stream_id, int) or \
        (isinstance(stream_id, str) and stream_id.isnumeric() and assume_10):
        return stream_id_10_to_36(stream_id), int(stream_id)

    #It is base 36:
    return stream_id, stream_id_36_to_10(stream_id)

def stream_id_ensure_b36(stream_id, assume_10 = False):
    """No matter wether a stream ID is base 36 or 10, return 36.
If assume_10 is set to False, will assume a string is base 36 even if it looks like base 10"""
    #It is base 10
    if isinstance(stream_id, int) or \
        (isinstance(stream_id, str) and stream_id.isnumeric() and assume_10):
        return stream_id_10_to_36(stream_id)

    #It is base 36:
    return stream_id

def stream_id_ensure_b10(stream_id, assume_10 = False):
    """No matter wether a stream ID is base 36 or 10, return 10.
If assume_10 is set to False, will assume a string is base 36 even if it looks like base 10"""
    #It is base 10
    if isinstance(stream_id, int) or \
        (isinstance(stream_id, str) and stream_id.isnumeric() and assume_10):
        return int(stream_id)

    #It is base 36:
    return stream_id_36_to_10(stream_id)

def badges_to_glyph_string(badges):
    """Convert a list of badges into a string of glyphs"""
    out = ""
    for badge in badges:
        badge = str(badge)
        if badge in BADGES_AS_GLYPHS:
            out += BADGES_AS_GLYPHS[badge]
        else:
            out += "?"
    return out
