from option import Option, Some

from classes.NewArtist import ArtistInfoData


def find_main_handle(
    artist_handle: str, artists_alt_handles: dict[str, set[str]], artists_info: dict[str, ArtistInfoData]
) -> Option[str]:
    for handle, alt_handles in artists_alt_handles.items():
        if artist_handle.lower() in [handle.lower()] + [alt_handle.lower() for alt_handle in alt_handles]:
            return Some(handle)
    for item in artists_info.keys():
        if artist_handle.lower() == item.lower():
            return Some(item)
    return Option.NONE()  # type: ignore
