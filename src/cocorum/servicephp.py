#!/usr/bin/env python3
"""Service.PHP interactions

Control Rumble via Service.PHP
S.D.G."""

import requests
from . import static
from . import utils

def test_session_token(session_token):
    """Test if a session token is valid"""
    r = requests.get(static.URI.login_test,
            cookies = {"u_s": session_token},
            headers = static.RequestHeaders.user_agent,
            timeout = static.Delays.request_timeout,
        )

    assert r.status_code == 200, f"Testing session token failed: {r}"

    title = r.text.split("<title>")[1].split("</title>")[0]

    #If the session token is invalid, it won't log us in and "Login" will still be shown
    return "Login" not in title

def login(username, password):
    """Obtain a session token from username and password"""
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
            timeout = static.Delays.request_timeout,
            )
    assert r.status_code == 200, f"Login request failed: {r}"
    session_token = r.json()["data"]["session"]
    assert session_token, "Login failed: No token returned"

    return session_token
