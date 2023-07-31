from dataclasses import dataclass, field


@dataclass
class Post:
    url: str = ""

    profile_picture: str = ""
    handle: str = ""
    username: str = ""

    content: str = ""
    media_type: str = ""
    media: list[str] = field(default_factory=list)
    date: str = ""

    views: int = 0
    repost: int = 0
    quotes: int = 0
    comments: int = 0
    likes: int = 0
    bookmarks: int = 0
    rating: str = ""

    mention_link: list[tuple[str, str]] = field(default_factory=list)
    hashtag_link: list[tuple[str, str]] = field(default_factory=list)
    just_links: list[tuple[str, str]] = field(default_factory=list)

    @property
    def dict(self) -> dict[str, str | dict[str, str | int | list[str] | list[tuple[str, str]]] | list[str]]:
        return {
            "url": self.url,
            "account": f"{self.handle} ({self.username}) | {self.profile_picture}",
            "content": self.content,
            "media_type": self.media_type,
            "media": self.media,
            "date": self.date,
            "metrics": f"{self.views} views | {self.repost} reposts | {self.quotes} quotes | {self.comments} comments | {self.likes} likes | {self.bookmarks} bookmarks",
            "rating": self.rating,
            "urls": {
                "mentions": self.mention_link,
                "hashtags": self.hashtag_link,
                "just_links": self.just_links,
            },
        }
