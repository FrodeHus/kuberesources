from kubernetes import config, client
from PyInquirer import prompt
import sys, re, math

class Kube():
    context: str
    showPodInfo: bool = False
    showAutoScalers: bool = False
    api: client.CoreV1Api

    def selectContext(self, contextName = None):
        contexts, activeContext = config.list_kube_config_contexts()
        if not contexts:
            print("No contexts found - please set up your kubeconfig file")
            sys.exit(2)
        if len(contexts) == 1:
            self.context = activeContext["name"]
        elif contextName:
            self.context = contextName
        else:
            contextNames = [context['name'] for context in contexts]
            options = [
            {
                "type": "list",
                "message": "Select kubernetes context",
                "name": "context",
                "choices": contextNames
            },
            {
                "type":"checkbox",
                "message": "Show additional data per pod",
                "name": "extra",
                "choices":[
                    {
                        "name": "pod"
                    },
                    {
                        "name": "autoscalers",
                        "disabled": "To be implemented"
                    }
                ]
            }
            ]
            selected = prompt(options)
            self.context = selected["context"]
            self.showPodInfo = "pod" in selected["extra"]

        self.api = client.CoreV1Api(api_client=config.new_client_from_config(context=self.context))

    def getAutoScalers(self) -> client.V2beta2HorizontalPodAutoscalerList :
        hpaClient = client.AutoscalingV2beta2Api(config.new_client_from_config(context=self.context))
        autoscalers = hpaClient.list_horizontal_pod_autoscaler_for_all_namespaces()
        return autoscalers
        

class Parsers():
    @staticmethod
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

    @staticmethod
    def parseCpuResourceValue(value):
        match = re.match(r'^([0-9]+)m$', value)
        if match is not None:
            return int(match.group(1))
        return int(value) * 1000