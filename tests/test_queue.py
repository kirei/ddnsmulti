import logging
import os
import unittest

from ddnsmulti.queue import ChangeRequestQueue

BASEDIR = os.path.abspath(os.path.dirname(__file__))
QUEUEDIR = os.path.join(BASEDIR, "queue")
INDEX = "index.json"


class TestQueue(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.DEBUG)

    def test_queue(self):
        index_filename = os.path.join(QUEUEDIR, INDEX)
        try:
            os.unlink(index_filename)
        except FileNotFoundError:
            pass
        queue = ChangeRequestQueue(queue_directory=QUEUEDIR, index=index_filename)

        queue.load_index()
        queue.update_queue()
        queue.save_index()

        _ = [qe for qe in queue]

        queue.load_index()

        NAMESERVERS = ["10.0.0.1", "10.0.0.2"]
        for qe in queue:
            for n in NAMESERVERS:
                qe.set_nameserver_incomplete(n)
            self.assertFalse(qe.is_complete())
            qe.set_nameserver_complete(NAMESERVERS[0])
            self.assertFalse(qe.is_complete())
            for n in NAMESERVERS:
                qe.set_nameserver_complete(n)
            self.assertTrue(qe.is_complete())

        queue.save_index()


if __name__ == "__main__":
    unittest.main()
