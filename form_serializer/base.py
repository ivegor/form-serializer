from abc import abstractmethod
from functools import reduce


class MetaSerializer(type):
    def __new__(mcls, name, bases, namespace):
        cl = super().__new__(mcls, name, bases, namespace)
        cl._fields = reduce(
            lambda x, y: x.union(y),
            (c._fields for c in reversed(bases) if hasattr(c, '_fields')),
            set()
        )
        for field_name, value in namespace.items():
            if isinstance(value, BaseFieldSerializer):
                cl._fields.add(field_name)
        return cl


class BaseFieldSerializer:
    @abstractmethod
    def serialize(self, obj, field_name):
        pass


class BaseFieldSetSerializer(BaseFieldSerializer, metaclass=MetaSerializer):
    @abstractmethod
    def serialize(self, obj, field_name):
        pass


class BaseFormSerializer(metaclass=MetaSerializer):

    @abstractmethod
    def serialize(self):
        pass
