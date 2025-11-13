# ArgoCD Installation Manifests

This directory contains the ArgoCD installation manifests organized by resource type for better maintainability and clarity.

## File Organization

The manifests are split into the following files (numbered for installation order):

1. **01-crds.yaml** - CustomResourceDefinitions (3 resources)
   - Applications CRD
   - ApplicationSets CRD
   - AppProjects CRD

2. **02-serviceaccounts.yaml** - ServiceAccounts (7 resources)
   - Service accounts for ArgoCD components

3. **03-roles.yaml** - Roles (6 resources)
   - Namespace-scoped roles for ArgoCD components

4. **04-clusterroles.yaml** - ClusterRoles (3 resources)
   - Cluster-wide roles for ArgoCD

5. **05-rolebindings.yaml** - RoleBindings (6 resources)
   - Bindings for namespace-scoped roles

6. **06-clusterrolebindings.yaml** - ClusterRoleBindings (3 resources)
   - Bindings for cluster-wide roles

7. **07-configmaps.yaml** - ConfigMaps (7 resources)
   - Configuration data for ArgoCD components

8. **08-secrets.yaml** - Secrets (2 resources)
   - Sensitive configuration data

9. **09-services.yaml** - Services (8 resources)
   - Kubernetes services for ArgoCD components

10. **10-deployments.yaml** - Deployments (6 resources)
    - Stateless ArgoCD components

11. **11-statefulsets.yaml** - StatefulSets (1 resource)
    - Stateful ArgoCD components (application controller)

12. **12-networkpolicies.yaml** - NetworkPolicies (7 resources)
    - Network policies for ArgoCD components

## Installation

### Install All Resources

To install all ArgoCD resources in the correct order:

```bash
kubectl apply -n argocd -f argocd/
```

### Install Individual Resource Types

To install specific resource types:

```bash
kubectl apply -f argocd/01-crds.yaml
kubectl apply -f argocd/02-serviceaccounts.yaml
# ... and so on
```

### Install with Kustomize

You can also use kustomize by creating a `kustomization.yaml`:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - 01-crds.yaml
  - 02-serviceaccounts.yaml
  - 03-roles.yaml
  - 04-clusterroles.yaml
  - 05-rolebindings.yaml
  - 06-clusterrolebindings.yaml
  - 07-configmaps.yaml
  - 08-secrets.yaml
  - 09-services.yaml
  - 10-deployments.yaml
  - 11-statefulsets.yaml
  - 12-networkpolicies.yaml
```

Then apply:

```bash
kubectl apply -k argocd/
```

## Uninstallation

To remove all ArgoCD resources:

```bash
kubectl delete -f argocd/
```

## Notes

- These manifests are auto-generated from the official ArgoCD installation manifest
- The files are numbered to reflect the recommended installation order
- CRDs must be installed first before other resources
- All resources will be created in the namespace specified in the manifests (typically `argocd`)

