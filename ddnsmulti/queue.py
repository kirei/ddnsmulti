import json
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

from ddnsmulti.change_request import ChangeRequest


@dataclass(frozen=True)
class ChangeRequestQueueEntry:
    cr: ChangeRequest
    yaml_str: str
    created: float = field(default_factory=time.time)
    nameservers: Dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_file(cls, filename: str):
        with open(filename) as input_file:
            yaml_str = input_file.read()
        cr = ChangeRequest.from_yaml(yaml_str)
        return cls(cr=cr, yaml_str=yaml_str)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            cr=ChangeRequest.from_yaml(data["cr"]),
            yaml_str=data["cr"],
            created=data["created"],
            nameservers=data["nameservers"],
        )

    def as_dict(self) -> dict:
        return {
            "cr": self.yaml_str,
            "created": self.created,
            "nameservers": self.nameservers,
        }


class ChangeRequestQueue:
    def __init__(self, directory: str, index: Optional[str] = None) -> None:
        self.queue_directory = Path(directory)
        self.index_filename = index or self.queue_directory / "index.json"
        self.index = None

    def load_index(self):
        try:
            with open(self.index_filename) as idx:
                index_dict = json.load(idx)
                self.index = {
                    k: ChangeRequestQueueEntry.from_dict(v)
                    for k, v in index_dict.items()
                }
        except FileNotFoundError:
            self.index = {}

    def save_index(self):
        if self.index is None:
            raise ValueError("No index")
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
        return {k: v.as_dict() for k, v in self.index.items()}

    def update_queue(self):
        for f in self.get_files():
            if f not in self.index:
                logging.info("Adding %s to index", f)
                self.index[f] = ChangeRequestQueueEntry.from_file(
                    self.queue_directory / f
                )
            else:
                logging.debug("Skip %s, already in index", f)
