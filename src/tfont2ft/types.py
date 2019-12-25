

class Context:
    __slots__ = ("_font", "_master", "_log")

    def __init__(self, font, master):
        self._font = font
        self._master = master
        self._log = []
    
    @property
    def log(self):
        return self._log
    
    @property
    def font(self):
        return self._font
    
    @property
    def master(self):
        return self._master
