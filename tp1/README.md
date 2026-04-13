# File Transfer UDP

## Requirements

- Python 3.12 or higher.
- GNU/Linux Operating system (Maybe could work in others but we only give to support to GNU/Linux).

## Environment Setup

1. Create a virtual environment with `venv`.

`python3 -m venv .venv`

2. Activate it.

`source .venv/bin/activate`

## How to run

-  Start the server on your terminal like this:

`python3 src/start-server.py -H 0.0.0.0 -p 9000 -s ./server_storage`

- Now open other terminal and you can start uploading/downloading files like this:

`python3 src/upload.py -H 0.0.0.0 -p 7000 -s ~/Documents -n file.pdf`

`python3 src/download.py -H 0.0.0.0 -p 8000 -d ~/Documents -n file.pdf`

## Examples

