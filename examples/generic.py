from PyQt5.QtCore import QPoint, QSize
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QLineEdit, QLabel, QPushButton, QComboBox
from PyQt5.Qt import QApplication

import logging, sys

from adjustableWidget import DraggableWidget, AdjustableWidget, DragButtons

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


class DeleteableWidget():
    def __init__(self, *args, **kwargs):
        print('deletable init')
        print(kwargs)
        super().__init__(*args, **kwargs)

    def keyPressEvent(self, QKeyEvent):
        if QKeyEvent.key() == Qt.Key_Delete:
            self.deleteLater()
        else:
            super(type(self), self).keyPressEvent(QKeyEvent)

class Button(QPushButton, DeleteableWidget, DraggableWidget):
# class Button(QPushButton, DraggableWidget, DeleteableWidget):
    # keyPressEvent = deleteEvent
    pass

class EditBox(QLineEdit, AdjustableWidget):
    pass

class Label(QLabel, DeleteableWidget, AdjustableWidget):
    # keyPressEvent = deleteEvent
    pass

class Combo(QComboBox, AdjustableWidget):
    def __init__(self, parent=None, **kwargs):
        print('combo init')
        print(kwargs)
        AdjustableWidget.__init__(self, parent, **kwargs)
        self.addItems([*'1234567890'])


app = QApplication([])

# win = QWidget()
win = AdjustableWidget(button=DragButtons.MID, objectName='win')
win.setGeometry(200,200,400,500)

print('adjustable done')


E = EditBox(win, button=DragButtons.MID, objectName='E')
E.move(50,100)
E.setMinimumSize(QSize(50,20))
# e.setMaximumSize(QSize(150,200))
# e.setFixedSize(QSize(50,20))
# e.setFixedHeight(20)
# e.setFixedWidth(80)

print('editbox done')

B = Button(win, objectName='B')
B.setText('Button Object')
B.resize(100, 80)

print('button done')

L = Label(B, objectName='L')
L.setText('Label Object')
L.setFrameStyle(1)

print('label done')

C = Combo(E, button=DragButtons.RIGHT, objectName='C')
C.move(80,0)

print('combo done')

# TODO: debug combo box size jump

win.show()
app.exec_()
