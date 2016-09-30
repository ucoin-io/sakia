from enum import Enum

from PyQt5.QtWidgets import QDialog, QFileDialog, QMessageBox

from sakia.decorators import asyncify
from sakia.gui.widgets.dialogs import QAsyncMessageBox
from .revocation_uic import Ui_RevocationDialog


class RevocationView(QDialog, Ui_RevocationDialog):
    """
    Home screen view
    """

    class PublicationMode(Enum):
        ADDRESS = 0
        COMMUNITY = 1

    def __init__(self, parent):
        """
        Constructor
        """
        super().__init__(parent)
        self.setupUi(self)

        self.button_next.setEnabled(False)
        self.button_load.clicked.connect(self.load_from_file)

        self.radio_address.toggled.connect(lambda c: self.publication_mode_changed(RevocationView.PublicationMode.ADDRESS))
        self.radio_community.toggled.connect(lambda c: self.publication_mode_changed(RevocationView.PublicationMode.COMMUNITY))
        self.edit_address.textChanged.connect(self.refresh)
        self.spinbox_port.valueChanged.connect(self.refresh)
        self.combo_community.currentIndexChanged.connect(self.refresh)

    def publication_mode_changed(self, radio):
        self.edit_address.setEnabled(radio == RevocationView.PublicationMode.ADDRESS)
        self.spinbox_port.setEnabled(radio == RevocationView.PublicationMode.ADDRESS)
        self.combo_community.setEnabled(radio == RevocationView.PublicationMode.COMMUNITY)
        self.refresh_revocation_label()

    def refresh_target(self):
        if self.radio_community.isChecked():
            target = self.tr(
                "All nodes of community {name}".format(name=self.combo_community.currentText()))
        elif self.radio_address.isChecked():
            target = self.tr("Address {address}:{port}".format(address=self.edit_address.text(),
                                                               port=self.spinbox_port.value()))
        else:
            target = ""
        self.label_target.setText("""
<h4>Publication address</h4>
<div>{target}</div>
""".format(target=target))

    def select_revocation_file(self):
        """
        Get a revocation file using a file dialog
        :rtype: str
        """
        selected_files = QFileDialog.getOpenFileName(self.widget,
                                    self.tr("Load a revocation file"),
                                    "",
                                    self.tr("All text files (*.txt)"))
        selected_file = selected_files[0]
        return selected_file

    def malformed_file_error(self):
        QMessageBox.critical(self, self.tr("Error loading document"),
                             self.tr("Loaded document is not a revocation document"),
                             buttons=QMessageBox.Ok)

    async def revocation_broadcast_error(self, error):
        await QAsyncMessageBox.critical(self, self.tr("Error broadcasting document"),
                                        error)

    def show_revoked_selfcert(self, selfcert):
        text = self.tr("""
        <div>Identity revoked : {uid} (public key : {pubkey}...)</div>
        <div>Identity signed on block : {timestamp}</div>
            """.format(uid=selfcert.uid,
                       pubkey=selfcert.pubkey[:12],
                       timestamp=selfcert.timestamp))
        self.label_revocation_content.setText(text)

    def set_communities_names(self, names):
        self.combo_community.clear()
        for name in names:
            self.combo_community.addItem(name)
        self.radio_community.setChecked(True)

    def ask_for_confirmation(self):
        answer = QMessageBox.warning(self.widget, self.tr("Revocation"),
                                     self.tr("""<h4>The publication of this document will remove your identity from the network.</h4>
        <li>
            <li> <b>This identity won't be able to join the targeted community anymore.</b> </li>
            <li> <b>This identity won't be able to generate Universal Dividends anymore.</b> </li>
            <li> <b>This identity won't be able to certify individuals anymore.</b> </li>
        </li>
        Please think twice before publishing this document.
        """), QMessageBox.Ok | QMessageBox.Cancel)
        return answer == QMessageBox.Ok

    @asyncify
    async def accept(self):
        await QAsyncMessageBox.information(self.widget, self.tr("Revocation broadcast"),
                                     self.tr("The document was successfully broadcasted."))
        super().accept()
