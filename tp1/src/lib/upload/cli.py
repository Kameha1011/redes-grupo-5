import argparse
from ..common.cli import set_connnection_args, set_logger_args, set_protocol, set_file_name

def cli():
    parser = argparse.ArgumentParser(
        prog="upload", 
        description="A client to upload files to a server.",
        usage='%(prog)s [ -h ] [ -v | -q ] [ -H ADDR ] [ -p PORT ] [ -s FILEPATH ] [ -n FILENAME ] [ -r protocol ]')
    set_connnection_args(parser)
    set_logger_args(parser)
    set_protocol(parser)
    set_file_name(parser)
    parser.add_argument("-s", "--src", help="source file path", required=True)
    return parser.parse_args()