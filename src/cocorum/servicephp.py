#!/usr/bin/env python3
"""Service.PHP interactions

Control Rumble via Service.PHP
S.D.G."""

import requests
from . import static
from . import utils

def test_session_cookie(session_cookie):
    """Test if a session token is valid"""
    r = requests.get(static.URI.login_test,
            cookies = session_cookie,
            headers = static.RequestHeaders.user_agent,
            timeout = static.Delays.request_timeout,
        )

    assert r.status_code == 200, f"Testing session token failed: {r}"

    title = r.text.split("<title>")[1].split("</title>")[0]

    #If the session token is invalid, it won't log us in and "Login" will still be shown
    return "Login" not in title

def login(username, password):
    """Obtain a session cookie from username and password"""
    #Get salts
    r = requests.post(
            static.URI.ServicePHP.get_salts,
            data = {"username": username},
            headers = static.RequestHeaders.user_agent,
            timeout = static.Delays.request_timeout,
            )
    assert r.status_code == 200, f"Password salts request failed: {r}"
    salts = r.json()["data"]["salts"]

    #Get session token
    r = requests.post(
            static.URI.ServicePHP.login,
            data = {
                "username": username,

                #Hash the password using the salts
                "password_hashes": ",".join(utils.calc_password_hashes(password, salts)),
                },
            headers = static.RequestHeaders.user_agent,
            timeout = static.Delays.request_timeout,
            )
    assert r.status_code == 200, f"Login request failed: {r}"
    session_token = r.json()["data"]["session"]
    assert session_token, "Login failed: No token returned"

    return {"u_s": session_token}

def pin_message(session_cookie, stream_id_b10, message):
    """Pin a message in a chat"""
    r = requests.post(
            static.URI.ServicePHP.pin,
            data = {
                "video_id": stream_id_b10,
                "message_id": int(message),
                },
            headers = static.RequestHeaders.user_agent,
            cookies = session_cookie,
            timeout = static.Delays.request_timeout,
            )
    assert r.status_code == 200, f"Pin request failed: {r}"


def unpin_message(session_cookie, stream_id_b10, message):
    """Unpin a message in a chat"""
    r = requests.post(
            static.URI.ServicePHP.unpin,
            data = {
                "video_id": stream_id_b10,
                "message_id": int(message),
                },
            headers = static.RequestHeaders.user_agent,
            cookies = session_cookie,
            timeout = static.Delays.request_timeout,
            )
    assert r.status_code == 200, f"Unpin request failed: {r}"

def mute_user(session_cookie, username: str, is_channel: bool = False, video: int = None, duration: int = None, total: bool = False):
    """Mute a user or channel by name"""
    r = requests.post(
            static.URI.ServicePHP.mute,
            data = {
                    "user_to_mute": username,
                    "entity_type": ("user", "channel")[is_channel],
                    "video": video,
                    "duration": duration,
                    "type": ("video", "total")[total],
                },
            headers = static.RequestHeaders.user_agent,
            cookies = session_cookie,
            timeout = static.Delays.request_timeout,
            )
    assert r.status_code == 200, f"Mute request failed: {r}"

def unmute_user(session_cookie, record_id: int):
    """Unmute a user by record ID"""
    r = requests.post(
            static.URI.ServicePHP.unmute,
            data = {
                "record_id" : record_id,
                },
            headers = static.RequestHeaders.user_agent,
            cookies = session_cookie,
            timeout = static.Delays.request_timeout,
            )
    assert r.status_code == 200, f"Unmute request failed: {r}"
