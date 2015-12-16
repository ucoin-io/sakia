import sys
import unittest
import asyncio
import quamash
import logging
import time
from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import QLocale, Qt, QPoint
from PyQt5.QtTest import QTest
from ucoinpy.api import bma
from ucoinpy.api.bma import API
from sakia.tests.mocks.monkeypatch import pretender_reversed
from sakia.tests.mocks.bma import nice_blockchain
from sakia.core.registry.identities import IdentitiesRegistry
from sakia.gui.identities_tab import IdentitiesTabWidget
from sakia.gui.password_asker import PasswordAskerDialog
from sakia.core.app import Application
from sakia.core import Account, Community, Wallet
from sakia.core.net import Network, Node
from ucoinpy.documents.peer import BMAEndpoint
from sakia.core.net.api.bma.access import BmaAccess
from sakia.tests import QuamashTest


class TestIdentitiesTable(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        QLocale.setDefault(QLocale("en_GB"))
        self.identities_registry = IdentitiesRegistry()

        self.application = Application(self.qapplication, self.lp, self.identities_registry)
        self.application.preferences['notifications'] = False

        self.endpoint = BMAEndpoint("", "127.0.0.1", "", 50000)
        self.node = Node("test_currency", [self.endpoint],
                         "", "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk",
                         None, Node.ONLINE,
                         time.time(), {}, "ucoin", "0.14.0", 0)
        self.network = Network.create(self.node)
        self.bma_access = BmaAccess.create(self.network)
        self.community = Community("test_currency", self.network, self.bma_access)

        self.wallet = Wallet(0, "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                             "Wallet 1", self.identities_registry)

        # Salt/password : "testsakia/testsakia"
        # Pubkey : 7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ
        self.account = Account("testsakia", "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                               "john", [self.community], [self.wallet], [], self.identities_registry)

        self.password_asker = PasswordAskerDialog(self.account)
        self.password_asker.password = "testsakia"
        self.password_asker.remember = True

    def tearDown(self):
        self.tearDownQuamash()

    def test_search_identity_found(self):
        mock = nice_blockchain.get_mock()
        time.sleep(2)
        logging.debug(mock.pretend_url)
        API.reverse_url = pretender_reversed(mock.pretend_url)
        identities_tab = IdentitiesTabWidget(self.application)
        identities_tab.change_account(self.account, self.password_asker)
        identities_tab.change_community(self.community)
        future = asyncio.Future()

        def open_widget():
            identities_tab.show()
            return future

        def close_dialog():
            if identities_tab.isVisible():
                identities_tab.close()
            future.set_result(True)

        async     def exec_test():
            await asyncio.sleep(2)
            urls = [mock.get_request(i).url for i in range(0, 7)]
            self.assertTrue('/wot/certifiers-of/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ' in urls,
                            msg="Not found in {0}".format(urls))
            self.assertTrue('/wot/lookup/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ' in urls,
                            msg="Not found in {0}".format(urls))
            self.assertTrue('/wot/certified-by/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ' in urls,
                            msg="Not found in {0}".format(urls))


            # requests 1 to 3 are for getting certifiers-of and certified-by
            # on john, + a lookup

            QTest.keyClicks(identities_tab.edit_textsearch, "doe")
            QTest.mouseClick(identities_tab.button_search, Qt.LeftButton)
            await asyncio.sleep(2)
            req = 7

            self.assertEqual(mock.get_request(req).method, 'GET')
            self.assertEqual(mock.get_request(req).url,
                             '/blockchain/memberships/FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn')
            req += 1

            self.assertEqual(identities_tab.table_identities.model().rowCount(), 1)
            await asyncio.sleep(2)
            self.lp.call_soon(close_dialog)

        asyncio.ensure_future(exec_test())
        self.lp.call_later(15, close_dialog)
        self.lp.run_until_complete(open_widget())
        mock.delete_mock()

if __name__ == '__main__':
    logging.basicConfig( stream=sys.stderr )
    logging.getLogger().setLevel( logging.DEBUG )
    unittest.main()