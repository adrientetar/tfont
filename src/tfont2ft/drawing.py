

def draw_layer(layer, pen):
    for path in layer.paths:
        draw_path(path, pen)


def draw_path(path, pen):
    points = path._points
    if not points:
        return
    start = points[0]
    open_ = skip = start.type == "move"
    if open_:
        pen.moveTo((start.x, start.y))
    else:
        start = points[-1]
        assert start.type is not None
        pen.moveTo((start.x, start.y))
    stack = []
    for point in points:
        if skip:
            skip = False
        elif point.type == "line":
            assert not stack
            pen.lineTo((point.x, point.y))
        else:
            stack.append((point.x, point.y))
            if point.type == "curve":
                pen.curveTo(*stack)
                stack = []
    if not open_:
        pen.closePath()
