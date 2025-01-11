# cocorum.chatapi

The primary use from this module is the `ChatAPI` class, a wrapper for Rumble's internal chat API. When passed credentials, it currently automatically creates an internal instance of `cocorum.servicephp.ServicePHP()` to log in with, and includes links to the chat-related methods of `ServicePHP()` (muting users for example).
All other classes are supporting sub-classes.

::: cocorum.chatapi

S.D.G.
