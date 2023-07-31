def overwrite_sm_name(old_name: str) -> str:
    match old_name:
        case foo if "Twitter" in foo:
            return old_name.replace("Twitter", "𝕏")
        case foo if "FA" in foo:
            return old_name.replace("FA", "FA 🐾")
        case _:
            return old_name
