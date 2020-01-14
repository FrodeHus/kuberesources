from .helpers import Parsers, Kube
from kubernetes.client.rest import ApiException
from kubernetes import client
from progress.bar import Bar
from colorama import Fore, Style

class KubeResources:
    def __init__(self, kubeClient : Kube):
        self.__kubeClient = kubeClient
        self.__nodeData = self.__getNodeData()
    
    def __getNodeData(self):
        allData = []
        try:
            nodes = self.__kubeClient.api.list_node(label_selector='!node-role.kubernetes.io/master')
            for node in nodes.items:            
                nodeName = node.metadata.name
                nodeData = NodeData(nodeName, node.status.capacity)
                pod_templates = self.__kubeClient.api.list_pod_for_all_namespaces(field_selector='spec.nodeName=%s,status.phase!=Failed,status.phase!=Succeeded' % nodeName)
                
                for template in pod_templates.items:
                    name = template.metadata.name
                    
                    requests = self.__parseResourceRequestsForAllContainers(template.spec.containers)
                    nodeData.addCpuRequest(name, requests["cpu"])
                    nodeData.addMemRequest(name, requests["mem"])

                    limits = self.__parseResourceLimitsForAllContainers(template.spec.containers)
                    nodeData.addCpuLimit(name, limits["cpu"])

                allData.append(nodeData)
 
        except ApiException as e:
            print("Error when attempting to read node data: %s\n" % e)            
        return allData

    def __parseResourceRequestsForAllContainers(self, containers):
        cpuRequests = 0
        memRequests = 0

        for container in containers:    
            if container.resources is None or container.resources.requests is None:
                continue
        
            requests = container.resources.requests
            if "cpu" in requests:
                cpuRequests += Parsers.parseCpuResourceValue(requests["cpu"])
            if "memory" in requests:
                memRequests += Parsers.parseMemoryResourceValue(requests["memory"])
        
        return {"cpu": cpuRequests, "mem": memRequests}

    def __parseResourceLimitsForAllContainers(self, containers):
        cpuLimits = 0
        memLimits = 0

        for container in containers:    
            if container.resources is None or container.resources.limits is None:
                continue
        
            limits = container.resources.limits
            if "cpu" in limits:
                cpuLimits += Parsers.parseCpuResourceValue(limits["cpu"])
            if "memory" in limits:
                memLimits += Parsers.parseMemoryResourceValue(limits["memory"])
        
        return {"cpu": cpuLimits, "mem": memLimits}
    
    def print(self, verbose : bool):
            print(Fore.GREEN + "Active kube context: {}".format(self.__kubeClient.context) + Style.RESET_ALL)
            for node in self.__nodeData:
                print(Fore.CYAN + "Node {:20}".format(node.name) + Style.RESET_ALL)

                barCpu = Bar("Requested CPU   ", max=node.cpuCapacity , suffix='%(percent)d%%', fill=Fore.YELLOW + "#" + Style.RESET_ALL)
                barCpu.goto(node.totalCpuRequests)
                barCpu.finish()
                barCpu = Bar("Limits CPU      ", max=node.cpuCapacity , suffix='%(percent)d%%', fill=Fore.YELLOW + "#" + Style.RESET_ALL)
                barCpu.goto(node.totalCpuLimits)
                barCpu.finish()
                barMem = Bar("Requested memory", max=node.memCapacity , suffix='%(percent)d%%', fill=Fore.YELLOW + "#" + Style.RESET_ALL)
                barMem.goto(node.totalMemRequests)
                barMem.finish()
                
                print()
                
                if verbose:
                    print("\t{:50}{:>5}{:>8}".format("POD", "CPU", "MEM"))
                    for pod in node.cpuRequests.keys():
                        if node.cpuRequests[pod] == 0:
                            continue
                        print("\t{:50}{:>5}{:>8}Mi".format(pod, node.cpuRequests[pod], int(node.memRequests[pod] / 1048576)))
                    print()

            print(Fore.CYAN + "\nTotal cluster utilization" + Style.RESET_ALL)
            barTotalCpu = Bar("Requested CPU   ", max=NodeData.totalCpuCapacity, suffix='%(percent)d%%', fill=Fore.YELLOW + "#" + Style.RESET_ALL)
            barTotalCpu.goto(NodeData.totalCpuRequests)
            barTotalCpu.finish()
            barTotalMem = Bar("Requested Memory", max=NodeData.totalMemCapacity, suffix='%(percent)d%%', fill=Fore.YELLOW + "#" + Style.RESET_ALL)
            barTotalMem.goto(NodeData.totalMemRequests)
            barTotalMem.finish()

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
