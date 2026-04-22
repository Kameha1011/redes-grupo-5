from lib.common.Client import Client
from lib.upload.cli import cli

def main():
    args = cli()
    client = Client(args.host, args.port)
    # client.send_message("Holaa soy upload".encode())
    # client.wait_response()
    client.upload_file(args.src, args.name)
    client.close()

if __name__ == "__main__":
    main()