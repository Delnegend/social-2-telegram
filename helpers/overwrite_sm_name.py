def overwrite_sm_name(old_name: str) -> str:
    match old_name:
        case foo if "Twitter" in foo:
            return old_name.replace("Twitter", "𝕏")
        case foo if "FA" in foo:
            return old_name.replace("FA", "FA 🐾")
        case foo if "Ko-fi" in foo:
            return old_name.replace("Ko-fi", "Ko-fi 🍵")
        case foo if "buymeacoffee" in foo:
            return old_name.replace("buymeacoffee", "buymeacoffee 🍵")
        case _:
            return old_name
