import os


def norm(path: str) -> str:
    return os.path.normpath(path).replace("\\", "/")
