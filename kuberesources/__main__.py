import sys, getopt, urllib3
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from progress.bar import Bar
from colorama import Fore, Style
from .entities import NodeData
from .helpers import Kube, Parsers
import adal
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def main():
    argv = sys.argv[1:]
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
    api, contextName = Kube.selectContext()
    print(Fore.GREEN + "Active kube context: {}".format(contextName) + Style.RESET_ALL)
    try:
        allData = []
        nodes = api.list_node(label_selector='!node-role.kubernetes.io/master')
        for node in nodes.items:            
            nodeName = node.metadata.name
            nodeData = NodeData(nodeName, node.status.capacity)
            pod_templates = api.list_pod_for_all_namespaces(field_selector='spec.nodeName=%s,status.phase!=Failed,status.phase!=Succeeded' % nodeName)
            for template in pod_templates.items:
                name = template.metadata.name
                requests = parseResourceRequestsForAllContainers(template.spec.containers)
                nodeData.addCpuRequest(name, requests["cpu"])
                nodeData.addMemRequest(name, requests["mem"])

                limits = parseResourceLimitsForAllContainers(template.spec.containers)
                nodeData.addCpuLimit(name, limits["cpu"])

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
            barCpu = Bar("Limits CPU      ", max=node.cpuCapacity , suffix='%(percent)d%%', fill=Fore.YELLOW + "#" + Style.RESET_ALL)
            barCpu.goto(node.totalCpuLimits)
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

def parseResourceRequestsForAllContainers(containers):
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

def parseResourceLimitsForAllContainers(containers):
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

if __name__ == "__main__":
    main()
