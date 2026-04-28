from lib.common.cli import download_parser
from lib.client import Client
from lib.common.logger import Logger

def main():

    args = download_parser()
    Logger.configure(args.verbose, args.quiet, "CLIENT")
    client = Client(args.host, args.port)
    # client.send_message("Holaa soy download".encode())
    # client.wait_response()
    client.download_file(args.dst, args.name)
    client.close()

if __name__ == "__main__":
    main()