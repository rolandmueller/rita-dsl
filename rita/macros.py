def resolve_value(obj, context):
    if isinstance(obj, str):
        return obj
    return obj(context=context)

def ANY(context, op=None):
    context.append(('regex', r'.*', op))
    return context


def MARK(type_, obj):
    return {
        'label': type_,
        'data': resolve_value(obj, {})
    }


def IN_LIST(*args, context):
    variants = []
    new_context = []
    for arg in args:
        variants.append(resolve_value(arg, new_context))
    context.append(('any_of', variants, None))
    return context


def PATTERN(*args, context=None):
    new_ctx = []
    for arg in args:
        resolve_value(arg, new_ctx)
    return new_ctx


def WORD(literal, context, op=None):
    context.append(('value', literal, op))
    return context
