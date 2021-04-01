__all__ = [
    'parseynanswer',
    'variableinput',
    'typedvariableinput',
    'validatedvariableinput'
]


def parseynanswer(question):
    question = '\n' + question + ' (y/n)\n> '
    answer = input(question)
    while answer != 'y' and answer != 'n':
        answer = input('Please answer with "y" (yes) or "n" (no):\n> ')
    return answer == 'y'


def variableinput(variablename, default):
    question = variablename + ' (default=' + default + ')\n> '
    answer = input(question)
    if len(answer) == 0:
        return default
    else:
        return answer


def typedvariableinput(variablename, default, type, prepend=''):
    def isvalid(a, t):
        if len(a) == 0:
            return True
        try:
            a = t(a)
            return a
        except ValueError:
            return False

    question = prepend + variablename + ' (default=' + str(default) + ')\n> '
    answer = input(question)
    while not isvalid(answer, type):
        answer = input \
            ('Please input a valid {} value or leave blank for default:\n> '.format(type))
    if len(answer) == 0:
        return default
    else:
        return type(answer)


def validatedvariableinput(variablename, default, type, valid):
    def isvalid(a, t, v):
        if len(a) == 0:
            return True
        try:
            a = t(a)
            return v(a)
        except ValueError:
            return False

    question = variablename + ' (default=' + str(default) + ')\n> '
    answer = input(question)
    while not isvalid(answer, type, valid):
        answer = input \
            ('Please input a valid {} value with condition {} or leave blank for default:\n> '.format(type, valid))
    if len(answer) == 0:
        return default
    else:
        return type(answer)
