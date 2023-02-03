# DNS Updater Utility

`ddnsmulti` wil read dynamic update requests, formatted as YAML, from a queue directory and ensure that all updates are sent to a set of authoritative nameservers. It will keep track of what requests has been accepted to what nameserver and retransit any pending updates.

In addition to the update requests, `ddnsmulti` will keep an JSON-based index  in the queue directory. The index contains all pending transactions and their status.


## Configuration


### Configuration File

Example configuration file:

    queuedir: queue
    index: index.json
    
    nameservers:
      - address: 10.0.0.1
        tsig:
          name: test-20230201.
          key: BA3V2qaseslfYlJ3+XGQwKgXPprlshGnJcFN9NxapNg=
          alg: hmac-sha256
      - address: 10.0.0.2
        tsig:
          name: test-20230201.
          key: BA3V2qaseslfYlJ3+XGQwKgXPprlshGnJcFN9NxapNg=
          alg: hmac-sha256


### Updates

Example updates file:

    change: a.example.com
    
    ttl: 86400
    
    from:
      - "a.example.com. NS ns1.a.example.com"
      - "a.example.com. NS ns2.a.example.com"
      - "a.example.com. NS ns2.b.example.com"
      - "ns1.a.example.com A 10.0.0.1"
      - "ns2.a.example.com A 10.0.0.2"
    
    to:
      - "a.example.com. NS ns1.a.example.com"
      - "a.example.com. NS ns4.a.example.com"
      - "a.example.com. NS ns2.b.example.com"
      - "ns1.a.example.com A 10.0.0.1"
      - "ns4.a.example.com A 10.0.0.2"
      - "ns4.a.example.com AAAA 2001:67c:394:15::4"
