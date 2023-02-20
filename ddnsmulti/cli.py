import argparse
import logging

import dns.query
import dns.tsig

from .change_request import ChangeRequest  # noqa
from .config import UpdaterConfig
from .queue import ChangeRequestQueue

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_FILE = "ddnsmulti.yaml"


def show_queue(config: UpdaterConfig, args: argparse.Namespace):
    queue = ChangeRequestQueue(
        queue_directory=config.queue_directory, index=config.index
    )
    queue.load_index()
    for qe in queue:
        print(f"- {qe.filename} ({qe.fingerprint})")


def update_queue(config: UpdaterConfig, args: argparse.Namespace):
    queue = ChangeRequestQueue(
        queue_directory=config.queue_directory, index=config.index
    )
    queue.load_index()
    queue.update_queue()
    queue.save_index()


def send_dns_updates(config: UpdaterConfig, args: argparse.Namespace):
    queue = ChangeRequestQueue(
        queue_directory=config.queue_directory, index=config.index
    )

    if config.index:
        logging.info("Load index")
        queue.load_index()
    else:
        logging.info("Using raw queue")
        queue.update_queue()

    if args.nsupdate:
        for qe in queue:
            nsupdate = qe.cr.to_nsupdate()
            print(f"; {qe.filename}")
            print(nsupdate)
            print("send")
            print()
    else:
        for qe in queue:
            for nameserver in config.nameservers:
                address = str(nameserver["address"])
                if address not in qe.nameservers:
                    print("Will update", nameserver["address"])
                    update = qe.cr.to_message()

                    if tsig := nameserver.get("tsig"):
                        key = dns.tsig.Key(
                            name=tsig["name"], secret=tsig["key"], algorithm=tsig["alg"]
                        )
                        update.use_tsig(keyring=key)
                    try:
                        response = dns.query.tcp(
                            update, address, port=nameserver["port"], timeout=10
                        )
                        if response.rcode():
                            qe.set_nameserver_incomplete(address)
                            logging.warning(
                                "%s (%s) not accepted by %s",
                                qe.filename,
                                qe.fingerprint,
                                address,
                            )
                        else:
                            qe.set_nameserver_complete(address)
                            logging.info(
                                "%s (%s) accepted by %s",
                                qe.filename,
                                qe.fingerprint,
                                address,
                            )
                    except ConnectionRefusedError:
                        qe.set_nameserver_incomplete(address)
                        logging.warning(
                            "%s (%s) connection refused by %s",
                            qe.filename,
                            qe.fingerprint,
                            address,
                        )
                else:
                    print(nameserver["address"], "skipped, already sent")

    if config.index:
        logging.info("Save index")
        queue.save_index()


def main() -> None:
    """Main function"""

    parser = argparse.ArgumentParser(description="DNS Updater")
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
