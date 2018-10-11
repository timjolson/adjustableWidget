from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QWIDGETSIZE_MAX, QDesktopWidget
import logging
from generalUtils import loggableQtName, eventMatchesButtons


class DragButtons():
    LEFT = QtCore.Qt.LeftButton
    RIGHT = QtCore.Qt.RightButton
    MID = MIDDLE = QtCore.Qt.MidButton
    CTRL = CONTROL = QtCore.Qt.CTRL
    SHIFT = QtCore.Qt.ShiftModifier
    ALT = QtCore.Qt.AltModifier
    META = QtCore.Qt.MetaModifier
    # http://pyqt.sourceforge.net/Docs/PyQt4/qt.html#KeyboardModifier-enum
    # Note: On Mac OS X, the ControlModifier value corresponds to the Command keys on the Macintosh keyboard,
    #       and the MetaModifier value corresponds to the Control keys.
    # Note: On Windows Keyboards, Qt.MetaModifier and Qt.Key_Meta are mapped to the Windows key.


class DraggableWidget():
    name = loggableQtName

    def __init__(self, size=None, pos=None, buttons=QtCore.Qt.RightButton, containerRect=None):
        super().__init__()
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)
        self.setMouseTracking(True)

        if not hasattr(buttons, '__iter__'):
            buttons = list({buttons})

        self.dragButtons = buttons
        self.dragStartPos = None
        self._cursorOffset = None

        if containerRect and callable(containerRect):
            self.getContainerRect = lambda x: containerRect()

        if size:
            self.resize(size)
        if pos:
            self.move(pos)

    def mousePressEvent(self, QMouseEvent):
        self.setFocus()
        if eventMatchesButtons(QMouseEvent, self.dragButtons):
            logging.debug(f"{self.name}dragging activated")
            self.dragStartPos, self._cursorOffset = self.pos(), QMouseEvent.pos()
            self.setCursor(QtCore.Qt.ClosedHandCursor)
        else:
            self.unsetCursor()
            super(type(self), self).mousePressEvent(QMouseEvent)
        QMouseEvent.accept()

    def getContainerRect(self):
        if self.parent():
            return self.parent().contentsRect().getRect()
        elif self.window() == self:
            # cx1, cy1, cx2, cy2 = QDesktopWidget().contentsRect().getRect()
            # cx1, cy1, cx2, cy2 = QDesktopWidget().screenGeometry(-1).getRect()
            return QDesktopWidget().availableGeometry(self).getRect()
        else:
            return self.window().contentsRect().getRect()

    def mouseMoveEvent(self, QMouseEvent):
        if eventMatchesButtons(QMouseEvent, self.dragButtons) and self._cursorOffset:
            newPos = QMouseEvent.pos() + self.pos() - self._cursorOffset
            cx1, cy1, cx2, cy2 = self.getContainerRect()

            x = max(newPos.x(), cx1)
            x = min(cx2-self.width(), x)
            y = max(newPos.y(), cy1)
            y = min(cy2-self.height(), y)

            if (x, y) != (self.pos().x(), self.pos().y()):
                self.move(QtCore.QPoint(x, y))
        else:
            self.dragStartPos = None
            self.unsetCursor()
            super(type(self), self).mouseMoveEvent(QMouseEvent)
        QMouseEvent.accept()


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

    ANCHOR_TOP = (ALL - EDGETOP) - DRAG
    ANCHOR_BOTTOM = (ALL - EDGEBOTTOM) - DRAG
    ANCHOR_LEFT = (ALL - EDGELEFT) - DRAG
    ANCHOR_RIGHT = (ALL - EDGERIGHT) - DRAG

    ANCHOR_TOP_LEFT = (SIZE - EDGELEFT) - EDGETOP
    ANCHOR_BOTTOM_LEFT = (SIZE - EDGELEFT) - EDGEBOTTOM
    ANCHOR_TOP_RIGHT = (SIZE - EDGERIGHT) - EDGETOP
    ANCHOR_BOTTOM_RIGHT = (SIZE - EDGERIGHT) - EDGEBOTTOM

cursors = {
    _modes.Left: QtCore.Qt.SizeHorCursor,
    _modes.Right: QtCore.Qt.SizeHorCursor,
    _modes.Top: QtCore.Qt.SizeVerCursor,
    _modes.Bottom: QtCore.Qt.SizeVerCursor,
    _modes.TopLeft: QtCore.Qt.SizeFDiagCursor,
    _modes.TopRight: QtCore.Qt.SizeBDiagCursor,
    _modes.BottomLeft: QtCore.Qt.SizeBDiagCursor,
    _modes.BottomRight: QtCore.Qt.SizeFDiagCursor,
    # _modes.Move: QtCore.Qt.ClosedHandCursor,
    _modes.NONE: QtCore.Qt.ArrowCursor
}


class AdjustableWidget(QWidget, DraggableWidget):
    # TODO: add position constraint options (stick to lines or edges)
    # TODO: constrainOnEdge(), setCenterPosition()
    # TODO: add aspect ratio option
    buffer = 3

    def __init__(self, parent=None, allowedAdjust=None, defaultCursor=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.mode = _modes.NONE

        if allowedAdjust is not None:
            self.allowedAdjust = allowedAdjust
        else:
            self.allowedAdjust = AdjustModes.ALL

        from copy import copy
        self.cursors = copy(cursors)
        if defaultCursor is not None:
            self.cursors[_modes.NONE] = defaultCursor

    def mousePressEvent(self, QMouseEvent):
        self.setFocus()
        if eventMatchesButtons(QMouseEvent, self.dragButtons):
            self.mode = self.__getMoveMode(QMouseEvent.pos(), self.buffer)

            # moving/dragging, pass click to DraggableWidget
            if self.mode == _modes.Move:
                DraggableWidget.mousePressEvent(self, QMouseEvent)
            else:
                # store size and position limits for stretching
                self._lims = self.__getSizeLimits()
                logging.debug(f"{self.name}adjustment activated")
        else:
            super(type(self), self).mousePressEvent(QMouseEvent)
            QMouseEvent.accept()

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

        if (x, y) not in self.allowedAdjust:
            if _modes.Move in self.allowedAdjust:
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
        if self.parent():
            cx2 -= 1
            cy2 -= 1

        # keep inside parent
        x1_min = max(x1_min, 0)
        y1_min = max(y1_min, 0)
        x2_max = min(x2_max, cx2)
        y2_max = min(y2_max, cy2)

        return x1, y1, x2, y2, (x1_min, x1_max), (y1_min, y1_max), (x2_min, x2_max), (y2_min, y2_max)

    def mouseMoveEvent(self, QMouseEvent):
        # not using dragButtons
        if not eventMatchesButtons(QMouseEvent, self.dragButtons):
            self.mode = self.__getMoveMode(QMouseEvent.pos(), self.buffer)  # get new mode (for hovering)

            # update cursor
            if self.mode == _modes.Move or self.mode == _modes.NONE:
                self.setCursor(self.cursors[_modes.NONE])
            else:
                self.setCursor(self.cursors[self.mode])

            super(type(self), self).mouseMoveEvent(QMouseEvent)

        # moving/dragging
        elif self.mode == _modes.Move:
            DraggableWidget.mouseMoveEvent(self, QMouseEvent)

        # stretching
        else:
            # size limits
            x1, y1, x2, y2, \
                (x1_min, x1_max), (y1_min, y1_max), \
                (x2_min, x2_max), (y2_min, y2_max), = self._lims

            # event pos wrt parent
            ePos = self.mapTo(self.parent(), QMouseEvent.pos())

            if self.mode[0] == _edges.Left:
                x1 = min(ePos.x(), x1_max)
                x1 = max(x1, x1_min)
            elif self.mode[0] == _edges.Right:
                x2 = max(ePos.x(), x2_min)
                x2 = min(x2, x2_max)

            if self.mode[1] == _edges.Top:
                y1 = min(ePos.y(), y1_max)
                y1 = max(y1, y1_min)
            elif self.mode[1] == _edges.Bottom:
                y2 = max(ePos.y(), y2_min)
                y2 = min(y2, y2_max)

            rect = QtCore.QRect()
            rect.setCoords(x1, y1, x2, y2)
            if self.geometry().getRect() != rect.getRect():
                self.setGeometry(rect)

        QMouseEvent.accept()

    def disableAdjust(self, disable):
        self.allowedAdjust -= disable

    def enableAdjust(self, enable):
        self.allowedAdjust = self.allowedAdjust.union(enable)

    def setFixedSize(self, *args):
        self.allowedAdjust -= AdjustModes.SIZE
        if len(args)>0 and not args[0]:
            args = (QWIDGETSIZE_MAX, QWIDGETSIZE_MAX)
        super().setFixedSize(*args)

    def setFixedHeight(self, p_int):
        self.allowedAdjust -= set.union(AdjustModes.EDGETOP, AdjustModes.EDGEBOTTOM)
        if not p_int:
            p_int = QWIDGETSIZE_MAX
        super().setFixedHeight(p_int)

    def setFixedWidth(self, p_int):
        self.allowedAdjust -= set.union(AdjustModes.EDGELEFT, AdjustModes.EDGERIGHT)
        if not p_int:
            p_int = QWIDGETSIZE_MAX
        super().setFixedWidth(p_int)


class AdjustableContainer(AdjustableWidget):
    # TODO: implement as superclass (then make QFrame, QWidget, QGroupBox from it)
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


__all__ = ['DraggableWidget', 'DragButtons', 'AdjustableWidget', 'AdjustableContainer', 'AdjustModes', 'QWIDGETSIZE_MAX']
