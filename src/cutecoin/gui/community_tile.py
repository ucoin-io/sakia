"""
@author: inso
"""

from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout, QLayout, QPushButton
from PyQt5.QtGui import QPalette
from PyQt5.QtCore import QEvent, QSize, pyqtSignal


class CommunityTile(QFrame):
    clicked = pyqtSignal()

    def __init__(self, parent, app, community):
        super().__init__(parent)
        self.app = app
        self.community = community
        self.text_label = QLabel()
        self.setLayout(QVBoxLayout())
        self.layout().setSizeConstraint(QLayout.SetFixedSize)
        self.layout().addWidget(self.text_label)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.refresh()

    def sizeHint(self):
        return QSize(250, 250)

    def refresh(self):
        current_block = self.community.get_block(self.community.network.latest_block_number)
        status = self.tr("Member") if self.app.current_account.pubkey in self.community.members_pubkeys() \
            else self.tr("Non-Member")
        description = """<html>
        <body>
        <p>
        <span style=" font-size:16pt; font-weight:600;">{currency}</span>
        </p>
        <p>{nb_members} {members_label}</p>
        <p><span style=" font-weight:600;">{monetary_mass_label}</span> : {monetary_mass}</p>
        <p><span style=" font-weight:600;">{status_label}</span> : {status}</p>
        <p><span style=" font-weight:600;">{balance_label}</span> : {balance}</p>
        </body>
        </html>""".format(currency=self.community.currency,
                          nb_members=len(self.community.members_pubkeys()),
                          members_label=self.tr("members"),
                          monetary_mass_label=self.tr("Monetary mass"),
                          monetary_mass=current_block['monetaryMass'],
                          status_label=self.tr("Status"),
                          status=status,
                          balance_label=self.tr("Balance"),
                          balance=self.app.current_account.amount(self.community))
        self.text_label.setText(description)

    def mousePressEvent(self, event):
        self.clicked.emit()
        return super().mousePressEvent(event)

    def enterEvent(self, event):
        self.setStyleSheet("color: rgb(0, 115, 173);")
        return super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet("")
        return super().leaveEvent(event)