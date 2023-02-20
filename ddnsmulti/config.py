import base64
import ipaddress
from dataclasses import dataclass
from typing import List, Optional

import dns.name
import dns.tsig
import voluptuous as vol
import yaml
from voluptuous.humanize import validate_with_humanized_errors

DOMAIN_NAME = dns.name.from_text

TSIG_ALGORITHMS = {
    "hmac-sha1",
    "hmac-sha224",
    "hmac-sha256",
    "hmac-sha256-128",
    "hmac-sha384",
    "hmac-sha384-192",
    "hmac-sha512",
    "hmac-sha512-256",
}

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required("queuedir"): vol.IsDir(),
        vol.Optional("index"): str,
        vol.Required("nameservers"): [
            vol.Schema(
                {
                    vol.Required("address"): ipaddress.ip_address,
                    vol.Optional("port", default=53): int,
                    vol.Optional("tsig"): vol.Schema(
                        {
                            vol.Required("name"): DOMAIN_NAME,
                            vol.Required("key"): lambda k: base64.b64decode(k.encode()),
                            vol.Required("alg"): vol.Any(*TSIG_ALGORITHMS),
                        }
                    ),
                }
            )
        ],
    }
)


@dataclass(frozen=True)
class UpdaterConfig:
    index: Optional[str]
    queue_directory: str
    nameservers: List[dict]

    @classmethod
    def from_yaml(cls, yaml_str: str):
        config = validate_with_humanized_errors(yaml.safe_load(yaml_str), CONFIG_SCHEMA)
        return cls(
            index=config.get("index"),
            queue_directory=config["queuedir"],
            nameservers=config["nameservers"],
        )

    @classmethod
    def from_file(cls, filename: str):
        with open(filename) as input_file:
            return cls.from_yaml(input_file.read())
