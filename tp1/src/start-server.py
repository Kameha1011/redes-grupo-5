from lib.common.cli import server_parser
from lib.server.Server import Server

def main():
    args = server_parser()
    sv = Server(args.storage, args.host, args.port)
    sv.start()

if __name__ == "__main__":
    main()