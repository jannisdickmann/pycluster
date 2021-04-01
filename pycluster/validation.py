def isbool(x):
    return isinstance(x, bool)


def isint(x):
    return isinstance(x, int)


def ispositiveint(x, strict=True):
    if strict:
        return isint(x) and x > 0
    else:
        return isint(x) and x >= 0


def isnumber(x):
    return isinstance(x, (int, float))


def ispositivenumber(x, strict=True):
    if strict:
        return isnumber(x) and x > 0
    else:
        return isnumber(x) and x >= 0


def islist(x, minlength=1):
    return isinstance(x, list) and len(x) >= minlength


def isnumericlist(x, minlength=1):
    success = islist(x, minlength)
    if success:
        for item in x:
            if not isnumber(item):
                success = False
    return success


def isnotnone(x):
    return x is not None
