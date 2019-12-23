from fontTools.misc.timeTools import epoch_diff
import io
import unicodedata


_postscript_name_exceptions = set("[](){}<>/%")


def _filter_string(string, try_writec, logging_callback):
    result = io.StringIO()

    for c in string:
        try_writec(c, result) or try_writec(unicodedata.normalize("NFKD", c)[0], result)

    value = result.getvalue()
    if logging_callback is not None and value != string:
        # use kv pairs!!
        logging_callback(string)
    return value

#


def to_bitflags(indices, start, length):
    end = start + length
    value = 0
    for ix in indices:
        if start <= ix < end:
            value |= ix
    return value


def to_opentype_timestamp(datetime, logging_callback=None):
    """
    OpenType offsets use original Mac epoch (Jan. 1 1904).
    """

    return int(datetime.timestamp()) - epoch_diff


def to_glyph_name(string, logging_callback=None):

    def try_writec(c, out):
        if ("A" <= c <= "Z") or \
            ("a" <= c <= "z") or \
            ("0" <= c <= "9") or \
            c == "." or \
            c == "_":
            out.write(c)
            return True
        return False

    return _filter_string(string, try_writec, logging_callback)


def to_postscript_name(string, logging_callback=None):

    def try_writec(c, out):
        if ("!" <= c <= "~") and \
            c not in _postscript_name_exceptions and \
            c != " ":
            out.write(c)
            return True
        return False

    return _filter_string(string, try_writec, logging_callback)


def to_postscript_string(string, logging_callback=None):

    def try_writec(c, out):
        if c == "©":
            out.write("Copyright")
            return True
        if ("!" <= c <= "~") and \
            c not in _postscript_name_exceptions:
            out.write(c)
            return True
        return False

    return _filter_string(string, try_writec, logging_callback)
