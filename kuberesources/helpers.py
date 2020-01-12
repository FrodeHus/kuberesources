from kubernetes import config, client
from pick import pick
import sys, re, math

class Kube():
    def selectContext():
        contexts, activeContext = config.list_kube_config_contexts()
        if not contexts:
            print("No contexts found - please set up your kubeconfig file")
            sys.exit(2)
        if len(contexts) == 1:
            cluster = activeContext["name"]
        else:
            contextNames = [context['name'] for context in contexts]
            active = contextNames.index(activeContext["name"])
            cluster, _ = pick(contextNames, "Select cluster", default_index=active)

        return client.CoreV1Api(api_client=config.new_client_from_config(context=cluster)), cluster

class Parsers():
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