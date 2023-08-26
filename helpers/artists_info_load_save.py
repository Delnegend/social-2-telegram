import os

import yaml

from classes.NewArtist import ArtistInfoData
from variables.Config import Config


def artists_info_load() -> tuple[dict[str, ArtistInfoData], dict[str, set[str]]]:
    """Load artist info from yaml files and return them as a tuple of dicts."""

    if not os.path.isfile(Config.ARTISTS_INFO_FILE):
        with open(file=Config.ARTISTS_INFO_FILE, mode="w", encoding="utf-8") as f:
            yaml.dump({}, f, sort_keys=False, allow_unicode=True, indent=4)

    with open(file=Config.ARTISTS_INFO_FILE, mode="r", encoding="utf-8") as f:
        data = yaml.load(f, Loader=yaml.FullLoader).items()
        artists_info = {
            artist_username: ArtistInfoData(
                country_flag=artist_info["country_flag"] or "",
                hashtag_represent=artist_info["hashtag_represent"] or "",
                social_media=artist_info["social_media"],
            )
            for artist_username, artist_info in data
        }

    if not os.path.isfile(Config.ARTISTS_ALT_HANDLES_FILE):
        with open(file=Config.ARTISTS_ALT_HANDLES_FILE, mode="w", encoding="utf-8") as f:
            yaml.dump({}, f, sort_keys=False, allow_unicode=True, indent=4)

    with open(file=Config.ARTISTS_ALT_HANDLES_FILE, mode="r", encoding="utf-8") as f:
        artists_alt_handles = yaml.load(f, Loader=yaml.FullLoader).items()

    return dict(artists_info), dict(artists_alt_handles)


def artists_info_save(artists_info: dict[str, ArtistInfoData], artists_alt_handles: dict[str, set[str]]) -> None:
    with open(file=Config.ARTISTS_INFO_FILE, mode="w", encoding="utf-8") as f:

        def process_sm_links(sm: dict[str, str]) -> dict[str, str]:
            res: dict[str, str] = {}
            for sm_name, sm_link in sm.items():
                sm_link = sm_link.strip().replace("http://", "https://")
                if not sm_link.endswith("/"):
                    sm_link += "/"
                res[sm_name] = sm_link
            return res

        artists_info_yaml = {
            handle: {
                "country_flag": info.country_flag,
                "hashtag_represent": info.hashtag_represent if info.hashtag_represent != handle else "",
                "social_media": process_sm_links(info.social_media),
            }
            for handle, info in artists_info.items()
        }
        artists_info_yaml = dict(sorted(artists_info_yaml.items(), key=lambda item: item[0]))
        yaml.dump(artists_info_yaml, f, sort_keys=False, allow_unicode=True, indent=4)

    with open(file=Config.ARTISTS_ALT_HANDLES_FILE, mode="w", encoding="utf-8") as f:
        artists_alt_handles = dict(sorted(artists_alt_handles.items(), key=lambda item: item[0]))
        yaml.dump(
            {handle: list(alt_handles) for handle, alt_handles in artists_alt_handles.items()},
            f,
            sort_keys=False,
            allow_unicode=True,
            indent=4,
        )
