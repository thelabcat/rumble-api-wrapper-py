#!/usr/bin/env python3
"""Service.PHP interactions

Control Rumble via Service.PHP
S.D.G."""

import requests
import bs4
from . import static
from . import utils
#from .chatapi import ChatAPIUserBadge as UserBadge
from . import APISubObj

class UserBadge(APISubObj):
    """A badge of a user"""
    def __init__(self, slug, jsondata):
        """Pass the slug, and the object JSON"""
        super().__init__(jsondata)
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

class Comment(APISubObj):
    """A comment on a video as returned by a successful attempt to make it"""
    def __init__(self, jsondata):
        """Pass the JSON block for a single comment"""
        super().__init__(jsondata)

        #Badges of the user who commented
        self.user_badges = {slug : UserBadge(slug, data) for slug, data in self["comment_user_badges"].items()}

    @property
    def comment_id(self):
        """The numeric ID of the comment"""
        return int(self["comment_id"])

    @property
    def text(self):
        """The text of the comment"""
        return self["comment_text"]

    @property
    def user_display(self):
        """The display name of the user who commented"""
        return self["comment_user_display"]

    @property
    def tree_size(self):
        """TODO"""
        return self["comment_tree_size"]

class ContentVotes(APISubObj):
    """Votes made on content"""
    def __int__(self):
        """The integer form of the content votes"""
        return self.score

    def __str__(self):
        """The string form of the content votes"""
        return self.score_formatted

    @property
    def num_votes_up(self):
        """Upvotes on the content"""
        return self._jsondata.get("num_votes_up", 0)

    @property
    def num_votes_down(self):
        """Downvotes on the content"""
        return self._jsondata.get("num_votes_down", 0)

    @property
    def score(self):
        """Summed score of the content"""
        return self["score"]

    @property
    def votes(self):
        """The total number of votes on the content"""
        if not self["votes"]:
            return 0
        return self["votes"]

    @property
    def num_votes_up_formatted(self):
        """The upvotes on the content, formatted into a string"""
        return self._jsondata.get("num_votes_up_formatted", "0")

    @property
    def num_votes_down_formatted(self):
        """The downvotes on the content, formatted into a string"""
        return self._jsondata.get("num_votes_down_formatted", "0")

    @property
    def score_formatted(self):
        """The total votes on the content, formatted into a string"""
        return self._jsondata.get("score_formatted", "0")

    @property
    def content_type(self):
        """The type of content being voted on"""
        return self["content_type"]

    @property
    def content_id(self):
        """The numerical ID of the content being voted on"""
        return self["content_id"]

class ServicePHP:
    """Interact with Rumble's service.php API"""
    def __init__(self, username: str = None, password: str = None, session = None):
        """Pass the username and password or a session token (accepts cookie dict or base string)"""
        #Session is the token directly
        if isinstance(session, str):
            self.session_cookie = {static.Misc.session_token_key, session}
        #Session is a cookie dict
        elif isinstance(session, dict):
            assert session.get(static.Misc.session_token_key), f"Session cookie dict must have '{static.Misc.session_token_key}' as key."
            self.session_cookie = session
        #Session was passed but it is not anything we can use
        elif session is not None:
            raise ValueError(f"Session must be a token str or cookie dict, got {type(session)}")
        #Session was not passed, but credentials were
        elif username and password:
            self.session_cookie = self.login(username, password)
        #Neither session nor credentials were passed:
        else:
            raise ValueError("Must pass either userame and password, or a session token")

        assert utils.test_session_cookie(self.session_cookie), "Session cookie is invalid."

    def sphp_request(self, service_name: str, data: dict = {}, additional_params: dict = {}, logged_in = True):
        """Make a POST request to Service.PHP with common settings
        service_name: The name parameter of the specific PHP service
        data: Form data
        additional_params: Any additional query string parameters
        logged_in: The request should use the session cookie"""
        params = {"name" : service_name}
        params.update(additional_params)
        r = requests.post(
                static.URI.servicephp,
                params = params,
                data = data,
                headers = static.RequestHeaders.user_agent,
                cookies = self.session_cookie if logged_in else None,
                timeout = static.Delays.request_timeout,
                )
        assert r.status_code == 200, f"Service.PHP request for {service_name} failed: {r}\n{r.text}"
        #If the request json has a data -> success value, make sure it is True
        assert r.json().get("data", {}).get("success", True), f"Service.PHP request for {service_name} failed: \n{r.text}"
        return r

    def login(self, username, password):
        """Obtain a session cookie from username and password"""
        #Get salts
        r = self.sphp_request(
                "user.get_salts",
                data = {"username": username},
                logged_in = False,
                )
        salts = r.json()["data"]["salts"]

        #Get session token
        r = self.sphp_request(
                "user.login",
                data = {
                    "username": username,

                    #Hash the password using the salts
                    "password_hashes": ",".join(utils.calc_password_hashes(password, salts)),
                    },
                logged_in = False,
                )
        session_token = r.json()["data"]["session"]
        assert session_token, f"Login failed: No token returned\n{r.json()}"

        return {static.Misc.session_token_key: session_token}

    def chat_pin(self, stream_id, message, unpin: bool = False):
        """Pin or unpin a message in a chat
        stream_id: ID of the stream in base 10 or 36
        message: int(this) must return a chat message ID
        unpin: If true, unpins a message instead"""
        self.sphp_request(
            f"chat.message.{"un" * unpin}pin",
            data = {
                "video_id": utils.ensure_b10(stream_id),
                "message_id": int(message),
                },
            )

    def mute_user(self, username: str, is_channel: bool = False, video: int = None, duration: int = None, total: bool = False):
        """Mute a user or channel by name"""
        self.sphp_request(
            "moderation.mute",
            data = {
                "user_to_mute": username,
                "entity_type": ("user", "channel")[is_channel],
                "video": video,
                "duration": duration,
                "type": ("video", "total")[total],
                },
            )

    def unmute_user(self, record_id: int):
        """Unmute a user by record ID"""
        self.sphp_request(
            "moderation.unmute",
            data = {
                "record_id" : record_id,
                }
            )

    def comment_add(self, video_id: int, comment: str, reply_id: int = 0):
        """Post a comment on a video
        video_id: The numeric ID of a video / stream
        comment: What to say
        reply_id: The ID of the comment to reply to
            Defaults to zero (don't reply to anybody)"""
        r = self.sphp_request(
                "comment.add",
                data = {
                    "video": video_id,
                    "reply_id": reply_id,
                    "comment": comment,
                    "target": "comment-create-1",
                    },
                )
        return Comment(r.json()["data"])

    def comment_pin(self, comment_id: int, unpin: bool = False):
        """Pin or unpin a comment by ID
        comment_id: Integer comment ID
        unpin: If true, unpins instead of pinning comment"""
        self.sphp_request(
            f"comment.{"un" * unpin}pin",
            data = {"comment_id": comment_id},
            )

    def comment_delete(self, comment_id: int):
        """Delete a comment by ID"""
        self.sphp_request(
            "comment.delete",
            data = {"comment_id": comment_id},
            )

    def comment_restore(self, comment_id: int):
        """Restore a deleted comment by ID"""
        r = self.sphp_request(
            "comment.restore",
            data = {"comment_id": comment_id},
            )
        return Comment(r.json()["data"])

    def rumbles(self, vote: int, item_id, item_type: int):
        """Post a like or dislike
        vote: -1, 0, or 1
        item_id: The numeric ID of whatever we are liking or disliking
        item_type: 1 for video, 2 for comment"""
        r = self.sphp_request(
            "user.rumbles",
            data = {
                "type" : item_type,
                "id" : utils.ensure_b10(item_id),
                "vote" : vote,
                },
            )
        return ContentVotes(r.json()["data"])

    def get_video_url(self, video_id):
        """Get the URL of a Rumble video from Service.PHP's media.share"""
        r = self.sphp_request(
            "media.share",
            additional_params = {
                "video_id" : utils.ensure_b36(video_id),
                "start" : 0,
                },
            )
        soup = bs4.BeautifulSoup(r.json()["html"], features = "html.parser")
        elem = soup.find("div", attrs = {"class" : "fb-share-button share-fb"})
        return elem.attrs["data-url"]
