import unittest
from localshit.components.content_provider import ContentProvider
from localshit.components.ring import Ring
from localshit.components.election import Election

class TestContentProvider(unittest.TestCase):
    def test_jokes(self):
        hosts = Ring("192.168.0.2")
        election = Election(hosts, "192.168.0.2")

        content_provider = ContentProvider(hosts, election)
        content_provider.start()

        quote = content_provider.get_quote('jokes.json')

        print(quote)

        content_provider.stop()
        content_provider.join()

        self.assertIsNotNone(quote)

        