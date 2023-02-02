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
        q = ChangeRequestQueue(directory=QUEUEDIR, index=index_filename)
        q.load_index()
        q.update_queue()
        q.save_index()
        q.load_index()
        q.save_index()


if __name__ == "__main__":
    unittest.main()
