from lib.download.cli import cli
from lib.common.Client import Client
from lib.common.logger import Logger

def main():

    args = cli()
    Logger.configure(args.verbose, args.quiet, "CLIENT")
    client = Client(args.host, args.port)
    # client.send_message("Holaa soy download".encode())
    # client.wait_response()
    client.download_file(args.dst, args.name)
    client.close()

if __name__ == "__main__":
    main()