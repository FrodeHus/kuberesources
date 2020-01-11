#!/usr/bin/env python3
import sys, getopt, urllib3
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from progress.bar import Bar
from colorama import Fore, Style
import helpers
import adal
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class NodeData:
    totalCpuRequests = 0
    totalMemRequests = 0
    totalCpuCapacity = 0
    totalMemCapacity = 0

    def __init__(self, nodename, capacity):
        self.cpuRequests = {}
        self.memRequests = {}
        self.name = nodename
        self.cpuCapacity = int(capacity["cpu"]) * 1000
        self.memCapacity = helpers.parseMemoryResourceValue(capacity["memory"])
        self.totalCpuRequests = 0
        self.totalMemRequests = 0

        NodeData.totalCpuCapacity += self.cpuCapacity
        NodeData.totalMemCapacity += self.memCapacity

    def addCpuRequest(self, podName, cpuRequest):
        NodeData.totalCpuRequests += cpuRequest
        self.totalCpuRequests += cpuRequest
        self.cpuRequests[podName] = cpuRequest

    def addMemRequest(self, podName, memRequest):
        NodeData.totalMemRequests += memRequest
        self.totalMemRequests += memRequest
        self.memRequests[podName] = memRequest

def main(argv):
    verbose = False
    try:
        opts, args = getopt.getopt(argv, "hv", ["verbose"])
    except getopt.GetoptError:
        print("{} [-v]".format(__file__))
        sys.exit(2)
    for opt, arg in opts:
        if opt == "-h":
            print("{} -v (optional) - Lists requests for each pod on the nodes".format(__file__))
            sys.exit(1)
        elif opt in ("-v", "--verbose"):
            verbose = True
    api = helpers.selectContext()

    try:
        allData = []
        nodes = api.list_node(label_selector='!node-role.kubernetes.io/master')
        for node in nodes.items:            
            nodeName = node.metadata.name
            nodeData = NodeData(nodeName, node.status.capacity)
            pod_templates = api.list_pod_for_all_namespaces(field_selector='spec.nodeName=%s,status.phase!=Failed,status.phase!=Succeeded' % nodeName)
            for template in pod_templates.items:
                name = template.metadata.name
                resources = parseResourcesForAllContainers(template.spec.containers)
                nodeData.addCpuRequest(name, resources["cpu"])
                nodeData.addMemRequest(name, resources["mem"])
            allData.append(nodeData)

        printResourceReport(allData, verbose)
    except ApiException as e:
        print("Error when attempting to read node data: %s\n" % e)

def printResourceReport(data, verbose : bool):
        for node in data:
            print(Fore.CYAN + "Node {:20}".format(node.name) + Style.RESET_ALL)

            barCpu = Bar("Requested CPU   ", max=node.cpuCapacity , suffix='%(percent)d%%', fill=Fore.YELLOW + "#" + Style.RESET_ALL)
            barCpu.goto(node.totalCpuRequests)
            barCpu.finish()
            barMem = Bar("Requested memory", max=node.memCapacity , suffix='%(percent)d%%', fill=Fore.YELLOW + "#" + Style.RESET_ALL)
            barMem.goto(node.totalMemRequests)
            barMem.finish()
            
            print()
            
            if verbose:
                for pod in node.cpuRequests.keys():
                    if node.cpuRequests[pod] == 0:
                        continue
                    print("\t{:50}{:>5}".format(pod, node.cpuRequests[pod]))
            
        print(Fore.CYAN + "\nTotal cluster utilization" + Style.RESET_ALL)
        barTotalCpu = Bar("Requested CPU   ", max=NodeData.totalCpuCapacity, suffix='%(percent)d%%', fill=Fore.YELLOW + "#" + Style.RESET_ALL)
        barTotalCpu.goto(NodeData.totalCpuRequests)
        barTotalCpu.finish()
        barTotalMem = Bar("Requested Memory", max=NodeData.totalMemCapacity, suffix='%(percent)d%%', fill=Fore.YELLOW + "#" + Style.RESET_ALL)
        barTotalMem.goto(NodeData.totalMemRequests)
        barTotalMem.finish()

def parseResourcesForAllContainers(containers):
    cpuRequests = 0
    memRequests = 0

    for container in containers:    
        if container.resources is None or container.resources.requests is None:
            continue
    
        requests = container.resources.requests
        if "cpu" in requests:
            cpuRequests += helpers.parseCpuResourceValue(requests["cpu"])
        if "memory" in requests:
            memRequests += helpers.parseMemoryResourceValue(requests["memory"])
    
    return {"cpu": cpuRequests, "mem": memRequests}


if __name__ == "__main__":
    main(sys.argv[1:])
