from lib.common.Client import Client
from lib.upload.cli import cli
from lib.constants import SELECTIVE_REPEAT, STOP_AND_WAIT_PROTOCOL, SELECTIVE_REPEAT_PROTOCOL

def main():
    args = cli()
    client = Client(args.host, args.port)
    # client.send_message("Holaa soy upload".encode())
    # client.wait_response()

    protocol_choice = SELECTIVE_REPEAT_PROTOCOL if args.protocol == SELECTIVE_REPEAT else STOP_AND_WAIT_PROTOCOL

    client.upload_file(args.src, args.name, protocol_choice)
    client.close()

if __name__ == "__main__":
    main()