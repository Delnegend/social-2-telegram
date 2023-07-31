import os

import yaml

from classes.NewArtist import ArtistInfoData


def artists_info_load() -> tuple[dict[str, ArtistInfoData], dict[str, str]]:
    """Load artist info from yaml files and return them as a tuple of dicts."""
    if not os.path.isfile("artist_info.yaml"):
        with open(file="artist_info.yaml", mode="w", encoding="utf-8") as f:
            yaml.dump({}, f, sort_keys=False, allow_unicode=True, indent=4)

    with open(file="artist_info.yaml", mode="r", encoding="utf-8") as f:
        data = yaml.load(f, Loader=yaml.FullLoader).items()
        artists_info = {
            artist_username: ArtistInfoData(
                country_flag=artist_info["country_flag"] or "",
                hashtag_represent=artist_info["hashtag_represent"] or "",
                social_media=artist_info["social_media"],
            )
            for artist_username, artist_info in data
        }

    if not os.path.isfile("artist_alt_account.yaml"):
        with open(file="artist_alt_account.yaml", mode="w", encoding="utf-8") as f:
            yaml.dump({}, f, sort_keys=False, allow_unicode=True, indent=4)

    with open(file="artist_alt_account.yaml", mode="r", encoding="utf-8") as f:
        data = yaml.load(f, Loader=yaml.FullLoader).items()
        artists_alt_handles = {alt_account: main_account for alt_account, main_account in data}

    return artists_info, artists_alt_handles


def artists_info_save(artists_info: dict[str, ArtistInfoData], artists_alt_handles: dict[str, str]) -> None:
    with open(file="artist_info.yaml", mode="w", encoding="utf-8") as f:

        def process_sm_links(sm: dict[str, str]) -> dict[str, str]:
            res = {}
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

    with open(file="artist_alt_account.yaml", mode="w", encoding="utf-8") as f:
        artists_alt_handles = dict(sorted(artists_alt_handles.items(), key=lambda item: item[0]))
        yaml.dump(artists_alt_handles, f, sort_keys=False, allow_unicode=True, indent=4)
