# Tutorials

## Reading chat using the Rumble Live Stream API wrapper
Class `cocorum.RumbleAPI` is the wrapper for [the Rumble Live Stream API](https://rumblefaq.groovehq.com/help/how-to-use-rumble-s-live-stream-api); the API Rumble has published for the public to use, furthermore referenced as the RLS API. To get started with it, you will first need an API "key" from Rumble (really it's a static URL with a key as a parameter, but you don't need to worry about that). You can get that URL with key [here](https://rumble.com/account/livestream-api).

The recommended way to handle most API keys is an environment variable, but since there's a good chance you could be handling multiple API keys on the same machine, I don't recommend this. Whatever you do, DO NOT HARDCODE IT! You can use [dotenv](https://pypi.org/project/dotenv/) to load it, or whatever method you prefer, but make sure that you do not accidentally distribute it. If you are using Git, you can add the filename to your repository's .gitignore file. All the code here will assume you have loaded your URL with key, and assigned it to `API_URL`.

With that taken care of, we can initialize the API wrapper. I recommend you do this in an interactive Python shell, such as IDLE, rather than a script. 

```
from cocorum import RumbleAPI

## API_URL is Rumble Live Stream API URL with key
api = RumbleAPI(API_URL, refresh_rate = 10)
```

The wrapper will load data from the API, then be ready to use. I'll explain the `refresh_rate` parameter in a moment.

Now we can query the wrapper for some data.

```
print(api.username)
## Should display your Rumble username

print("Latest follower:", api.latest_follower)
## Should display your latest follower, or None if you have none.
```

If you are familiar with the RLS API's JSON structure, this naming scheme should be familiar. Most of the JSON keys are translated directly into Python attribute names, with the general exception of `id` being augmented to `thing_id`, since `id` means something in Python.

Now, let's try to get the `latest_subscriber/amount_dollars` endpoint:

```
if api.latest_subscriber:
    print(api.latest_subscriber, f"subscribed for ${api.latest_subscriber.amount_dollars}")
## Should display your latest subscriber if you have one.
```

Note: If there is no latest subscriber, this endpoint will be None, and NoneType has no attribute amount_dollars. I added the `if` statement in that code to avoid an AttributeError.

You may have noticed by now that sometimes, querying data takes quite a bit longer than other times. This is `refresh_rate` in action. The way the Rumble Live Stream API currently works is by passing a big JSON data block of everything it knows, all at once. It would be very wasteful to ask it for this JSON block anew every time we wanted to read one value from it. But, after awhile we do want to check again and make sure it's up-to-date. The wrapper handles this by remembering the entire JSON block, and checking how old it is every time you make a query (with some exceptions). If the remembered JSON is older than `refresh_rate` (a value in seconds), the wrapper discards the JSON block and queries it again. Otherwise, it reuses the old data (it's not THAT old).

Now, about those exceptions, some properties will not be likely to change while you are using the API (the username it is under, for example). These are listed in `cocorum.static.StaticAPIEndpoints`. Because of this, querying those properties specifically will not trigger a refresh. They do still reference the newest remembered JSON, however, so if you really needed to get the latest version of them, you could run `api.check_refresh()` to make sure the remembered JSON is not older than `refresh_rate`.

The next part of the tutorial requires that you have a livestream up. You don't actually have to go live, you can just initialize it and then not actually stream, but the chat needs to be open. We are going to watch the chat in Python. Once you have the livestream up, query it from the API wrapper.

```
api.refresh() # Make sure the API data is up-to-date
livestream = api.latest_livestream # None if there is no stream running
```

We won't have to get this again, because Livestream objects returned by RumbleAPI are deep: When queried for data, they will make sure their sub-block of the JSON is still up-do-date, via an internal link to their parent RumbleAPI object.

Let's get some data on this livestream:

```
print(livestream.title)
print("Stream visibility is", livestream.visibility)

#We will use this later
STREAM_ID = livestream.stream_id

print("Stream ID is", STREAM_ID)
```

We will use that `STREAM_ID` in a later test, so don't close this interpreter!

Now that we've verified the `Livestream` object is working, we can start monitoring chat. To help with this kind of application, I added a `new_messages` virtual endpoint to the `LivestreamChat` API sub-wrapper class. When you query this, it will only return chat messages that are newer than the last time you queried it (or the time you first created the Livestream object instance). Effectively, it's like checking the chat mailbox. Let's check it frequently, for one minute. Be sure to send some chat messages in this time, so you can see this at work.

```
import time # We'll need this Python builtin for delays and knowing when to stop 

# Get messages for one minute
start_time = time.time()

# Continue as long as we haven't been going for a whole minute, and the livestream is still live
while time.time() - start_time < 60 and livestream.is_live:
    # For each new message...
    for message in livestream.chat.new_messages:
        # Display it
        print(message.username, "said", message)
    
    # Wait a bit, just to keep the loop from maxxing a CPU core
    time.sleep(0.1)
```

This is a good simple way to get slow chats' messages. But, what if the chat is moving too fast for this to be effective? RLS API queries have a max number of chat messages they will show into the past, and we could miss some if more than that many new chat messages arrive before we can refresh the JSON block. That was the problem GlobalGamer2015 encountered when developing [RUM Bot Live Alerts](https://www.rumbot.org/rum-bot-live-alerts/), and so he found and used a different API: The Rumble internal SSE chat stream.

## Reading chat using the ChatAPI wrapper
This is where Cocorum goes into the backroads of Rumble. So far, we have only seen wrappers for the API Rumble expresssly designed for the public to use. Past this point, we get into wrappers for APIs used by the internals of the web interface. If Rumble officially forbids / denies public access to them (which they have every right to do), these wrappers will break. Thankfully, they have made no indication that they intend to do so, as far as I know, so please, don't give them a reason to. We're fudging our boundaries here, make sure you respect the spirit of the law rather than just the letter. I do not, in any regards whatsoever, endorse any sort of cyber-arson, including but not limited to; disrupting the Rumble platform, via misuse of the public RSL API, or any other means.

With that being understood, let's connect to the SSE chat stream. I expect this to be in the same interpreter, so `time` will still be imported, api is still a RumbleAPI object, and `STREAM_ID` is still assigned, from earlier.

```
from cocorum import chatapi

chat = chatapi.ChatAPI(stream_id = STREAM_ID) #Stream ID can be base 10 or 36
chat.clear_mailbox() #Erase messages that were still visible before we connected
```

If you don't run `chat.clear_mailbox()`, then the following code will print messages that were already in chat before it gets to waiting for new ones. Anyways, let's monitor chat for one minute. 

```
# Get messages for one minute
start_time = time.time()

# Continue watching chat for one minute, or until the return of chat.get_message() is None (indicates a chat close)
while time.time() - start_time < 60 and (msg := chat.get_message()):
    print(msg.user.username, "said", msg)
```

A note about this. `ChatAPI().get_message()` will always wait for an additional message, even after the time runs out. I've also had trouble getting the chat to close properly once the stream ends, or staying open if it is inactive for several minutes. See [GitHub issue #5](https://github.com/thelabcat/rumble-api-wrapper-py/issues/5) for more info on this.
