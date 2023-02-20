import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path, PosixPath
from typing import Dict, Optional, Union

from ddnsmulti.change_request import ChangeRequest


@dataclass
class ChangeRequestQueueEntry:
    filename: str
    fingerprint: str
    cr: ChangeRequest
    yaml_str: str
    created: float = field(default_factory=time.time)
    nameservers: Dict[str, float] = field(default_factory=dict)

    @classmethod
    def from_file(cls, filename: Union[str, PosixPath]):
        if isinstance(filename, str):
            filename = Path(filename)
        with open(filename, "rb") as input_file:
            raw_contents = input_file.read()
            fingerprint = hashlib.sha256(raw_contents).hexdigest()
            yaml_str = raw_contents.decode()
        cr = ChangeRequest.from_yaml(yaml_str)
        return cls(
            cr=cr,
            yaml_str=yaml_str,
            filename=filename.parts[-1],
            fingerprint=fingerprint,
            nameservers={},
        )

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            filename=data["filename"],
            fingerprint=data["fingerprint"],
            cr=ChangeRequest.from_yaml(data["payload"]),
            yaml_str=data["payload"],
            created=data["created"],
            nameservers=data["nameservers"],
        )

    def as_dict(self) -> dict:
        return {
            "filename": self.filename,
            "fingerprint": self.fingerprint,
            "payload": self.yaml_str,
            "created": self.created,
            "nameservers": self.nameservers,
        }

    def is_complete(self) -> bool:
        """Return Tue if all nameservers has a timestamp"""
        return all([v is not None for v in self.nameservers.values()])

    def set_nameserver_incomplete(self, address: str):
        self.nameservers[address] = None

    def set_nameserver_complete(self, address: str):
        self.nameservers[address] = time.time()


class ChangeRequestQueue:
    def __init__(self, queue_directory: str, index: Optional[str] = None) -> None:
        self.queue_directory = Path(queue_directory)
        self.index_filename = index
        self.queue = None
        self.files = set()
        self._current_index = None

    def __iter__(self):
        return self.queue.__iter__()

    def __getitem__(self, key):
        return self.queue[key]

    def __setitem__(self, key, value):
        self.queue[key] = value

    def __len__(self) -> int:
        return len(self.queue)

    def load_index(self):
        try:
            with open(self.index_filename) as idx:
                index_dict = json.load(idx)
                self.queue = [
                    ChangeRequestQueueEntry.from_dict(v) for v in index_dict["queue"]
                ]
                self.files = set([qe.filename for qe in self.queue])
        except FileNotFoundError:
            self.queue = []
            self.files = set()

    def save_index(self):
        if self.queue is None:
            raise ValueError("No queue")
        if self.index_filename is None:
            raise ValueError("No index defined")
        with open(self.index_filename, "wt") as idx:
            json.dump(self.as_dict(), idx, indent=4)

    def get_files(self):
        return [
            f
            for f in os.listdir(self.queue_directory)
            if os.path.isfile(os.path.join(self.queue_directory, f))
            and f.endswith(".yaml")
        ]

    def as_dict(self) -> dict:
        return {"queue": [qe.as_dict() for qe in self.queue or []]}

    def update_queue(self):
        if self.queue is None:
            self.queue = []
        for f in self.get_files():
            if f not in self.files:
                if self.index_filename:
                    logging.info("Adding %s to index", f)
                else:
                    logging.info("Reading %s", f)
                self.queue.append(
                    ChangeRequestQueueEntry.from_file(self.queue_directory / f)
                )
            else:
                logging.debug("Skip %s, already in index", f)
