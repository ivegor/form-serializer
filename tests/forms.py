class Field1:
    pass


class Field2(Field1):
    pass


class Field3(Field2):
    pass


class Field4:
    pass


class Form:
    choice = {'field1': Field1(),
              'field2': Field2(),
              'field3': Field3(),
              'field4': Field4()}
