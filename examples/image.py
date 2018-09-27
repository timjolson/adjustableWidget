from PyQt5.QtCore import QPoint, QSize
from PyQt5.QtWidgets import QWidget
from PyQt5.Qt import QApplication

from imageWidget import widget_images, ImgDraggable, ImgAdjustable
from adjustableWidget import AdjustModes
import logging, sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

app = QApplication([])

win = QWidget()
win.setGeometry(200,200,400,500)


# r = ImgAdjustable(win, img=widget_images['arrow_red'], allowedAdjust=AdjustModes.ANCHOR_BOTTOM_LEFT+AdjustModes.DRAG, size=QSize(150,200), pos=QPoint(50,50))
r = ImgAdjustable(win, allowedAdjust=AdjustModes.ANCHOR_BOTTOM_RIGHT, img=widget_images['arrow_red'], size=QSize(150, 200), pos=QPoint(50, 50))
r.setMaximumSize(QSize(300,300))
r.setObjectName('r')
r.setMinimumSize(10, 20)
r.setFrameStyle(1)

b = ImgDraggable(r, img=widget_images['arrow_blue'], size=QSize(40, 50))
# b.container = QtCore.QRect(50, 50, 200, 300).getRect
# b.container = r.geometry().getRect


win.show()
app.exec_()
