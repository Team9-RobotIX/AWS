from enum import Enum


# Describes the item added to the delivery
class Package:
    def __init__(self, id, name, description, priority, minTemp,
                 maxTemp, timeLimit):
        self.id = id
        self.name = name
        self.description = description
        self.priority = priority
        self.minTemp = minTemp
        self.maxTemp = maxTemp
        self.timeLimit = timeLimit
        if(minTemp > maxTemp):
            raise ValueError("Invalid temperatures")
        if(timeLimit < 0):
            raise ValueError("Invalid time limit")


# A delivery contains packages
class Delivery:
    def __init__(self, id, packageList, fromLoc, toLoc, state):
        self.id = id
        self.packageList = packageList
        self.fromLoc = fromLoc
        self.toLoc = toLoc
        # Lowest number has highest priority
        self.priority = min([x.priority for x in packageList])
        self.state = state
        if(len(packageList) < 1):
            raise ValueError("No packages")


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
