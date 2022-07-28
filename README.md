# mastodon-archive-static-site

_A Python script to convert a Mastodon user archive into a static site._

## Purpose

This script will take the `.tar.gz` archive that a Mastodon server can generate for one of its users (requested via _Settings → Import and export → Data export → Request your archive_) and, for each public toot in there, create a subdirectory with an `index.html` file and all of the toot’s attachments, so that you can seamlessly replace the original toot permalinks with these static files.

## Status

This is an unfinished prototype.

The main thing that’s missing at this time is a beautiful (but self-contained) design for the generated pages.
Hit me up if you’re interested in contributing that, I’m not good at it.

## Usage

Requires Python 3.6 or higher with `Jinja2` and (optionally) `requests` installed.

Run `./generate.py --help` for usage information.

By default, the generated pages are written to `./output/`.
You can use `-o DIR` to change that.

A simple example call would be `./generate.py archive-20220414144106-fbdf204a1bdf9375618d8a032d5a64d8.tar.gz`.

## Archiving to the Wayback Machine

**This whole feature is experimental and kinda sucks right now.**

If the Mastodon instance still exists, you can use the `-w` command-line switch to ask the [Wayback Machine](https://web.archive.org/) aka `web.archive.org` to add each toot to its archive.

You’ll need to have `requests` installed.

This flag will result in one API call to the Wayback Machine for each public toot in the archive.
Note that each of these calls usually takes significantly more than 30 seconds, and I have not yet tested whether archive.org is happy about thousands of requests, even though it’s only one at a time.

There is currently no way to resume these calls if your `generate.py` invocation gets terminated or something, you’ll have to start over.
Try to avoid this, I guess.

## Contact

This project lives at <https://codeberg.org/scy/mastodon-archive-static-site>.
You can find the author on Mastodon: [@scy@chaos.social](https://chaos.social/@scy).

## License

MIT.
