# Cocorum: Rumble Livestream API Python Wrapper
A Python wrapper for the Rumble Livestream API v1.0 (beta), with some quality of live additions, such as:
- Automatic refresh when past the refresh_rate delay when querying any non_static property.
- All timespamps are parsed to seconds since Epoch, UTC timezone.
- Chat has new_messages and new_rants properties that return only messages and rants since the last time they were read.

## Usage:
I tried to document the wrapper well, so the help function should work. Note, you are only expected to create a RumbleAPI object, and work with everything through that.

Most attributes that are not added features have the same name as the direct JSON counterparts, with the exception of adding prefixes to some things that have the same name in the JSON as Python builtin functions. For example, thing/id in JSON is thing.thing_id in this Python wrapper.

```
from cocorum import RumbleAPI
api = RumbleAPI(API_URL, refresh_rate = 10)
print(api.username)
print(api.latest_follower)
if api.latest_subscriber:
    print(api.latest_subscriber, "subscribed for $" + str(api.latest_subscriber.amount_dollars))
livestream = api.latest_livestream #None if there is no stream running
if livestream:
    message = livestream.chat.latest_message #None if there are no messages yet
    if message:
        print(message.username, "said", message)
```

Hope this helps!

I, Wilbur Jaywright, and my brand, Marswide BGL, have no official association with Rumble Corp. beyond that of a normal user and/or channel on the Rumble Video platform. This wrapper is not officially endorsed by Rumble Corp. or its subsidiaries.

S.D.G.
