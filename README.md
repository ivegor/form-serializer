# Form Serializer
**Simple serializer for forms**

example of usage for django-rest-framework:

```python
from rest_framework import serializers

from form_serializer.components import SerializerFieldByAttr, SerializerFieldSet, FormSerializer


class DefaultFilterSet(SerializerFieldSet):
    type = SerializerFieldByAttr('__class__.__name__')
    verbose_name = SerializerFieldByAttr()
    payload = SerializerFieldByAttr('choices')


class CustomForm(FormSerializer):
    name = SerializerFieldByAttr('__class__.__name__')
    fields = DefaultFilterSet()


class TestSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    string = serializers.StringRelatedField()

print(CustomForm(TestSerializer()).serialize())