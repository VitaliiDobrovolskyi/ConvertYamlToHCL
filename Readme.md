**ConvertYamlToHCL Kubernetes-alpha**

This is a converter for the Terraform kubernetes-alpha provider. It converts all yaml files in a directory.
It splits files internally with "---" separator and creates each separate resource with a .tf file. You don't need to prepare the yaml file before running the converter

Unfortunately, the kubernetes-alpha provider does not currently work with all kubernetes CRD resources.
I was able to run 1 of 3 tested resources (ECK, Zalando-Postgres, Percona-xtradb-cluster-operator). Percona-xtradb-cluster-operator worked with operator error. So for now, you can use it for simple Kubernetes resources, or try to get lucky with some complex resource.

**Usage**:
- Install all required libraries
- Specify the absolute directory path to the variable  directory_path