import sys, getopt, urllib3
from .entities import KubeResources
from .helpers import Kube
import adal
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def main():
    argv = sys.argv[1:]
    contextName : str = None
    kube = Kube()
    try:
        opts, _ = getopt.getopt(argv, "hvc:", ["verbose", "context="])
    except getopt.GetoptError:
        printHelp()
        sys.exit(2)

    for opt, arg in opts:
        if opt == "-h":
            printHelp()
            sys.exit(1)
        if opt in ("-v", "--verbose"):
            kube.showPodInfo = True

        if opt in ("-c", "--context"):
            contextName = arg

    kube.selectContext(contextName)

    resourceView = KubeResources(kube)
    resourceView.print()    

def printHelp():
    print("{} -v (optional) \t\t Lists requests for each pod on the nodes".format(__file__))
    print("{} -c contextName(optional)\tSpecify context".format(__file__))

if __name__ == "__main__":
    main()
