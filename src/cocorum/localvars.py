#!/usr/bin/env python3
"""Cocorum local variable definitions

This submodule provides absolute variable definitions for Cocorum.

S.D.G."""

#Rumble timestamp format, not including the 6 TODO characters at the end
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S"

#Headers for the Rumble Live Stream API request (currently must fake a User-Agent string)
LS_API_HEADERS = {"User-Agent" : "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"}

#Headers for the SSE chat API
SSE_API_HEADERS = {'Accept': 'text/event-stream'}

#Keys of the API JSON that should not change unless the API URL changes, and so do not trigger a refresh
STATIC_KEYS = [
    "user_id",
    "username",
    "channel_id",
    "channel_name",
    ]

#Keys of the API JSON stream object that should not trigger a refresh
STATIC_KEYS_STREAM = [
    "id",
    "created_on"
    ]

#API types, under JSON["type"]
API_TYPE_USER = "user"
API_TYPE_CHANNEL = "channel"

#Stream visibility possibilities, under JSON["livestreams"][0]["visibility"]
STREAM_VIS_PUBLIC = "public"
STREAM_VIS_UNLISTED = "unlisted"
STREAM_VIS_PRIVATE = "private"

#Base URL to Rumble's website, for URLs that are relative to it
RUMBLE_BASE_URL = "https://rumble.com"

#Numerical base that the stream ID is in
STREAM_ID_BASE = "0123456789abcdefghijklmnopqrstuvwxyz"

#Rumble's SSE chat display URL for a stream, format this string with a stream_id_b10
SSE_CHAT_URL = "https://web7.rumble.com/chat/api/chat/{stream_id_b10}/stream"

#Size of chat badge icons to retrieve, only valid one has long been the string 48
BADGE_ICON_SIZE = "48"

#How long to wait before giving up on a network request, in seconds
DEFAULT_TIMEOUT = 20

#How long to reuse old data from the API, in seconds
DEFAULT_REFRESH_RATE = 10

#Dictionary of badge slugs mapped to UTF-8 glyphs
BADGES_AS_GLYPHS = {
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
