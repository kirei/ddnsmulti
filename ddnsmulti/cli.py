import argparse
import logging

from .change_request import ChangeRequest  # noqa
from .config import UpdaterConfig
from .queue import ChangeRequestQueue

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_FILE = "ddnsmulti.yaml"


def show_queue(config: dict, args: argparse.Namespace):
    queue = ChangeRequestQueue(
        queue_directory=config.queue_directory, index=config.index
    )
    queue.load_index()
    for qe in queue:
        print(f"- {qe.filename} ({qe.fingerprint})")


def update_queue(config: dict, args: argparse.Namespace):
    queue = ChangeRequestQueue(
        queue_directory=config.queue_directory, index=config.index
    )
    queue.load_index()
    queue.update_queue()
    queue.save_index()


def send_dns_updates(config: dict, args: argparse.Namespace):
    pass


def main() -> None:
    """Main function"""

    parser = argparse.ArgumentParser(description="DNS Updater")
    parser.add_argument(
        "--config",
        metavar="config",
        default=DEFAULT_CONFIG_FILE,
        help="Configuration file",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debugging")

    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_show = subparsers.add_parser("show", help="Show queue")
    parser_show.set_defaults(func=show_queue)

    parser_update = subparsers.add_parser("update", help="Update queue")
    parser_update.set_defaults(func=update_queue)

    parser_send = subparsers.add_parser("send", help="Send DNS updates")
    parser_send.set_defaults(func=send_dns_updates)

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    config = UpdaterConfig.from_file(args.config)

    args.func(config, args)


if __name__ == "__main__":
    main()
