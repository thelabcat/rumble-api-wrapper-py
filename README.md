<h1><img src="https://raw.githubusercontent.com/thelabcat/rumble-api-wrapper-py/main/cocorum_icon.png" alt="" width="64"/> Cocorum: Rumble Live Stream API Python Wrapper</h1>

A Python wrapper for the Rumble Live Stream API v1.0 (beta), with some quality of life additions, such as:

- Automatic refresh when past the refresh_rate delay when querying any non_static property.
- All timespamps are parsed to seconds since Epoch, UTC timezone.
- Chat has new_messages and new_rants properties that return only messages and rants since the last time they were read.

## Usage:
I tried to document the wrapper well, so help("cocorum") should work. Note, you are only expected to create a RumbleAPI() and / or ssechat.SSEChat() object, and work with everything through them.

Most attributes that are not added features have the same name as the direct JSON counterparts, with the exception of adding prefixes to some things that have the same name in the JSON as Python builtin functions. For example, thing/id in JSON is thing.thing_id in this Python wrapper.

```
from cocorum import RumbleAPI
import time

#API_URL is either Rumble Live Stream API URL with key
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

## Experimental internal API submodules
This part of Cocorum is not part of the official Rumble Live Stream API. It includes the following submodules:
- chatapi
- servicephp
- uploadphp

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

## Conclusion
Hope this helps!

I, Wilbur Jaywright, and my brand, Marswide BGL, have no official association with Rumble Corp. beyond that of a normal user and/or channel on the Rumble Video platform. This wrapper is not officially endorsed by Rumble Corp. or its subsidiaries.

S.D.G.
