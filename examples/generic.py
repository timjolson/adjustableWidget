from PyQt5.QtCore import QPoint, QSize
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QLineEdit, QLabel, QPushButton, QComboBox
from PyQt5.Qt import QApplication

import logging, sys

from adjustableWidget import DraggableWidget, AdjustableWidget, DragButtons

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


class DeleteableWidget():
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def keyPressEvent(self, QKeyEvent):
        if QKeyEvent.key() == Qt.Key_Delete:
            self.deleteLater()
        else:
            super(type(self), self).keyPressEvent(QKeyEvent)

class Button(QPushButton, DraggableWidget, DeleteableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clicked.connect(self.showClick)

    def showClick(self):
        logging.info(self.name + 'Button Clicked')

class EditBox(QLineEdit, AdjustableWidget):
    pass

class Label(QLabel, DeleteableWidget, AdjustableWidget):
    def mouseReleaseEvent(self, event):
        if self.dragStartPos:  # we were dragging
            moved = self.pos() - self.dragStartPos

            if moved.manhattanLength() > 2:
                event.ignore()
                logging.debug(f"{self.name}moved from {(self.dragStartPos.x(), self.dragStartPos.y())}" +
                 f" to {(self.pos().x(), self.pos().y())}")

            self.dragStartPos = None
        else:
            super(type(self), self).mouseReleaseEvent(event)
        event.accept()

class Combo(QComboBox, AdjustableWidget):
    def __init__(self, parent=None, **kwargs):
        AdjustableWidget.__init__(self, parent, **kwargs)
        self.addItems([*'1234567890'])


app = QApplication([])

# win = QWidget()
win = AdjustableWidget(buttons=[DragButtons.MID, DragButtons.SHIFT], objectName='win')
win.setGeometry(200,200,400,500)


E = EditBox(win, buttons=DragButtons.MID, objectName='E')
E.move(50,100)
E.setMinimumSize(QSize(50,20))
# e.setMaximumSize(QSize(150,200))
# e.setFixedSize(QSize(50,20))
# e.setFixedHeight(20)
# e.setFixedWidth(80)

B = Button(win, objectName='B', buttons=[DragButtons.RIGHT, DragButtons.SHIFT])
B.setText('Button Object')
B.resize(100, 80)


L = Label(B, objectName='L', buttons=[DragButtons.RIGHT, DragButtons.CTRL])
L.setText('Label Object')
L.setFrameStyle(1)


C = Combo(E, buttons=DragButtons.RIGHT, objectName='C')
C.move(80,0)


# TODO: debug combo box size jump

win.show()
app.exec_()
