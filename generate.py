#!/usr/bin/env python3

import logging
from json import load
from pathlib import Path
import tarfile
from urllib.parse import urlparse

from jinja2 import Environment, FileSystemLoader
import requests


PUBLIC_URI = "https://www.w3.org/ns/activitystreams#Public"


logger = logging.getLogger("mastodon_archive_static_site")


class User:
    def __init__(self, file):
        self._data = data = load(file)
        self.name = data["name"]
        self.url = data["url"]
        self.short_handle = f"@{data['preferredUsername']}"

    def __str__(self):
        return f'"{self.name}" ({self.url})'


class Attachment:
    def __init__(self, data, toot):
        self._data = data
        self.toot = toot
        self.title = data.get("name", None)
        self.orig_path = data["url"]
        split = self.orig_path.split("/")
        self.tar_path = "/".join(split[2:])
        self.name = split[-1]


class Toot:
    def __init__(self, data, user):
        self._data = data
        self.user = user
        self.id = data["id"]
        obj = data["object"]
        self.url = obj["url"]
        self.content = obj["content"]
        self.isotime = obj["published"]
        self.in_reply_to = obj.get("inReplyTo", None)
        self.is_public = PUBLIC_URI in obj["to"]
        self.attachments = list([Attachment(a, self) for a in obj.get("attachment", [])])
        url = urlparse(self.url)
        self.basepath = url.path.strip("/")
        self.htmlpath = self.basepath + "/index.html"

    def __str__(self):
        return f"<{self.url}>: {self.content}"

    def wayback(self):
        logger.debug(f"Saving to Wayback Machine: {self.url}")
        try:
            res = requests.get(f"https://web.archive.org/save/{self.url}")
            res.raise_for_status()
            return True
        except Exception:
            logger.warn(f"Could not save in the Wayback Machine: {self.url}")
            return False

    def render(self, template):
        return template.render(toot=self, user=self.user)


class Toots:
    def __init__(self, file, user):
        self._data = load(file)
        self.toots = list([
            Toot(item, user)
            for item in self._data["orderedItems"]
            if item.get("type", None) == "Create"
        ])

    def __getitem__(self, index):
        return self.toots[index]

    def __len__(self):
        return len(self.toots)

    def __iter__(self):
        return iter(self.toots)


class Archive:
    def __init__(self, archive_path):
        logger.info(f"Opening archive: {archive_path}")
        self.tar = tarfile.open(archive_path)
        logger.info("Loading user information.")
        self.user = User(self.tar.extractfile("actor.json"))
        logger.info(f'User is {self.user}.')
        logger.info("Loading toot archive.")
        self.toots = Toots(self.tar.extractfile("outbox.json"), self.user)
        logger.info(f"{len(self.toots)} items loaded successfully.")

    def run(self, outdir, wayback=False):
        template_dir = Path(Path(__file__).parent, "templates")
        jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=True,
        )
        template = jinja_env.get_template("toot.html")
        for toot in self.toots:
            if not toot.is_public:
                continue
            outfile = Path(outdir, toot.htmlpath)
            logger.info(toot)
            outfile.parent.mkdir(parents=True, exist_ok=True)
            with open(outfile, "w") as outfile:
                outfile.write(toot.render(template))
            for attachment in toot.attachments:
                outfile = Path(outdir, toot.basepath, attachment.name)
                with open(outfile, "wb") as outfile:
                    outfile.write(self.tar.extractfile(attachment.tar_path).read())
            if wayback:
                toot.wayback()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Convert a Mastodon user archive into a static web site.",
    )
    parser.add_argument(
        "archive",
        metavar="FILE",
        help="a .tar.gz file as exported by Mastodon",
    )
    parser.add_argument(
        "-o, --output_dir",
        metavar="DIR",
        dest="output_dir",
        help="where to save the generated HTML pages to",
        default="output",
    )
    parser.add_argument(
        "-d, --debug",
        action="store_const",
        dest="log_level",
        const=logging.DEBUG,
        default=logging.INFO,
        help="enable more detailed log messages",
    )
    parser.add_argument(
        "-w, --wayback",
        action="store_true",
        dest="wayback",
        default=False,
        help="try to save each toot in the Wayback Machine (web.archive.org), "
            "will take > 10 seconds per toot",
    )
    args = parser.parse_args()

    logging.basicConfig(level=args.log_level)

    arch = Archive(args.archive)
    arch.run(args.output_dir, args.wayback)
