from form_serializer.componets import FormSerializer, SerializerFieldByAttr, SerializerFieldSet, specializer, \
    SerializerFieldMethod
from tests.forms import Field1


class DefaultSerializerSet(SerializerFieldSet):
    name = SerializerFieldByAttr('__class__.__name__')


@specializer(Field1)
class Field1Serializer(DefaultSerializerSet):
    add_field = SerializerFieldMethod()

    def get_add_field(self, obj):
        return 'hi'


class FormSer(FormSerializer):
    name = SerializerFieldByAttr('__name__')
    choices = DefaultSerializerSet('choice')