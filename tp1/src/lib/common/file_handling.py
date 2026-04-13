from pathlib import Path


def get_file(path: str, name: str) -> bytes:
    file_path = Path(path) / name
    if not file_path.is_file():
        raise FileNotFoundError(str(file_path))
    return file_path.read_bytes()


def save_file(path: str, name: str, bytes: bytes) -> None:
    name_path = Path(name)
    if name_path.is_absolute() or name_path.name != name:
        raise ValueError("name must be a file name without path components")

    file_path = Path(path) / name
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(bytes)