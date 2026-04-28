from lib.common.Client import Client
from lib.protocol.stop_and_wait import StopAndWait
from lib.upload.cli import cli
from lib.constants import STOP_AND_WAIT, OP_TYPE_UPLOAD

def main():
    args = cli()

    protocol_choice = StopAndWait(
        op_type=OP_TYPE_UPLOAD,
        server_host=args.host,
        server_port=args.port
        ) if args.protocol == STOP_AND_WAIT else None

    client = Client(protocol_choice)
    client.upload_file(args.src, args.name)

if __name__ == "__main__":
    main()