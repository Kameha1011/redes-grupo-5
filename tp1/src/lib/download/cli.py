import argparse
from ..common.cli import set_logger_args, set_connnection_args, set_protocol, set_file_name

def cli():
    parser = argparse.ArgumentParser(
        prog="download", 
        description="A client to download previously uploaded files from a server.",
        usage='%(prog)s [ -h ] [ -v | -q ] [ -H ADDR ] [ -p PORT ] [ -d FILEPATH ] [ -n FILENAME ] [ -r protocol ]')
    set_connnection_args(parser)
    set_logger_args(parser)
    set_protocol(parser)
    set_file_name(parser)
    parser.add_argument("-d", "--dst", help="dest file path", required=True)
    return parser.parse_args()
