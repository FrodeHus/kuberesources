import sys, getopt, urllib3
from .entities import KubeResources
from .helpers import Kube
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
    kube = Kube()
    kube.selectContext()
    resourceView = KubeResources(kube)
    resourceView.print(verbose=verbose)

if __name__ == "__main__":
    main()
