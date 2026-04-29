from tp1.src.lib.client.Client import Client
from lib.common.cli import upload_parser
from tp1.src.lib.common.constants import OP_TYPE_UPLOAD

def main():
    args = upload_parser()

    client = Client(args.protocol, args.host, args.port, OP_TYPE_UPLOAD)
    client.start(args.src, args.name)
    client.upload_file(args.src, args.name)

if __name__ == "__main__":
    main()