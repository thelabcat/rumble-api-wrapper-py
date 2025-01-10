# Explanation

## Why I created this library
This wrapper library started off as an idea I got while writing [this app for taking chat polls](https://github.com/thelabcat/rumble-chat-poll), but at first I dismissed it as overengineering. That app turned out to be kind of a mess of threading, and although that wasn't entirely the API access code's fault, it felt like a big part of it. I was used to neat wrappers, and didn't like having to go through a bunch of dictionary keys, keeping track of some while repeating others, and having to do checks to make sure they were still valid. I might've avoided some of this if I'd known about the `dict().get()` method at the time, but I'm kinda glad I didn't. Later, when I started thinking about writing another Rumble app, I realized how much of the API access code I would be reusing, especially the part where I made sure I didn't query it too frequently or too rarely to stay up-to-date. An object with a refresh timer would be useful. And so I wrote Cocorum. Later, GlobalGamer2015 helped me understand the SSE chat stream API and how to use it, and I added that as a submodule. K4nji later helped me understand the hashing algorithm that a3r0id had discovered, and helped me figure out a bunch of other endpoints, adding login and multiple other submodules. Both have continued to help me, and I thank The LORD for that. If Jesus hadn't gotten us together, this package would not exist to nearly this degree if at all.

## Example use cases
This library is currently the foundation under [Rumble Chat Actor](https://github.com/thelabcat/rumble-chat-actor), a framework for chat commands and other more standardized livestream chat interaction features. It utilizes many parts of Cocorum, so for example use cases and for its own sake I recommend you go check it out.

I intend to write a serious spam detection and moderation app in the future, similar to [this project for YouTube](https://github.com/ThioJoe/YT-Spammer-Purge), but I'd actually prefer somebody else did it.

## Missing endpoints
Some endpoints are currently missing from this wrapper, and that's not always intentional. There are endpoints or ways to get some data whih I didn't know about when, or were added since, I wrote those sections of the library. Those will be added. Some endpoints, however, were left off on purpose. I decided these would not be useful to any third-party developer, or could not be useful in an honest way. Some endpoints I did include for consistency may additionally be removed later for this same reason.

## Programmers should be forbidden from all naming things
When Rumble went public with the tag $RUM, they posted a bottle of coconut rum stylized with their branding as a celebratory thing. The name "cocorum" is based on this, and also that I like both coconuts and cocoa. The idea of Rumble being shelled inside the logo was a cute afterthought.

# Solo Deo Gloria.
