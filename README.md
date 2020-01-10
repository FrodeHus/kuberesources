# Description

Utility for retrieving the status of resource requests across nodes in a Kubernetes cluster.  
Useful for planning capacity.

`./kuberesources.py` gives an overview of the reserved capacity for each node as well as total for the cluster  
`./kuberesources.py -v` lists pods' resource requests on each node, as well. 

## Sample output
![sample output](images/sample.png)


## Known issues
If using Azure AD as authentication, you might run into errors where it fails to authenticate.

Since this script merely loads your kubeconfig, it doesn't do any token refresh or anything like that - so, if when this problem pops up you can just issue a `kubectl <something>` command against your cluster and the tokens should be refreshed and the script can run.
