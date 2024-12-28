#!/usr/bin/env python3
"""An unofficial Python wrapper for the Rumble.com APIs

A Python wrapper for the Rumble Live Stream API v1.0 (beta), with some quality of life additions, such as:
- Automatic refresh when past the refresh_rate delay when querying any non_static property.
- All timespamps are parsed to seconds since Epoch, UTC timezone.
- Chat has new_messages and new_rants properties that return only messages and rants since the last time they were read.

Note, you are only expected to create a RumbleAPI() and / or ssechat.SSEChat() object, and work with everything through them.

Most attributes that are not added features have the same name as the direct JSON counterparts, with the exception of adding prefixes to some things that have the same name in the JSON as Python builtin functions. For example, thing/id in JSON is thing.thing_id in this Python wrapper.

Example usage:
```
from cocorum import RumbleAPI

api = RumbleAPI(API_URL, refresh_rate = 10)

print(api.username)
print(api.latest_follower)

if api.latest_subscriber:
    print(api.latest_subscriber, "subscribed for $" + str(api.latest_subscriber.amount_dollars))

#RumbleLivestream objects returned by RumbleAPI properties are deep: When queried, they will pull new information via their parent RumbleAPI object.
livestream = api.latest_livestream #None if there is no stream running

if livestream:
    if livestream.visibility != "public":
        print("Stream is not public.")

    #Get messages for one minute
    start_time = time.time()
    while time.time() - start_time < 60 and livestream.is_live:
        for message in livestream.chat.new_messages:
            print(message.username, "said", message)
        time.sleep(0.1)
```
S.D.G."""

import time
import requests

from . import static
from . import utils

class JSONObj():
    """Abstract class for a Rumble API object"""
    def __init__(self, jsondata):
        """Pass the JSON block for a single Rumble API subobject"""
        self._jsondata = jsondata

    def __getitem__(self, key):
        """Get a key from the JSON"""
        return self._jsondata[key]

    @property
    def get(self):
        """Get a key from the JSON with fallback"""
        return self._jsondata.get

class UserAction(JSONObj):
    """Abstract class for Rumble user actions"""
    def __init__(self, jsondata):
        """Pass the JSON block for a single Rumble user action"""
        JSONObj.__init__(self, jsondata)
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
            response = requests.get(self.profile_pic_url, timeout = static.Delays.request_timeout)
            assert response.status_code == 200, "Status code " + str(response.status_code)

            self.__profile_pic = response.content

        return self.__profile_pic

class Follower(UserAction):
    """Rumble follower"""
    @property
    def followed_on(self):
        """When the follower followed, in seconds since Epoch UTC"""
        return utils.parse_timestamp(self["followed_on"])

class Subscriber(UserAction):
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
        return utils.parse_timestamp(self["subscribed_on"])

class StreamCategory(JSONObj):
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

class Livestream():
    """Rumble livestream"""
    def __init__(self, jsondata, api):
        """Pass the JSON block of a single Rumble livestream"""
        self._jsondata = jsondata
        self.api = api
        self.is_disappeared = False #The livestream is in the API listing
        self.__chat = LiveChat(self)

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
        if (not self.is_disappeared) and (key not in static.StaticAPIEndpoints.main) and (time.time() - self.api.last_refresh_time > self.api.refresh_rate):
            self.api.refresh()

        return self._jsondata[key]

    @property
    def stream_id(self):
        """The livestream ID in base 36"""
        return self["id"]

    @property
    def stream_id_b36(self):
        """The livestream ID in base 36"""
        return self.stream_id

    @property
    def stream_id_b10(self):
        """The livestream chat ID (stream ID in base 10)"""
        return utils.base_36_to_10(self.stream_id)

    @property
    def title(self):
        """The title of the livestream"""
        return self["title"]

    @property
    def created_on(self):
        """When the livestream was created, in seconds since the Epock UTC"""
        return utils.parse_timestamp(self["created_on"])

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
        return [StreamCategory(jsondata_block) for jsondata_block in data]

    @property
    def likes(self):
        """Number of likes on the stream"""
        return self["likes"]

    @property
    def dislikes(self):
        """Number of dislikes on the stream"""
        return self["dislikes"]

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

class ChatMessage(UserAction):
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
        return utils.parse_timestamp(self["created_on"])

    @property
    def badges(self):
        """The user's badges"""
        return tuple(self["badges"].values())

class Rant(ChatMessage):
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

class LiveChat():
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
        return ChatMessage(self["latest_message"])

    @property
    def recent_messages(self):
        """Recent chat messages"""
        data = self["recent_messages"].copy()
        return [ChatMessage(jsondata_block) for jsondata_block in data]

    @property
    def new_messages(self):
        """Chat messages that are newer than the last time this was referenced"""
        rem = self.recent_messages.copy()
        rem.sort(key = lambda x: x.created_on) #Sort the messages so the newest ones are last

        #There are no recent messages, or all messages are older than the last time we checked
        if not rem or rem[-1].created_on < self.last_newmessage_time:
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
        return Rant(self["latest_rant"])

    @property
    def recent_rants(self):
        """Recent chat rants"""
        data = self["recent_rants"].copy()
        return [Rant(jsondata_block) for jsondata_block in data]

    @property
    def new_rants(self):
        """Chat rants that are newer than the last time this was referenced"""
        rera = self.recent_rants.copy()
        rera.sort(key = lambda x: x.created_on) #Sort the rants so the newest ones are last

        #There are no recent rants, or all rants are older than the last time we checked
        if not rera or rera[-1].created_on < self.last_newrant_time:
            return []

        i = 0
        for i, r in enumerate(rera):
            if r.created_on > self.last_newrant_time:
                break #i is now the index of the oldest new rant

        self.last_newrant_time = time.time()
        return rera[i:]

class RumbleAPI():
    """Rumble API wrapper"""
    def __init__(self, api_url, refresh_rate = static.Delays.api_refresh_default, request_timeout = static.Delays.request_timeout):
        """Pass the Rumble API URL, and how long to wait before refreshing on new queries"""
        self.refresh_rate = refresh_rate
        self.request_timeout = request_timeout
        self.last_refresh_time = 0
        self.last_newfollower_time = time.time()
        self.last_newsubscriber_time = time.time()
        self.__livestreams = {}
        self._jsondata = {}
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
        if key not in static.StaticAPIEndpoints.main and time.time() - self.last_refresh_time > self.refresh_rate:
            self.refresh()
        return self._jsondata[key]

    def check_refresh(self):
        """Refresh only if we are past the refresh rate"""
        if time.time() - self.last_refresh_time > self.refresh_rate:
            self.refresh()

    def refresh(self):
        """Reload data from the API"""
        self.last_refresh_time = time.time()
        response = requests.get(self.api_url, headers = static.RequestHeaders.user_agent, timeout = self.request_timeout)
        assert response.status_code == 200, "Status code " + str(response.status_code)

        self._jsondata = response.json()

        #Remove livestream references that are no longer listed
        listed_ids = [jsondata["id"] for jsondata in self._jsondata["livestreams"]]
        for stream_id in self.__livestreams.copy():
            if stream_id not in listed_ids:
                self.__livestreams[stream_id].is_disappeared = True
                del self.__livestreams[stream_id]

        #Update livestream references' JSONs in-place
        for jsondata in self._jsondata["livestreams"]:
            try:
                #Update the JSON of the stored livestream
                self.__livestreams[jsondata["id"]]._jsondata = jsondata

            except KeyError: #The livestream has not been stored yet
                self.__livestreams[jsondata["id"]] = Livestream(jsondata, self)

    @property
    def data_timestamp(self):
        """The timestamp on the last data refresh"""
        #Definitely don't ever trigger a refresh on this
        return self._jsondata["now"]

    @property
    def api_type(self):
        """Type of API URL in use, user or channel"""
        return self["type"]

    @property
    def user_id(self):
        """The user ID in base 36"""
        return self["user_id"]

    @property
    def user_id_b36(self):
        """The user ID in base 36"""
        return self.user_id

    @property
    def user_id_b10(self):
        """The user ID in base 10"""
        return utils.base_36_to_10(self.user_id)

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
        return Follower(self["followers"]["latest_follower"])

    @property
    def recent_followers(self):
        """A list of recent followers"""
        data = self["followers"]["recent_followers"].copy()
        return [Follower(jsondata_block) for jsondata_block in data]

    @property
    def new_followers(self):
        """Followers that are newer than the last time this was checked (or RumbleAPI object creation)"""
        recent_followers = self.recent_followers

        nf = [follower for follower in recent_followers if follower.followed_on > self.last_newfollower_time]
        nf.sort(key = lambda x: x.followed_on)

        self.last_newfollower_time = time.time()

        return nf

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
        return Subscriber(self["subscribers"]["latest_subscriber"])

    @property
    def recent_subscribers(self):
        """A list (technically a shallow generator object) of recent subscribers"""
        data = self["subscribers"]["recent_subscribers"].copy()
        return [Subscriber(jsondata_block) for jsondata_block in data]

    @property
    def new_subscribers(self):
        """Subscribers that are newer than the last time this was checked (or RumbleAPI object creation)"""
        recent_subscribers = self.recent_subscribers

        ns = [subscriber for subscriber in recent_subscribers if subscriber.subscribed_on > self.last_newsubscriber_time]
        ns.sort(key = lambda x: x.subscribed_on)

        self.last_newsubscriber_time = time.time()

        return ns

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
