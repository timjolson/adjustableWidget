from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QWIDGETSIZE_MAX, QDesktopWidget, QLabel, QFrame
import logging
import os

from qt_utils import loggableQtName, eventMatchesButtons

widget_images = {}
widget_img_dir = os.path.join(os.path.dirname(__file__), 'arrows')
for img in os.listdir(widget_img_dir):
    if img.endswith('.png'):
        widget_images.update({os.path.basename(img)[:-4]:os.path.join(widget_img_dir, img)})


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class _edges():
    Left = -1
    Right = 1
    Top = -1
    Bottom = 1
    Move = 0
    NONE = 2


class _modes():
    Left = (_edges.Left, _edges.Move)
    Right = (_edges.Right, _edges.Move)
    Top = (_edges.Move, _edges.Top)
    Bottom = (_edges.Move, _edges.Bottom)
    TopLeft = (_edges.Left, _edges.Top)
    TopRight = (_edges.Right, _edges.Top)
    BottomLeft = (_edges.Left, _edges.Bottom)
    BottomRight = (_edges.Right, _edges.Bottom)
    Move = (_edges.Move, _edges.Move)
    NONE = (_edges.NONE, _edges.NONE)


_cursors = {
    _modes.Left: QtCore.Qt.SizeHorCursor,
    _modes.Right: QtCore.Qt.SizeHorCursor,
    _modes.Top: QtCore.Qt.SizeVerCursor,
    _modes.Bottom: QtCore.Qt.SizeVerCursor,
    _modes.TopLeft: QtCore.Qt.SizeFDiagCursor,
    _modes.TopRight: QtCore.Qt.SizeBDiagCursor,
    _modes.BottomLeft: QtCore.Qt.SizeBDiagCursor,
    _modes.BottomRight: QtCore.Qt.SizeFDiagCursor,
    _modes.Move: QtCore.Qt.ClosedHandCursor,
    _modes.NONE: QtCore.Qt.ArrowCursor
}


class AdjustableMixin():
    # TODO: add aspect ratio handling
    name = loggableQtName
    _adjustableMouseBuffer = 3
    _adjustableDefaultArgs = {'adjustButtons':None, 'allowedAdjustments':None,
                              'containerRect':None, 'defaultCursor':None}

    class DragButtons():
        """
        http://pyqt.sourceforge.net/Docs/PyQt4/qt.html#KeyboardModifier-enum
        Note: On Mac OS X, the ControlModifier value corresponds to the Command keys on the Macintosh keyboard,
              and the MetaModifier value corresponds to the Control keys.
        Note: On Windows Keyboards, Qt.MetaModifier and Qt.Key_Meta are mapped to the Windows key.
        """
        LEFT = QtCore.Qt.LeftButton
        RIGHT = QtCore.Qt.RightButton
        MID = MIDDLE = QtCore.Qt.MidButton
        CTRL = CONTROL = QtCore.Qt.CTRL
        SHIFT = QtCore.Qt.ShiftModifier
        ALT = QtCore.Qt.AltModifier
        META = QtCore.Qt.MetaModifier

    class AdjustModes():
        SIZE = {_modes.Left, _modes.Right, _modes.Top, _modes.Bottom, _modes.TopLeft,
                _modes.TopRight, _modes.BottomLeft, _modes.BottomRight}
        DRAG = {_modes.Move}
        ALL = FULL = SIZE.union(DRAG)

        WIDTHONLY = {_modes.Left, _modes.Right}
        HEIGHTONLY = {_modes.Top, _modes.Bottom}

        EDGELEFT = {_modes.Left, _modes.TopLeft, _modes.BottomLeft}
        EDGERIGHT = {_modes.Right, _modes.TopRight, _modes.BottomRight}
        EDGETOP = {_modes.Top, _modes.TopLeft, _modes.TopRight}
        EDGEBOTTOM = {_modes.Bottom, _modes.BottomLeft, _modes.BottomRight}

        ANCHOR_TOP = (ALL - EDGETOP)
        ANCHOR_BOTTOM = (ALL - EDGEBOTTOM)
        ANCHOR_LEFT = (ALL - EDGELEFT)
        ANCHOR_RIGHT = (ALL - EDGERIGHT)

        ANCHOR_TOP_LEFT = (SIZE - EDGELEFT) - EDGETOP
        ANCHOR_BOTTOM_LEFT = (SIZE - EDGELEFT) - EDGEBOTTOM
        ANCHOR_TOP_RIGHT = (SIZE - EDGERIGHT) - EDGETOP
        ANCHOR_BOTTOM_RIGHT = (SIZE - EDGERIGHT) - EDGEBOTTOM

    @classmethod
    def popArgs(cls, kwargs):
        '''
        Removes AdjustableMixin's kwargs from passed in dict.
        :param kwargs: dict, kwargs passed into the sub class
        :return: dict, kwargs for AdjustableMixin.__init__
        '''
        adjustableArgs = {}
        for k, v in cls._adjustableDefaultArgs.items():
            adjustableArgs[k] = kwargs.pop(k, cls._adjustableDefaultArgs[k])
        return adjustableArgs

    def __init__(self, adjustButtons=None, allowedAdjustments=None,
                 containerRect=None, defaultCursor=None):
        super().__init__()
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)
        self.setMouseTracking(True)

        adjustButtons = adjustButtons or QtCore.Qt.RightButton
        if not hasattr(adjustButtons, '__iter__'):
            adjustButtons = [adjustButtons]

        if containerRect and callable(containerRect):
            self.getContainerRect = lambda x: containerRect()

        self._adjustmentButtons = adjustButtons
        self._adjustmentDragStartPos = None
        self._adjustmentCursorOffset = None
        self._adjustmentMode = _modes.NONE
        self._allowedAdjustments = allowedAdjustments or AdjustableMixin.AdjustModes.ALL

        from copy import copy
        self._adjustmentCursors = copy(_cursors)
        if defaultCursor is not None:
            self._adjustmentCursors[_modes.NONE] = defaultCursor

        self.logger = logging.getLogger(self.name)
        self.logger.addHandler(logging.NullHandler())

    def mousePressEvent(self, QMouseEvent):
        self.setFocus()
        if eventMatchesButtons(QMouseEvent, self._adjustmentButtons):
            self._adjustmentMode = self.__getMoveMode(QMouseEvent.pos(), self._adjustableMouseBuffer)

            # moving/dragging
            if self._adjustmentMode == _modes.Move:
                self._adjustmentDragStartPos, self._adjustmentCursorOffset = self.pos(), QMouseEvent.pos()
                self.setCursor(_cursors[_modes.Move])
            else:
                # store size and position limits for stretching
                self._oldSizeLimits = self.__getSizeLimits()
        else:
            self.unsetCursor()
            super(type(self), self).mousePressEvent(QMouseEvent)
            QMouseEvent.accept()

    def mouseMoveEvent(self, QMouseEvent):
        if not eventMatchesButtons(QMouseEvent, self._adjustmentButtons):
            self._adjustmentMode = self.__getMoveMode(QMouseEvent.pos(), self._adjustableMouseBuffer)  # get new mode (for hovering)

            # update cursor
            if self._adjustmentMode == _modes.Move or self._adjustmentMode == _modes.NONE:
                self.setCursor(self._adjustmentCursors[_modes.NONE])
            else:
                self.setCursor(self._adjustmentCursors[self._adjustmentMode])

            sup = super()
            if hasattr(sup, 'mouseMoveEvent'):
                super().mouseMoveEvent(QMouseEvent)

        # moving/dragging
        elif self._adjustmentMode == _modes.Move:
            # if eventMatchesButtons(QMouseEvent, self.dragButtons) and self._cursorOffset:
            if self._adjustmentCursorOffset:
                newPos = QMouseEvent.pos() + self.pos() - self._adjustmentCursorOffset
                cx1, cy1, cx2, cy2 = self.getContainerRect()

                if _modes.Left not in self._allowedAdjustments or _modes.Right not in self._allowedAdjustments:
                    x = self.pos().x()
                else:
                    x = max(newPos.x(), cx1)
                    x = min(cx2 - self.width(), x)

                if _modes.Top not in self._allowedAdjustments or _modes.Bottom not in self._allowedAdjustments:
                    y = self.pos().y()
                else:
                    y = max(newPos.y(), cy1)
                    y = min(cy2 - self.height(), y)

                if (x, y) != (self.pos().x(), self.pos().y()):
                    self.move(QtCore.QPoint(x, y))
            else:
                self._adjustmentDragStartPos = None
                self.unsetCursor()
                super(type(self), self).mouseMoveEvent(QMouseEvent)

        # stretching
        else:
            # size limits
            x1, y1, x2, y2, \
                (x1_min, x1_max), (y1_min, y1_max), \
                (x2_min, x2_max), (y2_min, y2_max), = self._oldSizeLimits

            # event pos wrt parent
            ePos = self.mapTo(self.parent(), QMouseEvent.pos())

            if self._adjustmentMode[0] == _edges.Left:
                x1 = min(ePos.x(), x1_max)
                x1 = max(x1, x1_min)
            elif self._adjustmentMode[0] == _edges.Right:
                x2 = max(ePos.x(), x2_min)
                x2 = min(x2, x2_max)

            if self._adjustmentMode[1] == _edges.Top:
                y1 = min(ePos.y(), y1_max)
                y1 = max(y1, y1_min)
            elif self._adjustmentMode[1] == _edges.Bottom:
                y2 = max(ePos.y(), y2_min)
                y2 = min(y2, y2_max)

            rect = QtCore.QRect()
            rect.setCoords(x1, y1, x2, y2)
            if self.geometry().getRect() != rect.getRect():
                self.setGeometry(rect)

        QMouseEvent.accept()

    def mouseReleaseEvent(self, QMouseEvent):
        if self._adjustmentMode is not _modes.NONE:
            QMouseEvent.accept()
            self.unsetCursor()
        else:
            super(type(self), self).mouseReleaseEvent(QMouseEvent)

    def getContainerRect(self):
        if self.parent():
            return self.parent().contentsRect().getRect()
        elif self.window() == self:
            return QDesktopWidget().availableGeometry(self).getRect()
        else:
            return self.window().contentsRect().getRect()

    def __getMoveMode(self, pos, buffer):
        x, y = _modes.Move

        # left
        if 0 <= pos.x() < buffer:
            x = _edges.Left
        # right
        elif self.width()-buffer < pos.x() <= self.width():
            x = _edges.Right

        # top
        if 0 <= pos.y() < buffer:
            y = _edges.Top
        # bottom
        elif self.height()-buffer < pos.y() <= self.height():
            y = _edges.Bottom

        if (x, y) not in self._allowedAdjustments:
            if _modes.Move in self._allowedAdjustments:
                x, y = _modes.Move
            else:
                x, y = _modes.NONE

        return x, y

    def __getSizeLimits(self):
        # my current coords
        x1, y1, x2, y2 = self.geometry().getCoords()

        # limits of stretch coordinates based on my own limits
        x1_min, x1_max = x2 - self.maximumWidth(), x2 - self.minimumWidth()
        y1_min, y1_max = y2 - self.maximumHeight(), y2 - self.minimumHeight()
        x2_min, x2_max = x1 + self.minimumWidth(), x1 + self.maximumWidth()
        y2_min, y2_max = y1 + self.minimumHeight(), y1 + self.maximumHeight()

        # limits based on parent size
        cx1, cy1, cx2, cy2 = self.getContainerRect()

        # keep inside parent
        x1_min = max(x1_min, 0)
        y1_min = max(y1_min, 0)
        x2_max = min(x2_max, cx2)
        y2_max = min(y2_max, cy2)

        return x1, y1, x2, y2, (x1_min, x1_max), (y1_min, y1_max), (x2_min, x2_max), (y2_min, y2_max)

    def disableAdjustment(self, disable):
        self._allowedAdjustments -= disable

    def enableAdjustment(self, enable):
        self._allowedAdjustments = self._allowedAdjustments.union(enable)

    def setFixedSize(self, *args):
        self._allowedAdjustments -= AdjustableMixin.AdjustModes.SIZE
        if len(args)>0 and args[0] in [None, False]:
            args = (QWIDGETSIZE_MAX, QWIDGETSIZE_MAX)
        super().setFixedSize(*args)

    def setFixedHeight(self, p_int):
        self._allowedAdjustments -= set.union(AdjustableMixin.AdjustModes.EDGETOP, AdjustableMixin.AdjustModes.EDGEBOTTOM)
        if not p_int:
            p_int = QWIDGETSIZE_MAX
        super().setFixedHeight(p_int)

    def setFixedWidth(self, p_int):
        self._allowedAdjustments -= set.union(AdjustableMixin.AdjustModes.EDGELEFT, AdjustableMixin.AdjustModes.EDGERIGHT)
        if not p_int:
            p_int = QWIDGETSIZE_MAX
        super().setFixedWidth(p_int)


class AdjustableContainer(AdjustableMixin):
    # TODO: child management & repositioning on resize
    pass
    # # size of largest children (so widget can't cut them off)
    # smallestW, smallestH = 0, 0  # , (QWIDGETSIZE_MAX, QWIDGETSIZE_MAX)
    # for c in self.children():
    #     try:
    #         _, _, w, h = c.geometry().getRect()
    #     except AttributeError:
    #         pass
    #     else:
    #         if w > smallestW:
    #             smallestW = w
    #         if h > smallestH:
    #             smallestH = h
    # minW = max(self.minimumWidth(), smallestW)
    # minH = max(self.minimumHeight(), smallestH)

    # limits of stretch coordinates based on my own limits
    # x1_max, y1_max = x2 - minW, y2 - minH
    # x1_min, y1_min = x2 - self.maximumWidth(), y2 - self.maximumHeight()
    # x2_max, y2_max = x1 + self.maximumWidth(), y1 + self.maximumHeight()
    # x2_min, y2_min = x1 + minW, y1 + minH


class AdjustableImage(QLabel, AdjustableMixin):
    def __init__(self, parent=None, img=None, **kwargs):
        aArgs = AdjustableMixin.popArgs(kwargs)
        super().__init__(parent, **kwargs)
        AdjustableMixin.__init__(self, **aArgs)

        if img is None:
            self.setFrameStyle(1)
        else:
            self.setFrameStyle(0)

        self.pixmap = QtGui.QPixmap(img)
        self.setPixmap(self.pixmap)

    def resizeEvent(self, QResizeEvent):
        self.setPixmap(self.pixmap.scaled(QResizeEvent.size().width(), QResizeEvent.size().height()))


__all__ = ['AdjustableMixin', 'AdjustableContainer', 'QWIDGETSIZE_MAX',
           'AdjustableImage']
