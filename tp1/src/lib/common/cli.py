import argparse
from ..constants import SELECTIVE_REPEAT, GO_BACK_N

def set_logger_args(parser: argparse.ArgumentParser):
    logger_level = parser.add_mutually_exclusive_group()
    logger_level.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
    logger_level.add_argument("-q", "--quiet", help="decrease output verbosity", action="store_true")
    
def set_connnection_args(parser: argparse.ArgumentParser):
    parser.add_argument("-H", "--host", help="service IP address", required=True)
    parser.add_argument("-p", "--port", help="service port", type=int, required=True)
    
def set_protocol(parser: argparse.ArgumentParser):
    parser.add_argument(
                    "-r", 
                    "--protocol", 
                    help="error recovery protocol: selective_repeat | go_back_n",
                    choices=[SELECTIVE_REPEAT, GO_BACK_N],
                    default=SELECTIVE_REPEAT)
    
def set_file_name(parser: argparse.ArgumentParser):
    parser.add_argument("-n", "--name", help="file name")