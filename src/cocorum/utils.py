#!/usr/bin/env python3
"""Rumble API utilities

This submodule provides some utilities for working with the APIs
S.D.G."""

import base64
import calendar
import hashlib
import time
import uuid
import bs4
import requests
from . import static

class MD5Ex:
    """MD5 extended hashing utilities"""

    def hash(self, message: str) -> str:
        """Hash a string and return the hexdigest"""
        if isinstance(message, str):
            message = message.encode(static.Misc.text_encoding)
        return hashlib.md5(message).hexdigest()

    def hash_stretch(self, password: str, salt: str, iterations: int = 1024) -> str:
        """Stretch-hash a password with a salt"""
        #Start with the salt and password together
        message = (salt + password).encode(static.Misc.text_encoding)

        #Make one hash of it
        current = self.hash(message)

        #Then keep re-adding the password and re-hashing
        for _ in range(iterations):
            current = self.hash(current + password)

        return current

def parse_timestamp(timestamp):
    """Parse a Rumble timestamp to seconds since Epoch"""
    #Trims off the 6 TODO characters at the end
    return calendar.timegm(time.strptime(timestamp[:-6], static.Misc.timestamp_format))

def stream_id_10_to_36(stream_id_b10):
    """Convert a chat ID to the corresponding stream ID"""
    stream_id_b10 = int(stream_id_b10)
    stream_id = ""
    base_len = len(static.Misc.base36)
    while stream_id_b10:
        stream_id = static.Misc.base36[stream_id_b10 % base_len] + stream_id
        stream_id_b10 //= base_len

    return stream_id

def stream_id_36_to_10(stream_id):
    """Convert a stream ID to the corresponding chat ID"""
    return int(stream_id, len(static.Misc.base36))

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
        if badge in static.Misc.badges_as_glyphs:
            out += static.Misc.badges_as_glyphs[badge]
        else:
            out += "?"
    return out

def calc_password_hashes(password, salts):
    """Hash a password given the salts using custom MD5 implementation"""
    md5 = MD5Ex()
    stretched1 = md5.hash_stretch(password, salts[0], 128)
    stretched2 = md5.hash_stretch(password, salts[2], 128)
    final_hash1 = md5.hash(stretched1 + salts[1])
    return [final_hash1, stretched2, salts[1]]

def generate_request_id():
    """Generate a UUID for API requests"""
    random_uuid = uuid.uuid4().bytes + uuid.uuid4().bytes
    b64_encoded = base64.b64encode(random_uuid).decode(static.Misc.text_encoding)
    return b64_encoded.rstrip('=')[:43]

def get_muted_user_record(session_cookie, username: str = None):
    """Get the record IDs for mutes
    username: Username to find record ID for,
        defaults to returning all record IDs."""

    #The page we are on
    pagenum = 1

    record_ids = {}

    #While there are more pages
    while True:
        #Get the next page of mutes
        r = requests.get(
            static.URI.mutes_page.format(page = pagenum),
            cookies = session_cookie,
            headers = static.RequestHeaders.user_agent,
            timeout = static.Delays.request_timeout,
            )
        assert r.status_code == 200, f"Error: Getting mutes page #{pagenum} failed, {r}"

        #Parse the HTML and search for mute buttons
        soup = bs4.BeautifulSoup(r.text, features="lxml")
        elems = soup.find_all("button", attrs = {"class" : "unmute_action button-small"})

        #We reached the last page
        if not elems:
            break

        #Get the record IDs per username from each button
        for e in elems:
            #We were searching for a specific username and found it
            if username and e.attrs["data-username"] == username:
                return e.attrs["data-record-id"]

            record_ids[e.attrs["data-username"]] = int(e.attrs["data-record-id"])

        #Turn the page
        pagenum +=1

    #Only return record IDs if we weren't searching for a particular one
    if not username:
        return record_ids

def get_channels(session_cookie, username):
    """Get dict of channel slug : {id, title} for a username"""
    #Get the page of channels, does not require login
    r = requests.get(
        static.URI.channels_page.format(username = username),
        cookies = session_cookie,
        headers = static.RequestHeaders.user_agent,
        timeout = static.Delays.request_timeout,
        )
    assert r.status_code == 200, f"Error: Getting channels page failed, {r}"

    #Parse the HTML and search for channel
    soup = bs4.BeautifulSoup(r.text, features="lxml")
    elems = soup.find_all("div", attrs = {"data-type" : "channel"})
    return {e.attrs["data-slug"] : {"id" : int(e.attrs["data-id"]), "title" : e.attrs["data-title"]} for e in elems}
