from marshmallow import fields as f, ValidationError


class BytesField(f.Field):
    encoding = "latin1"

    def _validate(self, value):
        if not isinstance(value, bytes):
            raise ValidationError("Invalid input type!")

        if value is None or value == b"":
            raise ValidationError("Invalid value!")

    def _serialize(self, value, attr: str, obj, **kwargs):
        if value is None:
            return value

        return value.decode(self.encoding)

    def _deserialize(self, value, attr, data, **kwargs):
        if value is None:
            return value

        return value.encode(self.encoding)
