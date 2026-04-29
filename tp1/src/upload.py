from lib.common.Client import Client
from lib.upload.cli import cli
from lib.constants import OP_TYPE_UPLOAD

def main():
    args = cli()

    client = Client(args.protocol, args.host, args.port, OP_TYPE_UPLOAD)
    client.start(args.src, args.name)
    client.upload_file(args.src, args.name)

if __name__ == "__main__":
    main()