from lib.server.cli import cli
from lib.server.Server import Server

def main():
    args = cli()
    sv = Server(args.storage, args.host, args.port)
    sv.start()

if __name__ == "__main__":
    main()