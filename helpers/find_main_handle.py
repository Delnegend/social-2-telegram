from option import Option, Some


def find_main_handle(artist_handle: str, artists_alt_handles: dict[str, set[str]]) -> Option[str]:
    for handle, alt_handles in artists_alt_handles.items():
        if artist_handle.lower() in [handle.lower()] + [alt_handle.lower() for alt_handle in alt_handles]:
            return Some(handle)
    return Option.NONE()  # type: ignore
