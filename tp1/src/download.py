from lib.download.cli import cli
from lib.common.Client import Client
from lib.constants import OP_TYPE_DOWNLOAD

def main():
    args = cli()
    client = Client(args.protocol, args.host, args.port, OP_TYPE_DOWNLOAD)
    # client.send_message("Holaa soy download".encode())
    # client.wait_response()
    client.download_file(args.dst, args.name)
    client.close()

if __name__ == "__main__":
    main()