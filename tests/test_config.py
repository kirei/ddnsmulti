import unittest

from ddnsmulti.config import UpdaterConfig

CONFIG_EXAMPLE = """
index: index.json
queuedir: /tmp

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
"""


class TestConfig(unittest.TestCase):
    def test_validate(self):
        _ = UpdaterConfig.from_yaml(CONFIG_EXAMPLE)


if __name__ == "__main__":
    unittest.main()
