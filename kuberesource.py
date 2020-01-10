#!/usr/bin/env python3
import sys, getopt, re, urllib3, math
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from progress.bar import Bar
from colorama import Fore, Style
import adal
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class NodeData:
    totalCpuRequests = 0
    totalMemRequests = 0

    def __init__(self, nodename, capacity):
        super().__init__()
        self.cpuRequests = {}
        self.memRequests = {}
        self.name = nodename
        self.cpuCapacity = int(capacity["cpu"]) * 1000
        self.memCapacity = parseMemoryResourceValue(capacity["memory"])
        self.totalCpuRequests = 0
        self.totalMemRequests = 0

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
            print("{} [-v]".format(__file__))
            sys.exit(1)
        elif opt in ("-v", "--verbose"):
            verbose = True
    config.load_kube_config()
    api = client.CoreV1Api()

    try:
        allData = []
        nodes = api.list_node()
        for node in nodes.items:
            nodeName = node.metadata.name
            nodeData = NodeData(nodeName, node.status.capacity)
            pod_templates = api.list_pod_for_all_namespaces(
                field_selector='spec.nodeName=%s,status.phase!=Failed,status.phase!=Succeeded' % nodeName)
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

def parseResourcesForAllContainers(containers):
    cpuRequests = 0
    memRequests = 0

    for container in containers:    
        if container.resources is None or container.resources.requests is None:
            continue
    
        requests = container.resources.requests
        if "cpu" in requests:
            cpuRequests += parseCpuResourceValue(requests["cpu"])
        if "memory" in requests:
            memRequests += parseMemoryResourceValue(requests["memory"])
    
    return {"cpu": cpuRequests, "mem": memRequests}

def parseMemoryResourceValue(value):
    match = re.match(r'^([0-9]+)(E|Ei|P|Pi|T|Ti|G|g|Gi|M|Mi|m|K|k|Ki){0,1}$', value)
    if match is None:
        return int(value)
    amount = match.group(1)
    eom = match.group(2).capitalize()
    
    calc = {
        "Ki": math.pow(1024,1),
        "K": 1000,
        "Mi": math.pow(1024,2),
        "M": 1000000,
        "Gi": math.pow(1024,3),
        "G": 1000000000
    }

    return int(amount) * calc.get(eom)

def parseCpuResourceValue(value):
    match = re.match(r'^([0-9]+)m$', value)
    if match is not None:
        return int(match.group(1))
    return int(value) * 1000


if __name__ == "__main__":
    main(sys.argv[1:])
