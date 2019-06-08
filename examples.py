from PyQt5.QtCore import QSize, Qt, QPoint
from PyQt5.Qt import QApplication
from PyQt5.QtWidgets import QWidget, QLineEdit, QLabel, QPushButton, QComboBox
import logging, sys

from adjustableWidget import AdjustableMixin, DragButtons, AdjustModes, ImgAdjustable, widget_images

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


class DeleteableMixin():
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def keyPressEvent(self, QKeyEvent):
        if QKeyEvent.key() == Qt.Key_Delete:
            self.deleteLater()
        else:
            super(type(self), self).keyPressEvent(QKeyEvent)


class Button(QPushButton, AdjustableMixin, DeleteableMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clicked.connect(self.showClick)

    def showClick(self):
        logging.info(self.name + ':Button Clicked')


class EditBox(QLineEdit, AdjustableMixin):
    def __init__(self, parent=None, **kwargs):
        aArgs = AdjustableMixin.popArgs(kwargs)
        super().__init__(parent, **kwargs)
        aArgs['defaultCursor'] = Qt.IBeamCursor
        AdjustableMixin.__init__(self, **aArgs)


class Label(QLabel, AdjustableMixin):
    # pass
    def __init__(self, parent=None, *args, **kwargs):
        aArgs = AdjustableMixin.popArgs(kwargs)
        super().__init__(parent, **kwargs)
        AdjustableMixin.__init__(self, **aArgs)


class Combo(QComboBox, AdjustableMixin, DeleteableMixin):
    def __init__(self, parent=None, **kwargs):
        aArgs = AdjustableMixin.popArgs(kwargs)
        super().__init__(parent, **kwargs)
        AdjustableMixin.__init__(self, **aArgs)

        self.addItems(['RClick']+[*'1234567890'])


class Window(QWidget, AdjustableMixin):
    def __init__(self, parent=None, **kwargs):
        aArgs = AdjustableMixin.popArgs(kwargs)
        super().__init__(parent, **kwargs)
        AdjustableMixin.__init__(self, **aArgs)


if __name__ == '__main__':
    app = QApplication([])

    win = Window(adjustButtons=[DragButtons.MID, DragButtons.SHIFT], objectName='win')
    win.setGeometry(200,200,400,500)
    QLabel(parent=win, text="Shift+MidClick").move(100,200)

    E = EditBox(win, adjustButtons=DragButtons.MID, objectName='E', pos=QPoint(50,100), text='MidClick')
    E.setMinimumSize(QSize(50,20))

    B = Button(win, objectName='B', adjustButtons=[DragButtons.RIGHT, DragButtons.SHIFT],
               text='Shift+RClick', size=QSize(100, 80))

    L = Label(B, objectName='L', adjustButtons=[DragButtons.RIGHT, DragButtons.CTRL],
              text='Ctrl+RClick')
    L.setFrameStyle(1)

    C = Combo(E, adjustButtons=DragButtons.RIGHT, objectName='C', pos=QPoint(72, 0), size=QSize(70, 25),
              allowedAdjustments=AdjustModes.ANCHOR_TOP)

    I = ImgAdjustable(win, allowedAdjustments=AdjustModes.ANCHOR_BOTTOM, img=widget_images['arrow_red'],
                      size=QSize(100, 150), pos=QPoint(100, 250), objectName='I')
    I.setMaximumSize(QSize(300, 300))
    I.setMinimumSize(10, 20)
    I.setFrameStyle(1)

    win.show()
    app.exec_()
