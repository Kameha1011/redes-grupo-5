from tp1.src.lib.client.Client import Client
from lib.common.cli import upload_parser
from tp1.src.lib.common.constants import SELECTIVE_REPEAT, STOP_AND_WAIT_PROTOCOL, SELECTIVE_REPEAT_PROTOCOL

def main():
    args = upload_parser()
    client = Client(args.host, args.port)
    # client.send_message("Holaa soy upload".encode())
    # client.wait_response()

    protocol_choice = SELECTIVE_REPEAT_PROTOCOL if args.protocol == SELECTIVE_REPEAT else STOP_AND_WAIT_PROTOCOL

    client.upload_file(args.src, args.name, protocol_choice)
    client.close()

if __name__ == "__main__":
    main()