from abc import abstractmethod
from functools import reduce


class MetaSerializer(type):
    def __new__(mcls, name, bases, namespace):
        declared_fields = reduce(
            lambda x, y: dict(x, **y),
            (c._fields for c in reversed(bases) if hasattr(c, '_fields')),
            {}
        )
        for field_name, value in list(namespace.items()):
            if isinstance(value, BaseFieldSerializer):
                declared_fields[field_name] = (namespace.pop(field_name))
        namespace['_fields'] = declared_fields
        return super().__new__(mcls, name, bases, namespace)


class BaseFieldSerializer:
    @abstractmethod
    def serialize(self, obj, field_name, *args, **kwargs):
        pass


class BaseFieldSetSerializer(BaseFieldSerializer, metaclass=MetaSerializer):
    @abstractmethod
    def serialize(self, obj, field_name, *args, **kwargs):
        pass


class BaseFormSerializer(metaclass=MetaSerializer):

    @abstractmethod
    def serialize(self):
        pass
