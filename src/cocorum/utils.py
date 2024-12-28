#!/usr/bin/env python3
"""Rumble API utilities

This submodule provides some utilities for working with the APIs
S.D.G."""

import base64
import calendar
import hashlib
import time
import uuid
import requests
from . import static

class MD5Ex:
    """MD5 extended hashing utilities"""

    @staticmethod
    def hash(message: str) -> str:
        """Hash a string and return the hexdigest string"""
        #Actually, we can except bytes, but if we got string, encode the string
        if isinstance(message, str):
            message = message.encode(static.Misc.text_encoding)

        return hashlib.md5(message).hexdigest()

    @staticmethod
    def hash_stretch(password: str, salt: str, iterations: int = 1024) -> str:
        """Stretch-hash a password with a salt"""
        #Start with the salt and password together
        message = (salt + password).encode(static.Misc.text_encoding)

        #Make one hash of it
        current = MD5Ex.hash(message)

        #Then keep re-adding the password and re-hashing
        for _ in range(iterations):
            current = MD5Ex.hash(current + password)

        return current

def parse_timestamp(timestamp: str) -> float:
    """Parse a Rumble timestamp to seconds since Epoch"""
    #Trims off the 6 TODO characters at the end
    return calendar.timegm(time.strptime(timestamp[:-6], static.Misc.timestamp_format))

def form_timestamp(seconds: float, suffix = "+00:00") -> str:
    """Form a Rumble timestamp from seconds since Epoch"""
    return time.strftime(static.Misc.timestamp_format, time.gmtime(seconds)) + suffix

def base_10_to_36(b10) -> str:
    """Convert a base 10 number to base 36"""
    b10 = int(b10)
    b36 = ""
    base_len = len(static.Misc.base36)
    while b10:
        b36 = static.Misc.base36[b10 % base_len] + b36
        b10 //= base_len

    return b36

def base_36_to_10(b36) -> int:
    """Convert a base 36 number to base 10"""
    return int(str(b36), 36)

def ensure_b36(num, assume_10 = False) -> str:
    """No matter wether a number is base 36 or 10, return 36.
If assume_10 is set to False, will assume a string is base 36 even if it looks like base 10"""
    #It is base 10
    if isinstance(num, int) or hasattr(num, "__int__"):
        return base_10_to_36(int(num))

    #It is a string or has a string conversion attribute
    if isinstance(num, str) or hasattr(num, "__str__"):
        num = str(num)

        #The string number is in base 10
        if num.isnumeric() and assume_10:
            return base_10_to_36(num)

    #It is base 36:
    return num

def ensure_b10(num, assume_10 = False) -> int:
    """No matter wether a number is base 36 or 10, return 10.
If assume_10 is set to False, will assume a string is base 36 even if it looks like base 10"""
    #It is base 10 or has an integer conversion method
    if isinstance(num, int) or hasattr(num, "__int__"):
        return int(num)

    #It is a string or has a string conversion attribute
    if isinstance(num, str) or hasattr(num, "__str__"):
        num = str(num)

        #The string number is in base 10
        if num.isnumeric() and assume_10:
            return base_10_to_36(num), int(num)

    #It is base 36:
    return base_36_to_10(num)

def base_36_and_10(num, assume_10 = False):
    """Take a base 36 or base 10 number, and return both base 36 and 10.
If assume_10 is set to False, will assume a string is base 36 even if it looks like base 10"""
    return ensure_b36(num, assume_10), ensure_b10(num, assume_10)

def badges_to_glyph_string(badges) -> str:
    """Convert a list of badges into a string of glyphs"""
    out = ""
    for badge in badges:
        badge = str(badge)
        if badge in static.Misc.badges_as_glyphs:
            out += static.Misc.badges_as_glyphs[badge]
        else:
            out += "?"
    return out

def calc_password_hashes(password: str, salts):
    """Hash a password given the salts using custom MD5 extension"""
    #Stretch-hash the password with the first salt
    stretched1 = MD5Ex.hash_stretch(password, salts[0], 128)

    #Add the second salt to that result, and hash one more time
    final_hash1 = MD5Ex.hash(stretched1 + salts[1])

    #Stretch-hash the password with the third salt
    stretched2 = MD5Ex.hash_stretch(password, salts[2], 128)

    return final_hash1, stretched2, salts[1]

def generate_request_id() -> str:
    """Generate a UUID for API requests"""
    random_uuid = uuid.uuid4().bytes + uuid.uuid4().bytes
    b64_encoded = base64.b64encode(random_uuid).decode(static.Misc.text_encoding)
    return b64_encoded.rstrip('=')[:43]

def test_session_cookie(session_cookie: dict) -> bool:
    """Test if a session cookie dict is valid"""
    r = requests.get(static.URI.login_test,
            cookies = session_cookie,
            headers = static.RequestHeaders.user_agent,
            timeout = static.Delays.request_timeout,
        )

    assert r.status_code == 200, f"Testing session token failed: {r}"

    title = r.text.split("<title>")[1].split("</title>")[0]

    #If the session token is invalid, it won't log us in and "Login" will still be shown
    return "Login" not in title

def options_check(url: str, method: str, origin = static.URI.rumble_base, cookies: dict = {}, params: dict = {}) -> bool:
    """Check of we are allowed to do method on url via an options request"""
    r = requests.options(
        url,
        headers = {
            'Access-Control-Request-Method' : method.upper(),
            'Access-Control-Request-Headers' : 'content-type',
            'Origin' : origin,
            },
        cookies = cookies,
        params = params,
        timeout = static.Delays.request_timeout,
        )
    return r.status_code == 200
