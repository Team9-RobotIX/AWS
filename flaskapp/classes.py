from enum import Enum


# A delivery contains packages
class DeliveryState(Enum):
    IN_QUEUE = 0,
    MOVING_TO_SOURCE = 1,
    AWAITING_AUTHENTICATION_SENDER = 2,
    AWAITING_PACKAGE_LOAD = 3,
    PACKAGE_LOAD_COMPLETE = 4,
    MOVING_TO_DESTINATION = 6,
    AWAITING_AUTHENTICATION_RECEIVER = 7,
    AWAITING_PACKAGE_RETRIEVAL = 8,
    PACKAGE_RETRIEVAL_COMPLETE = 9,
    COMPLETE = 10,

    UNKNOWN = 5


class Delivery:
    def __init__(self, id, fromTarget, toTarget, sender, receiver,
                 priority, name, description = None,
                 state = DeliveryState.IN_QUEUE,
                 minTemp = None, maxTemp = None, timeLimit = None):
        self.id = id
        self.fromTarget = fromTarget
        self.toTarget = toTarget
        self.name = name
        self.description = description
        self.priority = priority
        self.sender = sender
        self.receiver = receiver

        self.state = state
        self.minTemp = minTemp
        self.maxTemp = maxTemp
        self.timeLimit = timeLimit

        if(minTemp and maxTemp and minTemp > maxTemp):
            raise ValueError("Invalid temperatures")
        if(timeLimit and timeLimit < 0):
            raise ValueError("Invalid time limit")


# Describes an instruction to the robot
class InstructionType(Enum):
    MOVE = 0,
    TURN = 1


class Instruction:
    def __init__(self, type, value):
        self.type = type
        self.value = value

        if(not isinstance(type, InstructionType)):
            raise ValueError("Instruction type must be of type \
                             InstructionType")
        else:
            if(type == InstructionType.TURN):
                if(value < -180.0 or value > 180.0):
                    raise ValueError("Turn angle must be between -180.0 \
                                     and 180.0")

    @classmethod
    def from_dict(self, obj):
        """
        Takes in a dictionary (e.g.: instruction type as string) and returns
        a valid Instruction instance.
        """
        type = None
        value = None

        if(obj['type'] == 'MOVE'):
            type = InstructionType.MOVE
        elif(obj['type'] == 'TURN'):
            type = InstructionType.TURN
        else:
            raise ValueError("Invalid instruction type.")

        value = float(obj['value'])
        return Instruction(type, value)


# Describes a possible target location
class Target:
    def __init__(self, id, name, description = None, color = None):
        self.id = id
        self.name = name
        self.description = description
        self.color = color

        if(not isinstance(id, int)):
            raise ValueError("ID must be positive integer")
        elif(id < 0):
            raise ValueError("ID must be positive integer")
        elif(not isinstance(name, basestring)):         # NOQA
            raise ValueError("Name must be string")
        elif(description is not None and
             not isinstance(description, basestring)):  # NOQA
            raise ValueError("Description must be string")
        elif(color is not None and
             not isinstance(color, basestring)):        # NOQA
            raise ValueError("Color must be string")

    @classmethod
    def from_dict(self, obj):
        """
        Takes in a dictionary (e.g.: from JSON request) and returns
        a valid Target instance.
        """
        id = obj['id']
        name = obj['name']
        description = None
        color = None

        if 'description' in obj:
            description = obj['description']

        if 'color' in obj:
            color = obj['color']

        return Target(id, name, description, color)


class Robot:
    def __init__(self, id):
        self.id = id
        self.motor = False
        self.angle = 0.0
        self.distance = 0.0
        self.correction = 0.0
        self.lock = False
