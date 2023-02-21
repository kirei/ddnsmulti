import argparse
import logging

from .commands import send_all_updates, send_single_update, show_queue, update_queue
from .config import UpdaterConfig

DEFAULT_CONFIG_FILE = "ddnsmulti.yaml"


def main() -> None:
    """Main function"""

    parser = argparse.ArgumentParser(description="DDNS Multi Updater")
    parser.add_argument(
        "--config",
        metavar="config",
        default=DEFAULT_CONFIG_FILE,
        help="Configuration file",
    )
    parser.add_argument(
        "--nsupdate", action="store_true", help="Output nsupdate commands"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debugging")

    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_show = subparsers.add_parser("show-queue", help="Show queue")
    parser_show.set_defaults(func=show_queue)

    parser_update = subparsers.add_parser("update-queue", help="Update queue")
    parser_update.set_defaults(func=update_queue)

    parser_send = subparsers.add_parser("send", help="Send all updates")
    parser_send.set_defaults(func=send_all_updates)

    parser_send = subparsers.add_parser("send-one", help="Send single update")
    parser_send.set_defaults(func=send_single_update)
    parser_send.add_argument("filename", help="Update")

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    config = UpdaterConfig.from_file(args.config)

    return args.func(config, args)


if __name__ == "__main__":
    main()
