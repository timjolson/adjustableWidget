from PyQt5.QtCore import QPoint, QSize
from PyQt5.QtWidgets import QWidget, QLineEdit, QLabel, QPushButton, QComboBox
from PyQt5.Qt import QApplication

import logging, sys

from adjustableWidget import DraggableWidget, AdjustableWidget, DragButtons

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

app = QApplication([])

win = QWidget()
win.setGeometry(200,200,400,500)

class Button(QPushButton, DraggableWidget):
    pass

class EditBox(QLineEdit, AdjustableWidget):
    pass

class Label(QLabel, AdjustableWidget):
    pass

class Combo(QComboBox, AdjustableWidget):
    def __init__(self, parent=None, **kwargs):
        AdjustableWidget.__init__(self, parent, **kwargs)
        self.addItems([*'1234567890'])

e = EditBox(win, button=DragButtons.MID)
e.move(50,100)

B = Button(win)
B.setText('Button Object')
B.resize(100, 80)

L = Label(B)
L.setText('Label Object')
L.setFrameStyle(1)

C = Combo(e, button=DragButtons.RIGHT)
C.move(80,0)

win.show()
app.exec_()
