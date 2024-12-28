#!/usr/bin/env python3
"""Internal chat API client

This part of cocorum is not part of the official Rumble Live Stream API, but may provide a more reliable method of ensuring all chat messages are received.
It also can do to-chat interactions, sometimes via Service.PHP.

Example usage:
```
from cocorum import chatapi

#Additionally pass username and password for to-chat interactions
chat = chatapi.ChatAPI(stream_id = STREAM_ID) #Stream ID can be base 10 or 36
chat.clear_mailbox() #Erase messages that were still visible before we connected

#Get messages for one minute
start_time = time.time()
while time.time() - start_time < 60 and (msg := chat.get_message()):
    print(msg.user.username, "said", msg)
```
S.D.G."""

import json #For parsing SSE message data
import time
import requests
import sseclient
from . import JSONObj
from . import UserAction
from .servicephp import ServicePHP
from . import scraping
from . import static
from . import utils

class ChatAPIObj(JSONObj):
    """Object in the internal chat API"""
    def __init__(self, jsondata, chat):
        """Pass the object JSON, and the parent ChatAPI object"""
        JSONObj.__init__(self, jsondata)
        self.chat = chat

class ChatAPIChatter(UserAction, ChatAPIObj):
    """A user or channel in the internal chat API"""
    def __init__(self, jsondata, chat):
        """Pass the object JSON, and the parent ChatAPI object"""
        ChatAPIObj.__init__(self, jsondata, chat)
        UserAction.__init__(self, jsondata)

    @property
    def link(self):
        """The user's subpage of Rumble.com"""
        return self["link"]

class ChatAPIUser(ChatAPIChatter):
    """User in the internal chat API"""
    def __init__(self, jsondata, chat):
        """Pass the object JSON, and the parent ChatAPI object"""
        ChatAPIChatter.__init__(self, jsondata, chat)
        self.previous_channel_ids = [] #List of channels the user has appeared as, including the current one
        self._set_channel_id = None #Channel ID set from message

    def __int__(self):
        """The user as an integer (it's ID in base 10)"""
        return self.user_id_b10

    @property
    def user_id(self):
        """The numeric ID of the user in base 10"""
        return int(self["id"])

    @property
    def user_id_b10(self):
        """The numeric ID of the user in base 10"""
        return self.user_id

    @property
    def user_id_b36(self):
        """The numeric ID of the user in base 36"""
        return utils.base_10_to_36(self.user_id)

    @property
    def channel_id(self):
        """The numeric channel ID that the user is appearing with in base 10"""

        #Try to get our channel ID from our own JSON (may be deprecated)
        try:
            new = int(self["channel_id"])

        #Rely on messages to have assigned our channel ID
        except KeyError:
            new = self._set_channel_id

        if new not in self.previous_channel_ids: #Record the appearance of a new chanel appearance, including None
            self.previous_channel_ids.append(new)
        return new

    @property
    def channel_id_b10(self):
        """The numeric channel ID that the user is appearing with in base 10"""
        return self.channel_id

    @property
    def channel_id_b36(self):
        """The numeric channel ID that the user is appearing with in base 36"""
        if not self.channel_id:
            return
        return utils.base_10_to_36(self.channel_id)

    @property
    def is_follower(self):
        """Is this user following the livestreaming channel?"""
        return self["is_follower"]

    @property
    def color(self):
        """The color of our username (RGB tuple)"""
        return tuple(int(self["color"][i : i + 2], 16) for i in range(0, 6, 2))

    @property
    def badges(self):
        """Badges the user has"""
        try:
            return [self.chat.badges[badge_slug] for badge_slug in self["badges"]]

        #User has no badges
        except KeyError:
            return []

class ChatAPIChannel(ChatAPIChatter):
    """A channel in the SSE chat"""
    def __init__(self, jsondata, chat):
        """Pass the object JSON, and the parent ChatAPI object"""
        super().__init__(jsondata, chat)

        #Find the user who has this channel
        for user in self.chat.users.values():
            if user.channel_id == self.channel_id or self.channel_id in user.previous_channel_ids:
                self.user = user
                break

    @property
    def is_appearing(self):
        """Is the user of this channel still appearing as it?"""
        return self.user.channel_id == self.channel_id #The user channel_id still matches our own

    @property
    def channel_id(self):
        """The ID of this channel in base 10"""
        return int(self["id"])

    @property
    def channel_id_b10(self):
        """The ID of this channel in base 10"""
        return self.channel_id

    @property
    def channel_id_b36(self):
        """The ID of this channel in base 36"""
        return utils.base_10_to_36(self.channel_id)

    @property
    def user_id(self):
        """The numeric ID of the user of this channel"""
        return self.user.user_id

class ChatAPIUserBadge(ChatAPIObj):
    """A badge of a user"""
    def __init__(self, slug, jsondata, chat):
        """Pass the slug, the object JSON, and the parent ChatAPI object"""
        super().__init__(jsondata, chat)
        self.slug = slug #The unique identification for this badge
        self.__icon = None

    def __eq__(self, other):
        """Check if this badge is equal to another"""
        #Check if the string is either our slug or our label in any language
        if isinstance(other, str):
            return other in (self.slug, self.label.values())

        #Check if the compared object has the same slug, if it has one
        if hasattr(other, "slug"):
            return self.slug == other.slug

    def __str__(self):
        """The chat user badge in string form"""
        return self.slug

    @property
    def label(self):
        """A dictionary of lang:label pairs"""
        return self["label"]

    @property
    def icon_url(self):
        """The URL of the badge's icon"""
        return static.URI.rumble_base + self["icons"][static.Misc.badge_icon_size]

    @property
    def icon(self):
        """The badge's icon as a bytestring"""
        if not self.__icon: #We never queried the icon before
            #TODO make the timeout configurable
            response = requests.get(self.icon_url, timeout = static.Delays.request_timeout)
            assert response.status_code == 200, "Status code " + str(response.status_code)

            self.__icon = response.content

        return self.__icon

class ChatAPIMessage(ChatAPIObj):
    """A single chat message in the internal chat API"""
    def __init__(self, jsondata, chat):
        """Pass the object JSON, and the parent ChatAPI object"""
        super().__init__(jsondata, chat)

        #Set the channel ID of our user if we can
        if self.user:
            self.user._set_channel_id = self.channel_id

    def __eq__(self, other):
        """Compare this chat message with another"""
        if isinstance(other, str):
            return self.text == other

        #Check if the other object's text matches our own, if it has such
        if hasattr(other, "text"):
            #Check if the other object's user ID matches our own, if it has one
            if hasattr(other, "user_id"):
                #Check if the other object is a raid notification, if it says
                if hasattr(other, "raid_notification"):
                    return (self.user_id, self.text, self.raid_notification) == (other.user_id, other.text, other.raid_notification)

                return (self.user_id, self.text) == (other.user_id, other.text)

            #Check if the other object's username matches our own, if it has one
            if hasattr(other, "username"):
                #Check if the other object is a raid notification, if it says
                if hasattr(other, "raid_notification"):
                    return (self.user_id, self.text, self.raid_notification) == (other.user_id, other.text, other.raid_notification)

                return (self.user.username, self.text) == (other.username, other.text)

            #No user identifying attributes, but the text does match
            return self.text == other.text

    def __str__(self):
        """The chat message in string form"""
        return self.text

    def __int__(self):
        """The chat message in integer (ID) form"""
        return self.message_id

    @property
    def message_id(self):
        """The unique numerical ID of the chat message in base 10"""
        return int(self["id"])

    @property
    def message_id_b10(self):
        """The unique numerical ID of the chat message in base 10"""
        return self.message_id

    @property
    def message_id_b36(self):
        """The unique numerical ID of the chat message in base 36"""
        return utils.base_10_to_36(self.message_id)

    @property
    def time(self):
        """The time the message was sent on, in seconds since the Epoch UTC"""
        return utils.parse_timestamp(self["time"])

    @property
    def user_id(self):
        """The numerical ID of the user who posted the message in base 10"""
        return int(self["user_id"])

    @property
    def user_id_b10(self):
        """The numeric ID of the user in base 10"""
        return self.user_id

    @property
    def user_id_b36(self):
        """The numeric ID of the user in base 36"""
        return utils.base_10_to_36(self.user_id)

    @property
    def channel_id(self):
        """The numeric ID of the channel who posted the message, if there is one"""
        try:
            #Note: For some reason, channel IDs in messages alone show up as integers in the SSE events
            return int(self["channel_id"])
        except KeyError: #This user is not appearing as a channel and so has no channel ID
            return None

    @property
    def channel_id_b10(self):
        """The ID of the channel who posted the message in base 10"""
        return self.channel_id

    @property
    def channel_id_b36(self):
        """The ID of the channel who posted the message in base 36"""
        if not self.channel_id:
            return
        return utils.base_10_to_36(self.channel_id)

    @property
    def text(self):
        """The text of the message"""
        return self["text"]

    @property
    def user(self):
        """Reference to the user who posted this message"""
        try:
            return self.chat.users[self.user_id]
        except KeyError:
            print(f"ERROR: Message {self.message_id} could not reference user {self.user_id} because chat has no records of them as of yet.")

    @property
    def channel(self):
        """Reference to the channel that posted this message, if there was one"""
        if not self.channel_id:
            return None

        return self.chat.channels[self.channel_id]

    @property
    def is_rant(self):
        """Is this message a rant?"""
        return "rant" in self._jsondata

    @property
    def rant_price_cents(self):
        """The price of the rant, returns 0 if message is not a rant"""
        if not self.is_rant:
            return 0
        return self["rant"]["price_cents"]

    @property
    def rant_duration(self):
        """The duration the rant will show for, returns 0 if message is not a rant"""
        if not self.is_rant:
            return 0
        return self["rant"]["duration"]

    @property
    def rant_expires_on(self):
        """When the rant expires, returns message creation time if message is not a rant"""
        if not self.is_rant:
            return self.time
        return utils.parse_timestamp(self["rant"]["expires_on"])

    @property
    def raid_notification(self):
        """Are we a raid notification? Returns associated JSON data if yes, False if no"""
        if "raid_notification" in self._jsondata:
            return self["raid_notification"]

        return False

class ChatAPI():
    """Access the Rumble internal chat api"""
    def __init__(self, stream_id, username: str = None, password: str = None, session = None):
        """Pass stream ID in base 10 or 36, and optionally login credentials / session token"""
        self.stream_id = utils.ensure_b36(stream_id)

        self.__mailbox = [] #A mailbox if you will
        self.deleted_message_ids = [] #IDs of messages that were deleted, as reported by the client
        self.pinned_message = None #If a message is pinned, it is assigned to this
        self.users = {} #Dictionary of users by user ID
        self.channels = {} #Dictionary of channels by channel ID
        self.badges = {}

        #Generate our URLs
        self.sse_url = static.URI.ChatAPI.sse_stream.format(stream_id_b10 = self.stream_id_b10)
        self.message_api_url = static.URI.ChatAPI.message.format(stream_id_b10 = self.stream_id_b10)

        #Connect to SSE stream
        #Note: We do NOT want this request to have a timeout
        response = requests.get(self.sse_url, stream = True, headers = static.RequestHeaders.sse_api)
        self.client = sseclient.SSEClient(response)
        self.event_generator = self.client.events()
        self.chat_running = True
        self.parse_init_data(self.next_jsondata())

        #If we have session login, use them
        if (username and password) or session:
            self.servicephp = ServicePHP(username, password, session)
            self.scraper = scraping.Scraper(self.servicephp)
        else:
            self.servicephp = None

        #The last time we sent a message
        self.last_send_time = 0

    @property
    def session_cookie(self):
        """The session cookie we are logged in with"""
        if self.servicephp:
            return self.servicephp.session_cookie
        return None

    def send_message(self, text: str, channel_id: int = None):
        """Send a message in chat
    text: The message text
    channel_id: Numeric ID of the channel to use,
        defaults to None
    Returns message ID, ChatAPIUser"""

        assert self.session_cookie, "Not logged in, cannot send message"
        assert len(text) <= static.Message.max_len, "Mesage is too long"
        curtime = time.time()
        assert self.last_send_time + static.Message.send_cooldown <= curtime, "Sending messages too fast"
        assert utils.options_check(self.message_api_url, "POST"), "Rumble denied options request to post message"
        r = requests.post(
            self.message_api_url,
            cookies = self.session_cookie,
            json = {
                "data": {
                    "request_id": utils.generate_request_id(),
                    "message": {
                        "text": text
                    },
                    "rant": None,
                    "channel_id": channel_id
                    }
                },
            # headers = static.RequestHeaders.user_agent,
            timeout = static.Delays.request_timeout,
            )

        if r.status_code != 200:
            print("Error: Sending message failed,", r, r.text)
            return

        return int(r.json()["data"]["id"]), ChatAPIUser(r.json()["data"]["user"], self)

    def command(self, command_message: str):
        """Send a native chat command, returns response JSON"""
        assert command_message.startswith(static.Message.command_prefix), "Not a command message"
        r = requests.post(
            static.URI.ChatAPI.command,
            data = {
                "video_id" : self.stream_id_b10,
                "message" : command_message,
                },
            cookies = self.session_cookie,
            headers = static.RequestHeaders.user_agent,
            timeout = static.Delays.request_timeout,
            )
        assert r.status_code == 200, f"Command failed: {r}\n{r.text}"
        return r.json()

    def delete_message(self, message):
        """Delete a message in chat
    message: Object which when converted to integer is the target message ID"""

        assert self.session_cookie, "Not logged in, cannot delete message"
        assert utils.options_check(self.message_api_url + f"/{int(message)}", "DELETE"), "Rumble denied options request to delete message"

        r = requests.delete(
            self.message_api_url + f"/{int(message)}",
            cookies = self.session_cookie,
            # headers = static.RequestHeaders.user_agent,
            timeout = static.Delays.request_timeout,
            )

        if r.status_code != 200:
            print("Error: Deleting message failed,", r, r.content.decode(static.Misc.text_encoding))
            return False

        return True

    def pin_message(self, message):
        """Pin a message"""
        assert self.session_cookie, "Not logged in, cannot pin message"
        return self.servicephp.chat_pin(self.stream_id_b10, message)

    def unpin_message(self, message = None):
        """Unpin the pinned message"""
        assert self.session_cookie, "Not logged in, cannot unpin message"
        if not message:
            message = self.pinned_message
        assert message, "No known pinned message and ID not provided"
        return self.servicephp.chat_pin(self.stream_id_b10, message, unpin = True)

    def mute_user(self, user, duration: int = None, total: bool = False):
        """Mute a user
        user: Username to mute
        duration: How long to mute the user in seconds.
            Defaults to infinite.
        total: Wether or not they are muted across all videos.
            Defaults to False, just this video."""
        assert self.session_cookie, "Not logged in, cannot mute user"
        return self.servicephp.mute_user(
            username = str(user),
            is_channel = False,
            video = self.stream_id_b10,
            duration = duration,
            total = total
            )

    def unmute_user(self, user):
        """Unmute a user"""
        assert self.session_cookie, "Not logged in, cannot unmute user"
        record_id = self.scraper.get_muted_user_record(str(user))
        assert record_id, "User was not in muted records"
        return self.servicephp.unmute_user(record_id)

    def next_jsondata(self):
        """Wait for the next event from the SSE and parse the JSON"""
        if not self.chat_running: #Do not try to query a new event if chat is closed
            print("Chat closed, cannot retrieve new JSON data.")
            return

        try:
            event = next(self.event_generator, None)
        except requests.exceptions.ReadTimeout:
            event = None

        if not event:
            self.chat_running = False #Chat has been closed
            print("Chat has closed.")
            return
        if not event.data: #Blank SSE event
            print("Blank SSE event:>", event, "<:")
            #Self recursion should work so long as we don't get dozens of blank events in a row
            return self.next_jsondata()

        return json.loads(event.data)

    def parse_init_data(self, jsondata):
        """Extract initial chat data from the SSE init event JSON"""
        if jsondata["type"] != "init":
            print(jsondata)
            raise ValueError("That is not init json")

        #Parse pre-connection users, channels, then messages
        self.update_users(jsondata)
        self.update_channels(jsondata)
        self.update_mailbox(jsondata)

        #Load the chat badges
        self.load_badges(jsondata)

        self.rants_enabled = jsondata["data"]["config"]["rants"]["enable"]
        #subscription TODO
        #rant levels TODO
        self.message_length_max = jsondata["data"]["config"]["message_length_max"]

    def update_mailbox(self, jsondata):
        """Parse chat messages from an SSE data JSON"""
        #Add new messages
        self.__mailbox += [ChatAPIMessage(message_json, self) for message_json in jsondata["data"]["messages"] if int(message_json["id"]) not in self.__mailbox]

    def clear_mailbox(self):
        """Delete anything in the mailbox"""
        self.__mailbox = []

    def clear_deleted_message_ids(self):
        """Clear and return the list of deleted message IDs"""
        del_m = self.deleted_message_ids.copy()
        self.deleted_message_ids = []
        return del_m

    def update_users(self, jsondata):
        """Update our dictionary of users from an SSE data JSON"""
        for user_json in jsondata["data"]["users"]:
            try:
                self.users[int(user_json["id"])]._jsondata = user_json #Update an existing user's JSON
            except KeyError: #User is new
                self.users[int(user_json["id"])] = ChatAPIUser(user_json, self)

    def update_channels(self, jsondata):
        """Update our dictionary of channels from an SSE data JSON"""
        for channel_json in jsondata["data"]["channels"]:
            try:
                self.channels[int(channel_json["id"])]._jsondata = channel_json #Update an existing channel's JSON
            except KeyError: #Channel is new
                self.channels.update({int(channel_json["id"]) : ChatAPIChannel(channel_json, self)})

    def load_badges(self, jsondata):
        """Create our dictionary of badges given a dictionary of badges"""
        self.badges = {badge_slug : ChatAPIUserBadge(badge_slug, jsondata["data"]["config"]["badges"][badge_slug], self) for badge_slug in jsondata["data"]["config"]["badges"].keys()}

    @property
    def stream_id_b10(self):
        """The chat ID in use"""
        return utils.base_36_to_10(self.stream_id)

    def get_message(self):
        """Return the next chat message (parsing any additional data), waits for it to come in, returns None if chat closed"""
        #We don't already have messages
        while not self.__mailbox:
            jsondata = self.next_jsondata()

            #The chat has closed
            if not jsondata:
                return

            #Messages were deleted
            if jsondata["type"] in ("delete_messages", "delete_non_rant_messages"):
                self.deleted_message_ids += jsondata["data"]["message_ids"]

            #Re-initialize (could contain new messages)
            elif jsondata["type"] == "init":
                self.parse_init_data(jsondata)

            #Pinned message
            elif jsondata["type"] == "pin_message":
                self.pinned_message = ChatAPIMessage(jsondata["data"]["message"], self)

            #New messages
            elif jsondata["type"] == "messages":
                #Parse users, channels, then messages
                self.update_users(jsondata)
                self.update_channels(jsondata)
                self.update_mailbox(jsondata)

            #Unimplemented event type
            else:
                print("API sent an unimplemented SSE event type")
                print(jsondata)

        return self.__mailbox.pop(0) #Return the first message in the mailbox, and then remove it from there
