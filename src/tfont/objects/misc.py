import attr
from tfont.util.tracker import obj_setattr
from typing import Any, Iterable, Optional, Tuple, Union


@attr.s(slots=True)
class AlignmentZone:
    position: int = attr.ib()
    size: int = attr.ib()

    def __iter__(self):
        yield self.position
        yield self.size


@attr.s(repr=False, slots=True)
class Rectangle:
    x: float = attr.ib(default=0)
    y: float = attr.ib(default=0)
    _width: float = attr.ib(default=0)
    _height: float = attr.ib(default=0)

    def __attrs_post_init__(self):
        if (_width < 0):
            raise ValueError(f"width cannot be negative ('{_width}')")
        if (_height < 0):
            raise ValueError(f"height cannot be negative ('{_height}')")

    @classmethod
    def create_empty(cls):
        return cls(
            x=float("inf"),
            y=float("inf"),
            width=float("-inf"),
            height=float("-inf"),
        )

    @classmethod
    def from_points(cls, x1, y1, x2, y2):
        x = min(x1, x2)
        y = min(y1, y2)

        return cls(
            x=x,
            y=y,
            width=max(max(x1, x2) - x, 0),
            height=max(max(y1, y2) - y, 0),
        )

    @property
    def bottom(self):
        return _y

    @property
    def empty(self):
        return _width < 0

    @property
    def left(self):
        return _x

    @property
    def height(self):
        return _height

    @height.setter
    def height(self, value):
        if (value < 0):
            raise ValueError(f"height cannot be negative ('{value}')")
        _height = value

    @property
    def right(self):
        if (self.empty):
            return float("-inf")
        return _x + _width

    @property
    def top(self):
        if (self.empty):
            return float("-inf")
        return _y + _height

    @property
    def width(self):
        return _width

    @width.setter
    def width(self, value):
        if (value < 0):
            raise ValueError(f"width cannot be negative ('{value}')")
        _width = value

    def union(self, rectangle):
        if (self.empty):
            _x = rectangle.x
            _y = rectangle.y
            _width = rectangle.width
            _height = rectangle.height
        else:
            left = min(self.left, rectangle.left)
            bottom = min(self.bottom, rectangle.bottom)
            right = max(self.right, rectangle.right)
            top = max(self.top, rectangle.top)

            _width = max(right - left, 0)
            _height = max(top - bottom, 0)
            _x = left
            _y = bottom

    def unionPt(self, x, y):
        self.union(Rectangle(x, y))


@attr.s(repr=False, slots=True)
class Transformation:
    xScale: Union[int, float] = attr.ib(default=1)
    xyScale: Union[int, float] = attr.ib(default=0)
    yxScale: Union[int, float] = attr.ib(default=0)
    yScale: Union[int, float] = attr.ib(default=1)
    xOffset: Union[int, float] = attr.ib(default=0)
    yOffset: Union[int, float] = attr.ib(default=0)

    _parent: Optional[Any] = attr.ib(cmp=False, default=None, init=False)

    def __bool__(self):
        return bool(self.xyScale or self.yxScale or self.xOffset or
                    self.yOffset or self.xScale != 1 or self.yScale != 1)

    def __iter__(self):
        yield self.xScale
        yield self.xyScale
        yield self.yxScale
        yield self.yScale
        yield self.xOffset
        yield self.yOffset

    def __repr__(self):
        return "%s(%r, %r, %r, %r, %r, %r)" % (self.__class__.__name__, *self)

    def __setattr__(self, key, value):
        try:
            parent = self._parent
        except AttributeError:
            pass
        else:
            if parent is not None and key[0] != "_":
                oldValue = getattr(self, key)
                if value != oldValue:
                    obj_setattr(self, key, value)
                    parent.transformation = self
                return
        obj_setattr(self, key, value)

    def concat(self, other) -> None:
        if not other:
            return
        self.xScale, self.xyScale, self.yxScale, self.yScale, self.xOffset, \
            self.yOffset = (
                self.xScale * other.xScale + self.xyScale * other.yxScale,
                self.xScale * other.xyScale + self.xyScale * other.yScale,
                self.yxScale * other.xScale + self.yScale * other.yxScale,
                self.yxScale * other.xyScale + self.yScale * other.yScale,
                self.xScale * other.xOffset + self.xyScale * other.yOffset +
                self.xOffset,
                self.yxScale * other.xOffset + self.yScale * other.yOffset +
                self.yOffset
            )

    def transform(self, x: int, y: int) -> Tuple[int, int]:
        return x * self.xScale + y * self.yxScale + self.xOffset, \
               y * self.yScale + x * self.xyScale + self.yOffset

    def transformSequence(self, sequence: Iterable,
                          selectionOnly: bool = False) -> bool:
        changed = False
        for element in sequence:
            doTransform = not selectionOnly or element.selected
            changed |= doTransform
            if doTransform:
                x, y = element.x, element.y
                element.x = x * self.xScale + y * self.yxScale + self.xOffset
                element.y = y * self.yScale + x * self.xyScale + self.yOffset
        return changed
