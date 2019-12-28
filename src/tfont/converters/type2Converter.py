from tfont.converters.openType import Type2FontCompiler


class Type2Converter:
    __slots__ = "_kwargs"

    def __init__(self, **kwargs):
        self._kwargs = kwargs

    def open(self, path, font=None):
        raise NotImplementedError

    def save(self, font, path):
        compiler = Type2FontCompiler(font, **self._kwargs)
        otf, log = compiler.compile()

        ok = not any(entry.type == "error" for entry in log)
        if ok:
            otf.save(path)

        return ok, log
