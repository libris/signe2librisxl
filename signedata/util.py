from pathlib import Path

heredir = Path(__file__).parent


def asiter(o):
    if o is None:
        return
    if isinstance(o, list):
        yield from o
    else:
        yield o


def get_etc_path(fname: str) -> Path:
    """
    Get `Path` to an "extra tool config" file.
    """
    return heredir.absolute() / 'etc' / fname
