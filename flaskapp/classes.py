#Describes the item added to the delivery
class Package:
    def __init__(self, id, name, description, priority, minTemp, maxTemp, timeLimit):
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

#A delivery contains packages
class Delivery:
    def __init__(self, id, packageList, fromLoc, toLoc, state):
        self.id = id
        self.packageList = packageList
        self.fromLoc = fromLoc
        self.toLoc = toLoc
        self.priority = min([x.priority for x in packageList]) #lowest number highest priority
        self.state = state
        if(len(packageList) < 1):
            raise ValueError("No packages")
