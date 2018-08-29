import inspect
from functools import singledispatch, update_wrapper


def method_dispatch(func):
    # from "https://stackoverflow.com/questions/24601722/how-can-i-use-functools-singledispatch-with-instance-methods"
    dispatcher = singledispatch(func)

    def wrapper(*args, **kw):
        return dispatcher.dispatch(args[1].__class__)(*args, **kw)
    wrapper.register = dispatcher.register
    update_wrapper(wrapper, func)
    return wrapper


class NearestClass(dict):
    def get_nearest(self, key):
        for cl in key.__mro__:
            try:
                return self[cl]
            except KeyError:
                pass

        raise KeyError


class Empty:
    def __init__(self, obj):
        self.obj = obj

    def __bool__(self):
        return not bool(self.check_obj(self.obj))

    @method_dispatch
    def check_obj(self, obj):
        return obj

    @check_obj.register(dict)
    def _(self, obj):
        return obj.values()


def is_simple_callable(obj):
    """
    from drf
    """
    if not (inspect.isfunction(obj) or inspect.ismethod(obj)):
        return False

    sig = inspect.signature(obj)
    params = sig.parameters.values()
    return all(
        param.kind == param.VAR_POSITIONAL or
        param.kind == param.VAR_KEYWORD or
        param.default != param.empty
        for param in params
    )
