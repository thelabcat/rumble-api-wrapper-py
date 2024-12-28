#!/usr/bin/env python3
"""Service.PHP interactions

Control Rumble via Service.PHP
S.D.G."""

import requests
import bs4
from . import scraping
from . import static
from . import utils
from . import JSONObj

class APIUserBadge(JSONObj):
    """A badge of a user as returned by the API"""
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
            response = requests.get(self.icon_url, timeout = static.Delays.request_timeout)
            assert response.status_code == 200, "Status code " + str(response.status_code)

            self.__icon = response.content

        return self.__icon

class APIComment(JSONObj):
    """A comment on a video as returned by a successful attempt to make it"""
    def __init__(self, jsondata):
        """Pass the JSON block for a single comment"""
        super().__init__(jsondata)

        #Badges of the user who commented if we have them
        if self.get("comment_user_badges"):
            self.user_badges = {slug : APIUserBadge(slug, data) for slug, data in self["comment_user_badges"].items()}

    def __int__(self):
        """The comment in integer form (its ID)"""
        return self.comment_id

    def __str__(self):
        """The comment as a string (its text)"""
        return self.text

    def __eq__(self, other):
        """Determine if this comment is equal to another"""
        #Check for direct matches first
        if isinstance(other, int):
            return self.comment_id_b10 == other
        if isinstance(other, str):
            return str(self) == other

        #Check for object attributes to match to
        if hasattr(other, "comment_id"):
            return self.comment_id_b10 == utils.ensure_b10(other.comment_id)

        #Check conversion to integer last
        if hasattr(other, "__int__"):
            return self.comment_id_b10 == int(other)

    @property
    def comment_id(self):
        """The numeric ID of the comment"""
        return int(self["comment_id"])

    @property
    def comment_id_b10(self):
        """The base 10 ID of the comment"""
        return self.comment_id

    @property
    def comment_id_b36(self):
        """The base 36 ID of the comment"""
        return utils.base_10_to_36(self.comment_id)

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

class APIContentVotes(JSONObj):
    """Votes made on content"""
    def __int__(self):
        """The integer form of the content votes"""
        return self.score

    def __str__(self):
        """The string form of the content votes"""
        return self.score_formatted

    def __eq__(self, other):
        """Determine if this content votes is equal to another"""
        #Check for direct matches first
        if isinstance(other, int):
            return self.score == other
        if isinstance(other, str):
            return other in (str(self.score), self.score_formatted)

        #Check for object attributes to match to
        if hasattr(other, "score"):
            #if hasattr(other, "content_id") and hasattr(other, "content_type"):
            #    return self.score, self.content_id, self.content_type == other.score, other.content_id, other.content_type
            return self.score == other.score

        #Check conversion to integer last
        if hasattr(other, "__int__"):
            return self.score == int(other)

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

class APIUser(JSONObj):
    """User data as returned by the API"""
    def __init__(self, jsondata):
        """Pass the JSON data of a user"""
        super().__init__(jsondata)

        #Our profile picture data
        self.__picture = None

    def __int__(self):
        """The user as an integer (it's ID in base 10)"""
        return self.user_id_b10

    def __eq__(self, other):
        """Determine if this user is equal to another"""
        #Check for direct matches first
        if isinstance(other, int):
            return self.user_id_b10 == other
        if isinstance(other, str):
            return str(other) in (self.user_id_b36, self.username)

        #Check for object attributes to match to
        if hasattr(other, "user_id"):
            return self.user_id_b10 == utils.ensure_b10(other.user_id)

        #Check conversion to integer last, in case another ID or something happens to match
        if hasattr(other, "__int__"):
            return self.user_id_b10 == int(other)

    @property
    def user_id(self):
        """The numeric ID of the user in base 10"""
        return self["id"]

    @property
    def user_id_b10(self):
        """The numeric ID of the user in base 10"""
        return self.user_id

    @property
    def user_id_b36(self):
        """The numeric ID of the user in base 36"""
        return utils.base_10_to_36(self.user_id)

    @property
    def username(self):
        """The username of the user"""
        return self["username"]

    @property
    def picture_url(self):
        """The URL of the user's profile picture"""
        return self["picture"]

    @property
    def picture(self):
        """The user's profile picture as a bytes string"""
        if not self.picture_url: #The profile picture is blank
            return b''

        if not self.__picture: #We never queried the profile pic before
            response = requests.get(self.picture_url, timeout = static.Delays.request_timeout)
            assert response.status_code == 200, "Status code " + str(response.status_code)

            self.__picture = response.content

        return self.__picture

    @property
    def verified_badge(self):
        """Is the user verified?"""
        return self["verified_badge"]

    @property
    def followers(self):
        """The number of followers this user has"""
        return self["followers"]

    @property
    def followed(self):
        """TODO -> Bool"""
        return self["followed"]

class APIPlaylist(JSONObj):
    """Playlist as returned by the API"""
    def __init__(self, jsondata):
        """Pass the JSON data of a playlist"""
        super().__init__(jsondata)
        self.user = APIUser(jsondata["user"])

    def __int__(self):
        """The playlist as an integer (it's ID in base 10)"""
        return self.playlist_id_b10

    def __str__(self):
        """The playlist as a string (it's ID in base 36)"""
        return self.playlist_id_b36

    def __eq__(self, other):
        """Determine if this playlist is equal to another"""
        #Check for direct matches first
        if isinstance(other, int):
            return self.playlist_id_b10 == other
        if isinstance(other, str):
            return str(other) == self.playlist_id_b36

        #Check for object attributes to match to
        if hasattr(other, "playlist_id"):
            return self.playlist_id_b10 == utils.ensure_b10(other.playlist_id)

        #Check conversion to integer last, in case another ID or something happens to match
        if hasattr(other, "__int__"):
            return self.playlist_id_b10 == int(other)

    @property
    def playlist_id(self):
        """The numeric playlist ID in base 36"""
        return self["id"]

    @property
    def playlist_id_b36(self):
        """The numeric ID of the playlist in base 36"""
        return self.playlist_id

    @property
    def playlist_id_b10(self):
        """The numeric ID of the playlist in base 10"""
        return utils.base_36_to_10(self.playlist_id)

    @property
    def title(self):
        """The title of the playlist"""
        return self["title"]

    @property
    def description(self):
        """The description of the playlist"""
        return self["description"]

    @property
    def visibility(self):
        """The visibility of the playlist"""
        return self["visibility"]

    @property
    def url(self):
        """The URL of the playlist"""
        return self["url"]

    @property
    def channel(self):
        """The channel the playlist is under, can be None"""
        return self["channel"]

    @property
    def created_on(self):
        """The time the playlist was created in seconds since epoch"""
        return utils.parse_timestamp(self["created_on"])

    @property
    def updated_on(self):
        """The time the playlist was last updated in seconds since epoch"""
        return utils.parse_timestamp(self["updated_on"])

    @property
    def permissions(self):
        """The permissions the ServicePHP user has on this playlist"""
        return self["permissions"]

    @property
    def num_items(self):
        """The number of items in the playlist"""
        return self["num_items"]

    @property
    def is_following(self):
        """TODO -> Bool"""
        return self["is_following"]

    @property
    def items(self):
        """The items of the playlist. TODO"""
        return self["items"]

    @property
    def extra(self):
        """TODO -> None, unknown"""
        return self["extra"]

class ServicePHP:
    """Interact with Rumble's service.php API"""
    def __init__(self, username: str, password: str = None, session = None):
        """Pass the username, and either a password or a session token (accepts cookie dict or base string)"""
        #Save the username
        self.username = username

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

        #Stored ID of the logged in user
        self.__user_id = None

    @property
    def user_id(self):
        """The numeric ID of the logged in user in base 10"""
        #We do not have a user ID, extract it from the unread notifications response
        if self.__user_id is None:
            j = self.sphp_request(
                "user.has_unread_notifications",
                method = "GET",
                ).json()
            self.__user_id = utils.base_36_to_10(j["user"]["id"].removeprefix("_"))

        return self.__user_id

    @property
    def user_id_b10(self):
        """The numeric ID of the logged in user in base 10"""
        return self.user_id

    @property
    def user_id_b36(self):
        """The numeric ID of the logged in user in base 36"""
        return utils.base_10_to_36(self.user_id)

    def sphp_request(self, service_name: str, data: dict = {}, additional_params: dict = {}, logged_in = True, method = "POST"):
        """Make a request to Service.PHP with common settings
        service_name: The name parameter of the specific PHP service
        data: Form data
        additional_params: Any additional query string parameters
        logged_in: The request should use the session cookie"""
        params = {"name" : service_name}
        params.update(additional_params)
        r = requests.request(
                method,
                static.URI.servicephp,
                params = params,
                data = data,
                headers = static.RequestHeaders.user_agent,
                cookies = self.session_cookie if logged_in else None,
                timeout = static.Delays.request_timeout,
                )
        assert r.status_code == 200, f"Service.PHP request for {service_name} failed: {r}\n{r.text}"
        #If the request json has a data -> success value, make sure it is True
        d = r.json().get("data")
        if isinstance(d, dict):
            assert d.get("success", True), f"Service.PHP request for {service_name} failed: \n{r.text}"
        #Data was not a dict but was not empty
        elif d:
            print(f"Service.PHP request for {service_name} did not fail but returned unknown data type {type(d)}: {d}")

        return r

    def login(self, username, password):
        """Obtain a session cookie and user ID from username and password"""
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
        j = r.json()
        session_token = j["data"]["session"]
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
                "video": int(video),
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

    def is_comment_elem(self, e):
        """Check if a beautifulsoup element is a comment"""
        return e.name == "li" and "comment-item" in e.get("class") and "comments-create" not in e.get("class")

    def comment_list(self, video_id):
        """Get the list of comments under a video"""
        r = self.sphp_request(
            "comment.list",
            additional_params = {
                "video" : utils.ensure_b36(video_id),
                },
            method = "GET",
            )
        soup = bs4.BeautifulSoup(r.json()["html"], features = "html.parser")
        comment_elems = soup.find_all(self.is_comment_elem)
        return [scraping.HTMLComment(e) for e in comment_elems]

    def comment_add(self, video_id: int, comment: str, reply_id: int = 0):
        """Post a comment on a video
        video_id: The numeric ID of a video / stream
        comment: What to say
        reply_id: The ID of the comment to reply to
            Defaults to zero (don't reply to anybody)"""
        r = self.sphp_request(
                "comment.add",
                data = {
                    "video": int(video_id),
                    "reply_id": int(reply_id),
                    "comment": str(comment),
                    "target": "comment-create-1",
                    },
                )
        return APIComment(r.json()["data"])

    def comment_pin(self, comment_id: int, unpin: bool = False):
        """Pin or unpin a comment by ID
        comment_id: Integer comment ID
        unpin: If true, unpins instead of pinning comment"""
        self.sphp_request(
            f"comment.{"un" * unpin}pin",
            data = {"comment_id": int(comment_id)},
            )

    def comment_delete(self, comment_id: int):
        """Delete a comment by ID"""
        self.sphp_request(
            "comment.delete",
            data = {"comment_id": int(comment_id)},
            )

    def comment_restore(self, comment_id: int):
        """Restore a deleted comment by ID"""
        r = self.sphp_request(
            "comment.restore",
            data = {"comment_id": int(comment_id)},
            )
        return APIComment(r.json()["data"])

    def rumbles(self, vote: int, item_id, item_type: int):
        """Post a like or dislike
        vote: -1, 0, or 1
        item_id: The numeric ID of whatever we are liking or disliking
        item_type: 1 for video, 2 for comment"""
        r = self.sphp_request(
            "user.rumbles",
            data = {
                "type" : int(item_type),
                "id" : utils.ensure_b10(item_id),
                "vote" : int(vote),
                },
            )
        return APIContentVotes(r.json()["data"])

    def get_video_url(self, video_id):
        """Get the URL of a Rumble video from Service.PHP's media.share"""
        r = self.sphp_request(
            "media.share",
            additional_params = {
                "video" : utils.ensure_b36(video_id),
                "start" : 0,
                },
            method = "GET",
            )
        soup = bs4.BeautifulSoup(r.json()["html"], features = "html.parser")
        elem = soup.find("div", attrs = {"class" : "fb-share-button share-fb"})
        return elem.attrs["data-url"]

    def playlist_add_video(self, playlist_id: str, video_id: int):
        """Add a video to a playlist"""
        print(self.sphp_request(
            "playlist.add_video",
            data = {
                "playlist_id": str(playlist_id),
                "video_id": utils.ensure_b10(video_id),
                }
            ).text)

    def playlist_delete_video(self, playlist_id: str, video_id: int):
        """Remove a video from a playlist"""
        print(self.sphp_request(
            "playlist.delete_video",
            data = {
                "playlist_id": str(playlist_id),
                "video_id": utils.ensure_b10(video_id),
                }
            ).text)

    def playlist_add(self, title: str, description: str = "", visibility: str = "public", channel_id: int = None):
        """Create a new playlist
        title: The title of the playlist.
        description: Describe the playlist.
            Defaults to nothing.
        visibility: Set to public, unlisted, or private via string.
            Defaults to public.
        channel_id: The ID of the channel to create the playlist under.
            Defaults to none."""
        r = self.sphp_request(
            "playlist.add",
            data = {
                "title": str(title),
                "description": str(description),
                "visibility": str(visibility),
                "channel_id": str(utils.ensure_b10(channel_id)) if channel_id else None,
            }
        )
        return APIPlaylist(r.json()["data"])

    def playlist_edit(self, playlist_id: str, title: str, description: str = "", visibility: str = "public", channel_id: int = None):
        """Edit the details of an existing playlist
        playlist_id: The ID of the playlist to edit.
        title: The title of the playlist.
        description: Describe the playlist.
            Defaults to nothing.
        visibility: Set to public, unlisted, or private via string.
            Defaults to public.
        channel_id: The ID of the channel to create the playlist under.
            Defaults to none."""

        r = self.sphp_request(
            "playlist.edit",
            data = {
                "title": str(title),
                "description": str(description),
                "visibility": str(visibility),
                "channel_id": str(utils.ensure_b10(channel_id)) if channel_id else None,
                "playlist_id": utils.ensure_b36(playlist_id),
            }
        )
        return APIPlaylist(r.json()["data"])

    def playlist_delete(self, playlist_id: str):
        """Delete a playlist"""
        print(self.sphp_request(
            "playlist.delete",
            data = {"playlist_id" : utils.ensure_b36(playlist_id)},
            ).text)

    def raid_confirm(self, stream_id: int):
        """Confirm a raid set up in the chat of the given livestream"""
        self.sphp_request(
            "raid.confirm",
            data = {"video_id" : utils.ensure_b10(stream_id)},
            )
