import logging

from PyQt5.QtCore import QObject
from sakia.errors import NoPeerAvailable
from sakia.constants import ROOT_SERVERS
from duniterpy.api import errors
from .model import IdentityModel
from .view import IdentityView

from sakia.decorators import asyncify
from sakia.gui.sub.certification.controller import CertificationController
from sakia.gui.sub.password_input import PasswordInputController
from sakia.gui.widgets import toast
from sakia.gui.widgets.dialogs import QAsyncMessageBox, QMessageBox


class IdentityController(QObject):
    """
    The informations component
    """

    def __init__(self, parent, view, model, certification):
        """
        Constructor of the informations component

        :param sakia.gui.informations.view.InformationsView view: the view
        :param sakia.gui.informations.model.InformationsModel model: the model
        """
        super().__init__(parent)
        self.view = view
        self.model = model
        self.certification = certification
        self._logger = logging.getLogger('sakia')
        self.view.button_membership.clicked.connect(self.send_join_demand)

    @classmethod
    def create(cls, parent, app, connection, blockchain_service, identities_service, sources_service):
        """

        :param parent:
        :param sakia.app.Application app:
        :param connection:
        :param blockchain_service:
        :param identities_service:
        :param sources_service:
        :return:
        """
        certification = CertificationController.integrate_to_main_view(None, app, connection)
        view = IdentityView(parent.view, certification.view)
        model = IdentityModel(None, app, connection, blockchain_service, identities_service, sources_service)
        identity = cls(parent, view, model, certification)
        certification.accepted.connect(view.clear)
        certification.rejected.connect(view.clear)
        identity.refresh_localized_data()
        return identity

    @asyncify
    async def init_view_text(self):
        """
        Initialization of text in informations view
        """
        params = self.model.parameters()
        if params:
            self.view.set_money_text(params, ROOT_SERVERS[self.model.connection.currency]["display"])
            self.refresh_localized_data()

    def handle_identity_change(self, identity):
        if identity.pubkey == self.model.connection.pubkey and identity.uid == self.model.connection.uid:
            self.refresh_localized_data()

    def refresh_localized_data(self):
        """
        Refresh localized data in view
        """
        localized_data = self.model.get_localized_data()
        try:
            simple_data = self.model.get_identity_data()
            all_data = {**simple_data, **localized_data}
            self.view.set_simple_informations(all_data, IdentityView.CommunityState.READY)
        except NoPeerAvailable as e:
            self._logger.debug(str(e))
            self.view.set_simple_informations(all_data, IdentityView.CommunityState.OFFLINE)
        except errors.DuniterError as e:
            if e.ucode == errors.BLOCK_NOT_FOUND:
                self.view.set_simple_informations(all_data, IdentityView.CommunityState.NOT_INIT)
            else:
                self._logger.debug(str(e))

    @asyncify
    async def send_join_demand(self, checked=False):
        if not self.model.connection:
            return
        if not self.model.get_identity_data()["membership_state"]:
            result = await self.view.licence_dialog(self.model.connection.currency,
                                                    self.model.parameters())
            if result == QMessageBox.No:
                return

        secret_key, password = await PasswordInputController.open_dialog(self, self.model.connection)
        if not password or not secret_key:
            return
        result = await self.model.send_join(secret_key, password)
        if result[0]:
            if self.model.notifications():
                toast.display(self.tr("Membership"), self.tr("Success sending Membership demand"))
            else:
                await QAsyncMessageBox.information(self.view, self.tr("Membership"),
                                                        self.tr("Success sending Membership demand"))
        else:
            if self.model.notifications():
                toast.display(self.tr("Membership"), result[1])
            else:
                await QAsyncMessageBox.critical(self.view, self.tr("Membership"),
                                                        result[1])
