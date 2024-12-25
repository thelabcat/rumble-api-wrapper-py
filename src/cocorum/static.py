#!/usr/bin/env python3
"""Cocorum static variable definitions

Provides various data that, if changed, would change globally

S.D.G."""

class RequestHeaders:
    """Headers for various HTTPrequests"""

    #Header with a fake user-agent string
    user_agent = {"User-Agent" : "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"}

    #Headers for the SSE chat API
    sse_api = {'Accept': 'text/event-stream'}

class StaticAPIEndpoints:
    """API endpoints that don't change and shouldn't trigger a refresh"""
    #Endpoints of the main API
    main = [
        "user_id",
        "username",
        "channel_id",
        "channel_name",
        ]

    #Endpoints of the stream subobject
    stream = [
        "id",
        "created_on"
        ]

class URI:
    """URIs to various Rumble services"""

    #Base URL to Rumble's website, for URLs that are relative to it
    rumble_base = "https://rumble.com"

    #Test the session token by sending it here and checking the title
    login_test = rumble_base + "/login.php"

    #Webpage with all the mutes on it, format with page number
    mutes_page = rumble_base + "/account/moderation/muting?pg={page}"

    #Channels under a user, format with username
    channels_page = rumble_base + "/user/{username}/channels"

    #The logged-in user's playlist page
    playlists_page = rumble_base + "/my-library/playlists"

    #The Service.PHP API
    servicephp = "https://rumble.com/service.php"

    #The video upload PHP
    uploadphp = "https://web18.rumble.com/upload.php"

    class ChatAPI:
        """URIs of the chat API"""

        #Rumble's internal chat URL for a stream, format this string with a stream_id_b10
        base = "https://web7.rumble.com/chat/api/chat/{stream_id_b10}"

        #SSE stream of chat events
        sse_stream = base + "/stream"

        #Message actions
        message = base + "/message"

        #Chat commands (does not use the base)
        command = "https://rumble.com/chat/command"


class Delays:
    """Various times for delays and waits"""

    #How long to wait before giving up on a network request, in seconds
    request_timeout = 20

    #How long to reuse old data from the API, in seconds
    api_refresh_default = 10

class Message:
    """For chat messages"""

    #Maximum chat message length
    max_len = 200

    #How long to wait between sending messages
    send_cooldown = 3

    #Prefix Rumble uses for native command
    command_prefix = "/"

class Upload:
    """Data relating to uploading videos"""
    #Size of upload chunks, not sure if this can be changed
    chunksz = 10000000

    #Upload API version to use
    api_ver = "1.3"

    #Maximum upload size is 15GB as stated by Rumble
    max_filesize = 15 * (1000 ** 3)

class Misc:
    """No idea where else to put this data"""
    #Numerical base that the stream ID is in
    base36 = "0123456789abcdefghijklmnopqrstuvwxyz"

    #Dictionary of badge slugs mapped to UTF-8 glyphs
    badges_as_glyphs = {
        "verified" : "✅",
        "admin" : "👑",
        "moderator" : "🛡",
        "premium" : "🗲",
        "locals" : "♖",
        "recurring_subscription" : "♖",
        "locals_supporter" : "⛋",
        "whale-grey" : "🐳",
        "whale-yellow" : "🐳",
        "whale-blue" : "🐳",
        }

    #Encoding for all text-bytes conversions
    text_encoding = "utf-8"

    #Size of chat badge icons to retrieve, only valid one has long been the string 48
    badge_icon_size = "48"

    #Rumble timestamp format, not including the 6 TODO characters at the end
    timestamp_format = "%Y-%m-%dT%H:%M:%S"

    #Key of the session token within the session cookie dict
    session_token_key = "u_s"

    class ContentTypes:
        """Types of content that can be rumbled on"""

        #A video or livestream
        video = 1

        #A comment
        comment = 2
