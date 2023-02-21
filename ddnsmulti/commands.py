import argparse
import logging

import dns.query
import dns.tsig

from .config import UpdaterConfig
from .queue import ChangeRequestQueue, ChangeRequestQueueEntry

logger = logging.getLogger(__name__)


def show_queue(config: UpdaterConfig, args: argparse.Namespace):
    queue = ChangeRequestQueue(
        queue_directory=config.queue_directory, index=config.index
    )
    if config.index:
        queue.load_index()
    queue.update_queue()
    for qe in queue:
        if qe:
            print(f"- {qe.filename} ({qe.cr.change}) {qe.fingerprint}")


def update_queue(config: UpdaterConfig, args: argparse.Namespace):
    queue = ChangeRequestQueue(
        queue_directory=config.queue_directory, index=config.index
    )
    if not config.index:
        logger.error("No queue configured")
        return -1
    logger.info("Load index")
    queue.load_index()
    logger.info("Update index")
    queue.update_queue()
    queue.save_index()
    logger.info("Save index")


def send_all_updates(config: UpdaterConfig, args: argparse.Namespace):
    queue = ChangeRequestQueue(
        queue_directory=config.queue_directory, index=config.index
    )

    if config.index:
        logger.info("Load index")
        queue.load_index()
    else:
        logger.info("Running without index")
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
            send_queue_entry(config, args, qe)

    if config.index:
        logger.info("Save index")
        queue.save_index()


def send_single_update(config: UpdaterConfig, args: argparse.Namespace):
    qe = ChangeRequestQueueEntry.from_file(args.filename)
    send_queue_entry(config, args, qe)


def send_queue_entry(
    config: UpdaterConfig, args: argparse.Namespace, qe: ChangeRequestQueueEntry
):
    for nameserver in config.nameservers:
        address = str(nameserver["address"])
        if address not in qe.nameservers:
            logger.info(
                "%s (%s) scheduled for update via %s",
                qe.filename,
                qe.cr.change,
                nameserver["address"],
            )
            update = qe.cr.to_message()

            if args.debug:
                print(str(update))

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
                    logger.warning(
                        "%s (%s) not accepted by %s",
                        qe.filename,
                        qe.cr.change,
                        address,
                    )
                else:
                    qe.set_nameserver_complete(address)
                    logger.info(
                        "%s (%s) accepted by %s",
                        qe.filename,
                        qe.cr.change,
                        address,
                    )
            except ConnectionRefusedError:
                qe.set_nameserver_incomplete(address)
                logger.warning(
                    "%s (%s) connection refused by %s",
                    qe.filename,
                    qe.cr.change,
                    address,
                )
        else:
            logger.info("%s already processed, skipped", nameserver["address"])
