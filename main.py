# ./main.py
import argparse

from dotenv import load_dotenv

from backend.PELServer import Server
from backend.utils.path_utils import get_full_path


def main(host, port, debug):
    server = Server()
    server.run(host, port, debug)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the Flask application.')
    parser.add_argument('--host', type=str, default='localhost', help='The host address to run the server on.')
    parser.add_argument('--port', type=int, default=5000, help='The port number to run the server on.')
    parser.add_argument('--debug', type=bool, default=False, help='Whether to run the server in debug mode.')

    load_dotenv(get_full_path('.env'))

    args = parser.parse_args()
    main(args.host, args.port, args.debug)