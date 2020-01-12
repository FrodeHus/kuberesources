from .helpers import Parsers

class NodeData:
    totalCpuRequests = 0
    totalCpuLimits = 0
    totalMemRequests = 0
    totalCpuCapacity = 0
    totalMemCapacity = 0

    def __init__(self, nodename, capacity):
        self.cpuRequests = {}
        self.memRequests = {}
        self.cpuLimits = {}
        self.name = nodename
        self.cpuCapacity = int(capacity["cpu"]) * 1000
        self.memCapacity = Parsers.parseMemoryResourceValue(capacity["memory"])
        self.totalCpuRequests = 0
        self.totalMemRequests = 0
        self.totalCpuLimits = 0

        NodeData.totalCpuCapacity += self.cpuCapacity
        NodeData.totalMemCapacity += self.memCapacity

    def addCpuRequest(self, podName, cpuRequest):
        NodeData.totalCpuRequests += cpuRequest
        self.totalCpuRequests += cpuRequest
        self.cpuRequests[podName] = cpuRequest
    
    def addCpuLimit(self, podName, cpuLimit):
        NodeData.totalCpuLimits += cpuLimit
        self.totalCpuLimits += cpuLimit
        self.cpuLimits[podName] = cpuLimit

    def addMemRequest(self, podName, memRequest):
        NodeData.totalMemRequests += memRequest
        self.totalMemRequests += memRequest
        self.memRequests[podName] = memRequest
