import io


class Context:
    __slots__ = ("_font", "_master", "_errors", "_output")

    def __init__(self, font, master):
        self._font = font
        self._master = master
        self._errors = io.StringIO()
        self._output = io.StringIO()
    
    @property
    def errors(self):
        return self._errors.getvalue()
    
    @property
    def font(self):
        return self._font
    
    @property
    def master(self):
        return self._master
    
    @property
    def output(self):
        return self._output.getvalue()
    
    def error(self, msg):
        self._errors.write(f"{msg}\n")
    
    def warning(self, msg):
        self._output.write(f"Warning: {msg}\n")