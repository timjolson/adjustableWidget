from PyQt5 import QtGui
from PyQt5.QtWidgets import QLabel
from adjustableWidget.adjustable_widget import DraggableWidget, AdjustableWidget


class ImgDraggable(QLabel, DraggableWidget):
    def __init__(self, parent=None, img=None, **kwargs):
        super().__init__(parent, **kwargs)

        if img is None:
            self.setFrameStyle(1)

        self.pixmap = QtGui.QPixmap(img)
        self.setPixmap(self.pixmap)

    def resizeEvent(self, QResizeEvent):
        self.setPixmap(self.pixmap.scaled(QResizeEvent.size().width(), QResizeEvent.size().height()))


class ImgAdjustable(QLabel, AdjustableWidget):
    def __init__(self, parent=None, img=None, **kwargs):
        super().__init__(parent, **kwargs)

        if img is None:
            self.setFrameStyle(1)

        self.pixmap = QtGui.QPixmap(img)
        self.setPixmap(self.pixmap)

    def resizeEvent(self, QResizeEvent):
        self.setPixmap(self.pixmap.scaled(QResizeEvent.size().width(), QResizeEvent.size().height()))


__all__ = ['ImgDraggable', 'ImgAdjustable']
