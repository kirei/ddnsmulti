import argparse
import logging

from .change_request import ChangeRequest  # noqa
from .config import UpdaterConfig

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_FILE = "dnsupdate.yaml"


def show_update_queue(config: dict, args: argparse.Namespace):
    pass


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

    queue_list = subparsers.add_parser("queue", help="Show update queue")
    queue_list.set_defaults(func=show_update_queue)

    update_list = subparsers.add_parser("update", help="Send DNS updates")
    update_list.set_defaults(func=send_dns_updates)

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    config = UpdaterConfig.from_file(args.config)

    args.func(config, args)


if __name__ == "__main__":
    main()
