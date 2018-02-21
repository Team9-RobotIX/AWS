from flask.json import JSONEncoder
from classes import Instruction, Target


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Instruction):
            return {
                'type': obj.type.name,
                'value': obj.value
            }
        elif isinstance(obj, Target):
            res = {
                'id': obj.id,
                'name': obj.name
            }

            if obj.description is not None:
                res['description'] = obj.description

            if obj.color is not None:
                res['color'] = obj.color

            return res

        return super(CustomJSONEncoder, self).default(obj)
