<h1><img src="https://raw.githubusercontent.com/thelabcat/rumble-api-wrapper-py/main/cocorum_icon.png" alt="" width="64"/> Cocorum: Rumble Live Stream API Python Wrapper</h1>

A Python wrapper for the Rumble Live Stream API v1.0 (beta), with some quality of life additions, such as:

- Automatic refresh when past the refresh_rate delay when querying any non_static property.
- All timespamps are parsed to seconds since Epoch, UTC timezone.
- Chat has new_messages and new_rants properties that return only messages and rants since the last time they were read.

## Table Of Contents

1. [Tutorials](tutorials.md)
2. [How-To Guides](how-to-guides.md)
3. [Reference](reference.md)
4. [Explanation](explanation.md)

## Acknowledgements

Special thanks to GlobalGamer2015 for information on the SSE chat API, and to K4nji for help with the password hashing algorithm. Both helped with other API endpoints as well.

I, Wilbur Jaywright, and my brand, Marswide BGL, have no official association with Rumble Corp. beyond that of a normal user and/or channel on the Rumble Video platform. This wrapper is not officially endorsed by Rumble Corp. or its subsidiaries.

S.D.G.
