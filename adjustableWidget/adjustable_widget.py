from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QFrame, QWIDGETSIZE_MAX
from PyQt5.QtGui import QCursor
import logging
from generalUtils import loggableQtName


class DragButtons():
    LEFT = QtCore.Qt.LeftButton
    RIGHT = QtCore.Qt.RightButton
    MID = QtCore.Qt.MidButton
    MIDDLE = QtCore.Qt.MiddleButton

    @classmethod
    def values(cls):
        for i in ['LEFT', 'RIGHT', 'MID', 'MIDDLE']:
            yield getattr(cls, i)


class DraggableWidget():
    name = loggableQtName

    def __init__(self, size=None, pos=None, button=QtCore.Qt.RightButton):
        super().__init__()
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

        assert button in DragButtons.values(), \
            f"Invalid button '{button}'. Must be in DragButtons)"
        self.drag_button = button
        self.setMouseTracking(True)
        self.__startPos = None
        self._cursorOffset = None

        if size:
            self.resize(size)
        if pos:
            self.move(pos)

    def mousePressEvent(self, event):
        self.setFocus()
        if event.button() == self.drag_button:
            self.__startPos = None
            logging.debug(f"{self.name} adjustment activated")
            self.__startPos, self._cursorOffset = self.pos(), event.pos()
            event.accept()
        else:
            super(type(self), self).mousePressEvent(event)
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == self.drag_button and self._cursorOffset:
            newPos = event.pos() + self.pos() - self._cursorOffset
            if self.parent():
                cx1, cy1, cx2, cy2 = self.parent().geometry().getRect()
            else:
                cx1, cy1, cx2, cy2 = self.window().geometry().getRect()

            x = max(newPos.x(), 0)
            x = min(cx2-self.width(), x)
            y = max(newPos.y(), 0)
            y = min(cy2-self.height(), y)

            if (x, y) != (self.pos().x(), self.pos().y()):
                self.move(QtCore.QPoint(x, y))
        else:
            super(type(self), self).mouseMoveEvent(event)
        event.accept()

    def mouseReleaseEvent(self, event):
        if self.__startPos is not None:  # we were dragging
            moved = self.pos() - self.__startPos

            if moved.manhattanLength() > 2:
                event.ignore()
                logging.debug(f"{self.name}moved from {(self.__startPos.x(), self.__startPos.y())}" +
                 f" to {(self.pos().x(), self.pos().y())}")

            self.__startPos = None
        else:
            super(type(self), self).mouseReleaseEvent(event)
        event.accept()


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
    SIZE = {_modes.Left, _modes.Right, _modes.Top, _modes.Bottom, _modes.TopLeft, _modes.TopRight, _modes.BottomLeft,
            _modes.BottomRight}
    DRAG = {_modes.Move}
    ALL = SIZE.union(DRAG)

    WIDTHONLY = {_modes.Left, _modes.Right}
    HEIGHTONLY = {_modes.Top, _modes.Bottom}

    EDGELEFT = {_modes.Left, _modes.TopLeft, _modes.BottomLeft}
    EDGERIGHT = {_modes.Right, _modes.TopRight, _modes.BottomRight}
    EDGETOP = {_modes.Top, _modes.TopLeft, _modes.TopRight}
    EDGEBOTTOM = {_modes.Bottom, _modes.BottomLeft, _modes.BottomRight}

    ANCHOR_TOP = ALL - EDGETOP - DRAG
    ANCHOR_BOTTOM = ALL - EDGEBOTTOM - DRAG
    ANCHOR_LEFT = ALL - EDGELEFT - DRAG
    ANCHOR_RIGHT = ALL - EDGERIGHT - DRAG

    ANCHOR_TOP_LEFT = {_modes.Right, _modes.Bottom, _modes.BottomRight}
    ANCHOR_BOTTOM_LEFT = {_modes.Right, _modes.Top, _modes.TopRight}
    ANCHOR_TOP_RIGHT = {_modes.Left, _modes.Bottom, _modes.BottomLeft}
    ANCHOR_BOTTOM_RIGHT = {_modes.Left, _modes.Top, _modes.TopLeft}

    @classmethod
    def values(cls):
        for k in [k for k, v in cls.__dict__.items() if isinstance(v, list)]:
            yield k


class AdjustableWidget(QWidget, DraggableWidget):
    # TODO: add position constraint options (stick to lines or edges)
    # TODO: constrainOnEdge(), constrainWithin(), setCenterPosition()
    # TODO: add aspect ratio option
    buffer = 3

    cursors = \
        {
            _modes.Left: QtCore.Qt.SizeHorCursor,
            _modes.Right: QtCore.Qt.SizeHorCursor,
            _modes.Top: QtCore.Qt.SizeVerCursor,
            _modes.Bottom: QtCore.Qt.SizeVerCursor,
            _modes.TopLeft: QtCore.Qt.SizeFDiagCursor,
            _modes.TopRight: QtCore.Qt.SizeBDiagCursor,
            _modes.BottomLeft: QtCore.Qt.SizeBDiagCursor,
            _modes.BottomRight: QtCore.Qt.SizeFDiagCursor,
            _modes.Move: QtCore.Qt.ArrowCursor,
            _modes.NONE: QtCore.Qt.ArrowCursor
        }

    def __init__(self, parent=None, allowedAdjust=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.mode = _modes.NONE
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setMouseTracking(True)

        if allowedAdjust is not None:
            assert all(len(i) == 2 for i in allowedAdjust)  # (,)
            assert all(j in [-1, 0, 1, 2] for i in allowedAdjust for j in i)  # -1, 0, 1, 2
            self.allowedAdjust = allowedAdjust
        else:
            self.allowedAdjust = {(i, j) for i in [-1, 0, 1] for j in [-1, 0, 1]}

    def mousePressEvent(self, event):
        self.setFocus()
        if event.button() == self.drag_button:
            self.mode = self.__getMoveMode(event.pos(), self.buffer)

            # moving/dragging, pass click to DraggableWidget
            if self.mode == _modes.Move:
                DraggableWidget.mousePressEvent(self, event)

            # store size and position limits for stretching
            self._lims = self.__getSizeLimits()
        else:
            super(type(self), self).mousePressEvent(event)
        event.accept()

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

        # size of largest children (so widget can't cut them off)
        smallestW, smallestH = 0, 0  # , (QWIDGETSIZE_MAX, QWIDGETSIZE_MAX)
        for c in self.children():
            try:
                _, _, w, h = c.geometry().getRect()
            except AttributeError:
                pass
            else:
                if w > smallestW:
                    smallestW = w
                if h > smallestH:
                    smallestH = h
        minW = max(self.minimumWidth(), smallestW)
        minH = max(self.minimumHeight(), smallestH)

        # limits of stretch coordinates based on my own limits
        x1_max, y1_max = x2 - minW, y2 - minH
        x1_min, y1_min = x2 - self.maximumWidth(), y2 - self.maximumHeight()
        x2_max, y2_max = x1 + self.maximumWidth(), y1 + self.maximumHeight()
        x2_min, y2_min = x1 + minW, y1 + minH

        # limits based on parent size
        if self.parent():
            _, _, cx2, cy2 = self.parent().geometry().getRect()
        else:
            _, _, cx2, cy2 = self.window().geometry().getRect()

        # keep inside parent
        x1_min = max(x1_min, 0)
        y1_min = max(y1_min, 0)
        x2_min = max(x2_min, 0)
        y2_min = max(y2_min, 0)

        x2_max = min(x2_max, cx2)
        y2_max = min(y2_max, cy2)

        return x1, y1, x2, y2, (x1_min, x1_max), (y1_min, y1_max), (x2_min, x2_max), (y2_min, y2_max)

    def mouseMoveEvent(self, event):
        # not using drag_button
        if event.buttons() != self.drag_button:
            oldMode = self.mode  # store mode
            self.mode = self.__getMoveMode(event.pos(), self.buffer)  # get new mode (for hovering)

            if oldMode != self.mode:  # if mode has changed, change cursor
                self.setCursor(QCursor(self.cursors[self.mode]))

            super(type(self), self).mouseMoveEvent(event)

        # moving/dragging
        elif self.mode == _modes.Move:
            DraggableWidget.mouseMoveEvent(self, event)

        # stretching
        else:
            # size limits
            x1, y1, x2, y2, \
                (x1_min, x1_max), (y1_min, y1_max), \
                (x2_min, x2_max), (y2_min, y2_max), = self._lims

            # event pos wrt parent
            ePos = self.mapTo(self.parent(), event.pos())

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

        event.accept()



class AdjustableContainer(AdjustableWidget):
    # TODO: implement as superclass (then make QFrame, QWidget, QGroupBox from it)
    # TODO: child management & repositioning on resize
    pass


__all__ = ['DraggableWidget', 'DragButtons', 'AdjustableWidget', 'AdjustModes']
