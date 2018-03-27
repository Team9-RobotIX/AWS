from flask.json import JSONEncoder
from classes import Instruction, Target, Delivery, DeliveryState


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
        elif isinstance(obj, DeliveryState):
            return obj.name
        elif isinstance(obj, Delivery):
            res = {
                'id': obj.id,
                'name': obj.name,
                'priority': obj.priority,
                'from': obj.fromTarget,
                'to': obj.toTarget,
                'state': obj.state,
                'sender': obj.sender,
                'receiver': obj.receiver
            }

            if obj.robot is not None:
                res['robot'] = obj.robot

            if obj.description is not None:
                res['description'] = obj.description

            return res

        return super(CustomJSONEncoder, self).default(obj)
