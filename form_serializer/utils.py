class NearestClass(dict):
    def __missing__(self, key):
        if key is object:
            raise KeyError
        return self[key.__mro__[1]]
