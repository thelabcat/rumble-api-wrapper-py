#!/usr/bin/env python3
"""Cocorum: a Python wrapper for the Rumble.com API

S.D.G."""

import time
import calendar
import requests

from .localvars import *
from .utils import *

class RumbleAPISubObj():
    """Abstract class for a Rumble API object"""
    def __init__(self, json):
        """Pass the JSON block for a single Rumble API subobject"""
        self._json = json

    def __getitem__(self, key):
        """Get a key from the JSON"""
        return self._json[key]

class RumbleUserAction(RumbleAPISubObj):
    """Abstract class for Rumble user actions"""
    def __init__(self, json):
        """Pass the JSON block for a single Rumble user action"""
        super().__init__(json)
        self.__profile_pic = None

    def __eq__(self, other):
        """Is this follower equal to another"""
        #Check if the compared string is our username
        if isinstance(other, str):
            return self.username == other

        #Check if the compared object has a username and if it matches our own
        if hasattr(other, "username"):
            return self.username == other.username

    def __str__(self):
        """Follower as a string"""
        return self.username

    @property
    def username(self):
        """The follower's username"""
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
            #TODO make this timeout assignable
            response = requests.get(self.profile_pic_url, DEFAULT_TIMEOUT)
            if response.status_code != 200:
                raise Exception("Status code " + str(response.status_code))

            self.__profile_pic = response.content

        return self.__profile_pic

class RumbleFollower(RumbleUserAction):
    """Rumble follower"""
    @property
    def followed_on(self):
        """When the follower followed, in seconds since Epoch UTC"""
        return parse_timestamp(self["followed_on"])

class RumbleSubscriber(RumbleUserAction):
    """Rumble subscriber"""
    def __eq__(self, other):
        """Is this subscriber equal to another"""
        #Check if the compared string is our username
        if isinstance(other, str):
            return self.username == other

        #check if the compared number is our amount in cents
        if isinstance(other, (int, float)):
            return self.amount_cents == other

        #Check if the compared object's username matches our own, if it has one
        if hasattr(other, "username"):
            #Check if the compared object's cost amout matches our own, if it has one
            if hasattr(other, "amount_cents"):
                return self.amount_cents == other.amount_cents

            #Other object has no amount_cents attribute
            return self.username == other.username

    @property
    def user(self):
        """AFAIK this is being deprecated, use username instead"""
        return self["user"]

    @property
    def amount_cents(self):
        """The total subscription amount in cents"""
        return self["amount_cents"]

    @property
    def amount_dollars(self):
        """The subscription amount in dollars"""
        return self["amount_dollars"]

    @property
    def subscribed_on(self):
        """When the subscriber subscribed, in seconds since Epoch UTC"""
        return parse_timestamp(self["subscribed_on"])

class RumbleStreamCategory(RumbleAPISubObj):
    """Category of a Rumble stream"""

    @property
    def slug(self):
        """Return the category's slug, AKA it's ID"""
        return self["slug"]

    @property
    def title(self):
        """Return the category's title"""
        return self["title"]

    def __eq__(self, other):
        """Is this category equal to another"""
        #Check if the compared string is our slug or title
        if isinstance(other, str):
            return other in (self.slug, self.title)

        #Check if the compared object has the same slug, if it has one
        if hasattr(other, "slug"):
            return self.slug == other.slug

    def __str__(self):
        """The category in string form"""
        return self.title

class RumbleLivestream():
    """Rumble livestream"""
    def __init__(self, json, api):
        """Pass the JSON block of a single Rumble livestream"""
        self._json = json
        self.api = api
        self.is_disappeared = False #The livestream is in the API listing
        self.__chat = RumbleLiveChat(self)

    def __eq__(self, other):
        """Is this stream equal to another"""
        #Check if the compared string is our stream ID
        if isinstance(other, str):
            return self.stream_id == other #or self.title == other

        #check if the compared number is our chat ID (linked to stream ID)
        if isinstance(other, (int, float)):
            return self.stream_id_b10 == other

        #Check if the compared object has the same stream ID
        if hasattr(other, "stream_id"):
            return self.stream_id == other.stream_id

        #Check if the compared object has the same chat ID
        if hasattr(other, "stream_id_b10"):
            return self.stream_id_b10 == other.stream_id_b10

    def __str__(self):
        """The livestream in string form"""
        return self.stream_id

    def __getitem__(self, key):
        """Return a key from the JSON, refreshing if necessary"""
        #The livestream has not disappeared from the API listing,
        #the key requested is not a value that doesn't change,
        #and it has been api.refresh rate since the last time we refreshed
        if (not self.is_disappeared) and (key not in STATIC_KEYS_STREAM) and (time.time() - self.api.last_refresh_time > self.api.refresh_rate):
            self.api.refresh()

        return self._json[key]

    @property
    def stream_id(self):
        """The livestream ID"""
        return self["id"]

    @property
    def stream_id_b10(self):
        """The livestream chat ID (stream ID in base 10)"""
        return stream_id_36_to_10(self.stream_id)

    @property
    def title(self):
        """The title of the livestream"""
        return self["title"]

    @property
    def created_on(self):
        """When the livestream was created, in seconds since the Epock UTC"""
        return parse_timestamp(self["created_on"])

    @property
    def is_live(self):
        """Is the stream live?"""
        return self["is_live"] and not self.is_disappeared

    @property
    def visibility(self):
        """TODO"""
        return self["visibility"]

    @property
    def categories(self):
        """A list of our categories"""
        data = self["categories"].copy().values()
        return [RumbleStreamCategory(json_block) for json_block in data]

    @property
    def likes(self):
        """Number of likes on the stream"""
        return self["likes"]

    @property
    def dislikes(self):
        """Number of dislikes on the stream"""

    @property
    def like_ratio(self):
        """Ratio of people who liked the stream to people who reacted total"""
        try:
            return self.likes / (self.likes + self.dislikes)

        except ZeroDivisionError:
            return None

    @property
    def watching_now(self):
        """The number of people watching now"""
        return self["watching_now"]

    @property
    def chat(self):
        """The livestream chat"""
        return self.__chat

class RumbleChatMessage(RumbleUserAction):
    """A single message in a Rumble livestream chat"""
    def __eq__(self, other):
        """Is this message equal to another"""
        #Check if the compared string is our message
        if isinstance(other, str):
            return self.text == other

        # #Check if the compared message has the same username and text (not needed)
        # if type(other) == type(self):
        #     return (self.username, self.text) == (other.username, other.text)

        #Check if the compared object has the same text
        if hasattr(other, "text"):
            #Check if the compared object has the same username, if it has one
            if hasattr(other, "username"):
                return (self.username, self.text) == (other.username, other.text)

            return self.text == other.text #the other object had no username attribute

    def __str__(self):
        """Follower as a string"""
        return self.text

    @property
    def text(self):
        """The message text"""
        return self["text"]

    @property
    def created_on(self):
        """When the message was created, in seconds since Epoch UTC"""
        return parse_timestamp(self["created_on"])

    @property
    def badges(self):
        """The user's badges"""
        return tuple(self["badges"].values())

class RumbleRant(RumbleChatMessage):
    """A single rant in a Rumble livestream chat"""
    def __eq__(self, other):
        """Is this category equal to another"""
        #Check if the compared string is our message
        if isinstance(other, str):
            return self.text == other

        # #Check if the compared rant has the same username, amount, and text (unneccesary?)
        # if type(other) == type(self):
        #     return (self.username, self.amount_cents, self.text) == (other.username, other.amount_cents, other.text)

        #Check if the compared object has the same text
        if hasattr(other, "text"):
            #Check if the compared object has the same username, if it has one
            if hasattr(other, "username"):
                #Check if the compared object has the same cost amount, if it has one
                if hasattr(other, "amount_cents"):
                    return (self.username, self.amount_cents, self.text) == (other.username, other.amount_cents, other.text)

                #Other object has no amount_cents attribute
                return (self.username, self.text) == (other.username, other.text)

            #Other object had no username attribute
            return self.text == other.text

    @property
    def expires_on(self):
        """When the rant will expire, in seconds since the Epoch UTC"""
        return self["expires_on"]

    @property
    def amount_cents(self):
        """The total rant amount in cents"""
        return self["amount_cents"]

    @property
    def amount_dollars(self):
        """The rant amount in dollars"""
        return self["amount_dollars"]

class RumbleLiveChat():
    """Reference for chat of a Rumble livestream"""
    def __init__(self, stream):
        """Pass the JSON block of a single Rumble livestream"""
        self.stream = stream
        self.api = stream.api
        self.last_newmessage_time = 0 #Last time we were checked for "new" messages
        self.last_newrant_time = 0 #Last time we were checked for "new" rants

    def __getitem__(self, key):
        """Return a key from the stream's chat JSON"""
        return self.stream["chat"][key]

    @property
    def latest_message(self):
        """The latest chat message"""
        if not self["latest_message"]:
            return None #No-one has chatted on this stream yet
        return RumbleChatMessage(self["latest_message"])

    @property
    def recent_messages(self):
        """Recent chat messages"""
        data = self["recent_messages"].copy()
        return [RumbleChatMessage(json_block) for json_block in data]

    @property
    def new_messages(self):
        """Chat messages that are newer than the last time this was referenced"""
        rem = self.recent_messages.copy()
        rem.sort(key = lambda x: x.created_on) #Sort the messages so the newest ones are last

        if rem[-1].created_on < self.last_newmessage_time: #All messages are older than the last time we checked
            return []

        i = 0
        for i, m in enumerate(rem):
            if m.created_on > self.last_newmessage_time:
                break #i is now the index of the oldest new message

        self.last_newmessage_time = time.time()
        return rem[i:]

    @property
    def latest_rant(self):
        """The latest chat rant"""
        if not self["latest_rant"]:
            return None #No-one has ranted on this stream yet
        return RumbleRant(self["latest_rant"])

    @property
    def recent_rants(self):
        """Recent chat rants"""
        data = self["recent_rants"].copy()
        return [RumbleRant(json_block) for json_block in data]

    @property
    def new_rants(self):
        """Chat rants that are newer than the last time this was referenced"""
        rera = self.recent_rants.copy()
        rera.sort(key = lambda x: x.created_on) #Sort the rants so the newest ones are last

        if rera[-1].created_on < self.last_newrant_time: #All rants are older than the last time we checked
            return []

        i = 0
        for i, r in enumerate(rera):
            if r.created_on > self.last_newrant_time:
                break #i is now the index of the oldest new rant

        self.last_newrant_time = time.time()
        return rera[i:]

class RumbleAPI():
    """Rumble API wrapper"""
    def __init__(self, api_url, refresh_rate = DEFAULT_REFRESH_RATE, request_timeout = DEFAULT_TIMEOUT):
        """Pass the Rumble API URL, and how long to wait before refreshing on new queries"""
        self.refresh_rate = refresh_rate
        self.request_timeout = request_timeout
        self.last_refresh_time = 0
        self.__livestreams = {}
        self._json = {}
        self.api_url = api_url

    @property
    def api_url(self):
        """Our API URL"""
        return self.__api_url

    @api_url.setter
    def api_url(self, url):
        """Set our API URL"""
        self.__api_url = url
        self.refresh()

    def __getitem__(self, key):
        """Return a key from the JSON, refreshing if necessary"""
        if key not in STATIC_KEYS and time.time() - self.last_refresh_time > self.refresh_rate:
            self.refresh()
        return self._json[key]

    def check_refresh(self):
        """Refresh only if we are past the refresh rate"""
        if time.time() - self.last_refresh_time > self.refresh_rate:
            self.refresh()

    def refresh(self):
        """Reload data from the API"""
        self.last_refresh_time = time.time()
        response = requests.get(self.api_url, headers = HEADERS, timeout = self.request_timeout)
        if response.status_code != 200:
            raise Exception("Status code " + str(response.status_code))

        self._json = response.json()

        #Remove livestream references that are no longer listed
        listed_ids = [json["id"] for json in self._json["livestreams"]]
        for stream_id in self.__livestreams.copy():
            if stream_id not in listed_ids:
                self.__livestreams[stream_id].is_disappeared = True
                del self.__livestreams[stream_id]

        #Update livestream references' JSONs in-place
        for json in self._json["livestreams"]:
            try:
                #Update the JSON of the stored livestream
                self.__livestreams[json["id"]]._json = json

            except KeyError: #The livestream has not been stored yet
                self.__livestreams[json["id"]] = RumbleLivestream(json, self)

    @property
    def api_type(self):
        """Type of API URL in use, user or channel"""
        return self["type"]

    @property
    def user_id(self):
        """The user ID"""
        return self["user_id"]

    @property
    def username(self):
        """The username"""
        return self["username"]

    @property
    def channel_id(self):
        """The channel ID, if we are a channel"""
        return self["channel_id"]

    @property
    def channel_name(self):
        """The channel name, if we are a channel"""
        return self["channel_name"]

    @property
    def num_followers(self):
        """The number of followers of this user or channel"""
        return self["followers"]["num_followers"]

    @property
    def num_followers_total(self):
        """The total number of followers of this account across all channels"""
        return self["followers"]["num_followers_total"]

    @property
    def latest_follower(self):
        """The latest follower of this user or channel"""
        if not self["followers"]["latest_follower"]:
            return None #No-one has followed this user or channel yet
        return RumbleFollower(self["followers"]["latest_follower"])

    @property
    def recent_followers(self):
        """A list (technically a shallow generator object) of recent followers"""
        data = self["followers"]["recent_followers"].copy()
        return [RumbleFollower(json_block) for json_block in data]

    @property
    def num_subscribers(self):
        """The number of subscribers of this user or channel"""
        return self["subscribers"]["num_subscribers"]

    @property
    def num_subscribers_total(self):
        """The total number of subscribers of this account across all channels"""
        return self["subscribers"]["num_subscribers_total"]

    @property
    def latest_subscriber(self):
        """The latest subscriber of this user or channel"""
        if not self["subscribers"]["latest_subscriber"]:
            return None #No-one has subscribed to this user or channel yet
        return RumbleSubscriber(self["subscribers"]["latest_subscriber"])

    @property
    def recent_subscribers(self):
        """A list (technically a shallow generator object) of recent subscribers"""
        data = self["subscribers"]["recent_subscribers"].copy()
        return [RumbleSubscriber(json_block) for json_block in data]

    @property
    def livestreams(self):
        """A dictionairy of our livestreams"""
        self.check_refresh()
        return self.__livestreams

    @property
    def latest_livestream(self):
        """Return latest livestream to be created. Use this to get a single running livestream"""
        if not self.livestreams:
            return None #No livestreams are running
        return max(self.livestreams.values(), key = lambda x: x.created_on)
