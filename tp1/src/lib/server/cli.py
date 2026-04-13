import argparse
from ..common.cli import set_logger_args,set_connnection_args 

def cli():
    parser = argparse.ArgumentParser(
        prog="start-server", 
        description="A Stop & Wait UDP server that implements Selective Repeat for error recovery, will accept incoming requests to upload files and download previously stored files.",
        usage='%(prog)s [ - h ] [ - v | -q ] [ - H ADDR ] [ - p PORT ] [ - s DIRPATH ]')
    set_connnection_args(parser)
    set_logger_args(parser)
    parser.add_argument("-s", "--storage", help="storage dir path", default="./storage")
    return parser.parse_args()
