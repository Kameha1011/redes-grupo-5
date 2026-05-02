from pathlib import Path

BASE_DIR = Path("storage")

def get_file(filepath: str) -> bytes:
    file_path = Path(filepath)
    if not file_path.is_file():
        raise FileNotFoundError(str(file_path))
    return file_path.read_bytes() # Manu: guarda con esto. El archivo puede ser muy grande


def save_file(dirpath: str, name: str, bytes: bytes) -> None:
    name_path = Path(name)
    if name_path.is_absolute() or name_path.name != name:
        raise ValueError("name must be a file name without path components")

    file_path = Path(dirpath) / name
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(bytes)

def create_file(name: str):
    path = BASE_DIR / name
    path.parent.mkdir(parents=True, exist_ok=True)

    f = open(path, "wb")  # binario
    return f

def write_chunk(f, data: bytes):
    f.write(data)

def open_file(path: str):
    return open(path, "rb")

def read_chunk(f, size: int) -> bytes:
    return f.read(size)

def get_size(path):
    return Path(path).stat().st_size