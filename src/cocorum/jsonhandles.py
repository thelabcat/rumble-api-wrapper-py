#!/usr/bin/env python3
"""JSON handles

Abstract classes for handling JSON data.
S.D.G."""

import requests
from . import static

class JSONObj():
    """Abstract class for handling a JSON data block as an object"""
    def __init__(self, jsondata):
        """Abstract class for handling a JSON data block as an object.

    Args:
        jsondata (dict): The JSON data block of an API object.
        """

        self._jsondata = jsondata

    def __getitem__(self, key):
        """Get a key from the JSON"""
        return self._jsondata[key]

    @property
    def get(self):
        """Get a key from the JSON with fallback"""
        return self._jsondata.get

class JSONUserAction(JSONObj):
    """Abstract class for Rumble JSON user actions"""
    def __init__(self, jsondata):
        """Abstract class for Rumble JSON user actions.

    Args:
        jsondata (dict): The JSON block for a single Rumble user action.
        """

        JSONObj.__init__(self, jsondata)
        self.__profile_pic = None

    def __eq__(self, other):
        """Is this user equal to another?

    Args:
        other (str, JSONUserAction): Object to compare to.

    Returns:
        Comparison (bool, None): Did it fit the criteria?
        """

        #Check if the compared string is our username, or base 36 user ID if we have one
        if isinstance(other, str):
            #We have a base 36 user ID
            if hasattr(self, "user_id_b36"):
                return other in (self.username, self.user_id_b36)

            #We only have our username
            return self.username == other

        #Check if the compared object has a username and if it matches our own
        if hasattr(other, "username"):
            return self.username == other.username

        #Check if the compared object has a user ID in base 36 and if it matches our own, if we have one
        if hasattr(self, "user_id_b36") and hasattr(other, "user_id_b36"):
            return self.user_id_b36 == other.user_id_b36

    def __str__(self):
        """Follower as a string"""
        return self.username

    @property
    def username(self):
        """The username"""
        return self["username"]

    @property
    def profile_pic_url(self):
        """The user's profile picture URL"""
        return self["profile_pic_url"]

    @property
    def profile_pic(self):
        """The user's profile picture as a bytes string"""
        if not self.profile_pic_url: #The profile picture is blank
            return b''

        if not self.__profile_pic: #We never queried the profile pic before
            response = requests.get(self.profile_pic_url, timeout = static.Delays.request_timeout)
            assert response.status_code == 200, "Status code " + str(response.status_code)

            self.__profile_pic = response.content

        return self.__profile_pic
