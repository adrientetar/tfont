

def error_duplicate_encoding(name, unicode, oldName):
    return _error(
        text="U+{unicode} in glyph '{name}' is already mapped to '{oldName}'",
        name=name,
        unicode=unicode,
        oldName=oldName,
    )


def error_duplicate_glyphs(duplicates):
    return _error(
        text="Glyph names '{duplicates}' appear multiple times in the font",
        duplicates=duplicates,
    )


def error_negative_width(name, width):
    return _error(
        text="Glyph '{name}' has negative width '{width}'",
        name=name,
        width=width,
    )


def warning_attr_truncated(attr, result):
    return _warning(
        text="'{attr}' attribute was truncated to '{result}'",
        attr=attr,
        result=result,
    )


def warning_missing_hmtx(target):
    return _warning(
        text="Missing 'hmtx' table when computing '{target}'",
        target=target,
    )

#


def _error(**kwargs):
    return {
        "level": "error",
        **kwargs
    }


def _warning(**kwargs):
    return {
        "level": "warning",
        **kwargs
    }