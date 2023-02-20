from dataclasses import dataclass
from typing import List

import dns.name
import dns.rdataclass
import dns.rdatatype
import dns.rrset
import dns.update
import dns.zonefile
import voluptuous as vol
import yaml
from voluptuous.humanize import validate_with_humanized_errors

DOMAIN_NAME = dns.name.from_text

RESOURCE_RECORDS = lambda rrs: dns.zonefile.read_rrsets(
    "\n".join(rrs), ttl=0, rdclass=dns.rdataclass.IN
)

RESOURCE_RECORDS_LIST = vol.All([str], RESOURCE_RECORDS)

CR_SCHEMA = vol.Schema(
    {
        vol.Required("zone"): DOMAIN_NAME,
        vol.Required("change"): DOMAIN_NAME,
        vol.Optional("ttl"): vol.All(int, vol.Range(min=0)),
        vol.Required("from"): RESOURCE_RECORDS_LIST,
        vol.Required("to"): RESOURCE_RECORDS_LIST,
    }
)

DEFAULT_TTL = 86400

ALLOWED_RDATATYPES = {
    dns.rdatatype.NS,
    dns.rdatatype.A,
    dns.rdatatype.AAAA,
}


class InvalidChangeError(ValueError):
    pass


class SuperflousGlueError(ValueError):
    pass


class MissingGlueError(ValueError):
    pass


@dataclass(frozen=True)
class ChangeRequest:
    zone: dns.name.Name
    change: dns.name.Name
    ttl: int
    from_rrsets: List[dns.rrset.RRset]
    to_rrsets: List[dns.rrset.RRset]

    def validate(self) -> None:
        if not self.change.is_subdomain(self.zone):
            raise ValueError("{self.change} is not a subdomain of {self.zone}")
        self.validate_rrsets(self.from_rrsets)
        self.validate_rrsets(self.to_rrsets)

    def validate_rrsets(self, rrsets: List[dns.rrset.RRset]) -> None:
        """Ensure a RRset change set is valid"""

        # check types
        for rrset in rrsets:
            if rrset.rdclass != dns.rdataclass.IN:
                raise ValueError("rdataclass")
            if rrset.rdtype not in ALLOWED_RDATATYPES:
                raise ValueError("rdatatype")

        # check nameservers
        nameservers = set()
        for rrset in rrsets:
            if rrset.rdtype == dns.rdatatype.NS:
                if rrset.name != self.change:
                    raise InvalidChangeError(f"Out of change NS: {rrset.name}")
                nameservers.update([rdata.target for rdata in rrset])

        # check for superflous glue
        glue = set()
        for rrset in rrsets:
            if rrset.rdtype == dns.rdatatype.A or rrset.rdtype == dns.rdatatype.AAAA:
                if rrset.name not in nameservers:
                    raise SuperflousGlueError(f"Superflous glue: {rrset.name}")
                glue.add(rrset.name)

        # check for missing glue
        for rrset in rrsets:
            if rrset.rdtype == dns.rdatatype.NS:
                for target in [rdata.target for rdata in rrset]:
                    if target not in glue and target.is_subdomain(self.change):
                        raise MissingGlueError(f"Missing glue for {target}")

    @classmethod
    def from_yaml(cls, yaml_str: str):
        data = validate_with_humanized_errors(yaml.safe_load(yaml_str), CR_SCHEMA)
        zone = data["zone"]
        change = data["change"]
        ttl = data.get("ttl", DEFAULT_TTL)
        from_rrsets = data["from"]
        to_rrsets = data["to"]
        res = cls(
            zone=zone,
            change=change,
            ttl=ttl,
            from_rrsets=from_rrsets,
            to_rrsets=to_rrsets,
        )
        res.validate()
        return res

    def to_message(self) -> dns.update.UpdateMessage:
        """Return CR as DDNS message"""

        res = dns.update.UpdateMessage(self.zone)

        for rrset in self.from_rrsets:
            res.present(rrset.name, rrset)
            if rrset not in self.to_rrsets:
                res.delete(rrset.name, rrset)

        for rrset in self.to_rrsets:
            rrset.ttl = self.ttl
            if rrset not in self.from_rrsets:
                res.add(rrset.name, rrset)

        return res

    def to_nsupdate(self) -> str:
        """Return CR as nsupdate instructions"""

        res = []
        res.append(f"zone {self.zone}")

        for rrset in self.from_rrsets:
            for rdata in rrset:
                rdclass = dns.rdataclass.to_text(rrset.rdclass)
                rdtype = dns.rdatatype.to_text(rrset.rdtype)
                res.append(f"prereq yxrrset {rrset.name} {rdclass} {rdtype} {rdata}")

        for rrset in self.from_rrsets:
            if rrset not in self.to_rrsets:
                for rdata in rrset:
                    rdclass = dns.rdataclass.to_text(rrset.rdclass)
                    rdtype = dns.rdatatype.to_text(rrset.rdtype)
                    res.append(f"update delete {rrset.name} {rdclass} {rdtype} {rdata}")

        for rrset in self.to_rrsets:
            rrset.ttl = self.ttl
            if rrset not in self.from_rrsets:
                for rdata in rrset:
                    rdclass = dns.rdataclass.to_text(rrset.rdclass)
                    rdtype = dns.rdatatype.to_text(rrset.rdtype)
                    res.append(
                        f"update add {rrset.name} {rrset.ttl} {rdclass} {rdtype} {rdata}"
                    )

        return "\n".join(res)
