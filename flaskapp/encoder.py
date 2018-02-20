from flask.json import JSONEncoder
from classes import Instruction


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Instruction):
            return {
                'type': obj.type.name,
                'value': obj.value
            }
        return super(CustomJSONEncoder, self).default(obj)
