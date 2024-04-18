#!/usr/bin/env python3
#Cocorum local variable definitions
#S.D.G.

TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S" #Rumble timestamp format, not including the 6 TODO characters at the end

HEADERS = {"User-Agent" : "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"}

STATIC_KEYS = [ #Keys of the API JSON that should not change unless the API URL changes, and so do not trigger a refresh
    "user_id",
    "username",
    "channel_id",
    "channel_name",
    ]

STATIC_KEYS_STREAM = [ #Keys of the API JSON stream object that should not change unless the API URL changes, and so do not trigger a refresh
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
