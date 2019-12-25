import attr
from tfont.util.observable import ChangeType, ObservableList


def observable_list(parent, items):
    ol = ObservableList(items)

    def change_handler(sender, args):
        is_replace = args.action == ChangeType.REPLACE
        if args.action == ChangeType.REMOVE or is_replace:
            for item in args.oldItems:
                item._parent = None
        if args.action == ChangeType.ADD or is_replace:
            for item in args.newItems:
                item._parent = parent
    ol.change_event.append(change_handler)

    return ol


@attr.s(auto_attribs=True, repr=False, slots=True)
class Matrix3x2:
    m11: float = 1
    m12: float = 0
    m21: float = 0
    m22: float = 1
    m31: float = 0
    m32: float = 0

    @classmethod
    def create_translation(self, dx, dy):
        return Matrix3x2(m31=dx, m32=dy)

    def __bool__(self):
        return bool(self.m12 or self.m21 or self.m31 or
                    self.m32 or self.m11 != 1 or self.m22 != 1)

    def __iter__(self):
        yield self.m11
        yield self.m12
        yield self.m21
        yield self.m22
        yield self.m31
        yield self.m32

    def __mul__(self, other):
        if not other:
            return
        self.m11, self.m12, self.m21, self.m22, self.m31, \
            self.m32 = (
                self.m11 * other.m11 + self.m12 * other.m21,
                self.m11 * other.m12 + self.m12 * other.m22,
                self.m21 * other.m11 + self.m22 * other.m21,
                self.m21 * other.m12 + self.m22 * other.m22,
                self.m11 * other.m31 + self.m12 * other.m32 +
                self.m31,
                self.m21 * other.m31 + self.m22 * other.m32 +
                self.m32
            )

    def __repr__(self):
        return "[%r, %r, %r, %r, %r, %r]" % tuple(self)

    def transform(self, x, y):
        return x * self.m11 + y * self.m21 + self.m31, \
               y * self.m22 + x * self.m12 + self.m32


@attr.s(auto_attribs=True, slots=True)
class AlignmentZone:
    position: int
    size: int

    def __iter__(self):
        yield self.position
        yield self.size


@attr.s(auto_attribs=True, repr=False, slots=True)
class Rectangle:
    x: float = 0
    y: float = 0
    _width: float = 0
    _height: float = 0

    def __attrs_post_init__(self):
        if self._width < 0:
            raise ValueError(f"width cannot be negative ('{self._width}')")
        if self._height < 0:
            raise ValueError(f"height cannot be negative ('{self._height}')")

    @classmethod
    def create_empty(cls):
        rectangle = cls(
            x=float("inf"),
            y=float("inf"),
        )
        rectangle._width = float("-inf")
        rectangle._height = float("-inf")
        return rectangle

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
        return self.y

    @property
    def empty(self):
        return self._width < 0

    @property
    def left(self):
        return self.x

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        if value < 0:
            raise ValueError(f"height cannot be negative ('{value}')")
        self._height = value

    @property
    def right(self):
        if self.empty:
            return float("-inf")
        return self.x + self._width

    @property
    def top(self):
        if self.empty:
            return float("-inf")
        return self.y + self._height

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        if value < 0:
            raise ValueError(f"width cannot be negative ('{value}')")
        self._width = value

    def union(self, rectangle):
        if self.empty:
            self.x = rectangle.x
            self.y = rectangle.y
            self._width = rectangle.width
            self._height = rectangle.height
        else:
            left = min(self.left, rectangle.left)
            bottom = min(self.bottom, rectangle.bottom)
            right = max(self.right, rectangle.right)
            top = max(self.top, rectangle.top)

            self._width = max(right - left, 0)
            self._height = max(top - bottom, 0)
            self.x = left
            self.y = bottom

    def unionPt(self, x, y):
        self.union(Rectangle(x, y))
