# Smart File Search - GitOps Deployment

This guide explains how to deploy the Smart File Search application to the [single-node-gitops](https://github.com/arnabdey73/single-node-gitops) platform.

## Prerequisites

1. **GitOps Platform Setup**: Ensure the single-node GitOps platform is running
   ```bash
   git clone https://github.com/arnabdey73/single-node-gitops
   cd single-node-gitops
   ./install.sh
   ```

2. **Tools Required**:
   - kubectl (configured to access your K3s cluster)
   - Docker
   - Git

3. **Access Information**:
   - K3s cluster running
   - ArgoCD available at `http://[NODE-IP]:30415`
   - Container registry at `http://[NODE-IP]:30500`

## Quick Deployment

### Option 1: Automated Deployment (Recommended)

1. **Clone and prepare the repository**:
   ```bash
   git clone <your-repo-url>
   cd smart-file-search
   ```

2. **Configure your OpenAI API key** (required for AI features):
   ```bash
   # Edit the secret file
   echo -n "your-actual-openai-api-key" | base64
   # Copy the output and replace the value in k8s/secret.yaml
   ```

3. **Run the deployment script**:
   ```bash
   chmod +x deploy-gitops.sh
   ./deploy-gitops.sh deploy
   ```

4. **Access the application**:
   - The script will show the access URLs
   - Default NodePort: `http://[NODE-IP]:30900`

### Option 2: Manual Deployment

1. **Build and push the Docker image**:
   ```bash
   # Build the image
   docker build -t smart-file-search:latest .
   
   # Tag for the registry
   docker tag smart-file-search:latest localhost:30500/smart-file-search:latest
   
   # Push to registry
   docker push localhost:30500/smart-file-search:latest
   ```

2. **Update the deployment manifest**:
   ```bash
   # Edit k8s/deployment.yaml and update the image reference
   sed -i 's|image: smart-file-search:latest|image: localhost:30500/smart-file-search:latest|g' k8s/deployment.yaml
   ```

3. **Deploy to Kubernetes**:
   ```bash
   kubectl apply -f k8s/
   ```

4. **Wait for deployment**:
   ```bash
   kubectl wait --for=condition=available --timeout=300s deployment/smart-file-search -n smart-file-search
   ```

### Option 3: GitOps with ArgoCD

1. **Fork this repository** to your GitHub account

2. **Update the ArgoCD application manifest**:
   ```bash
   # Edit k8s/argocd-application.yaml
   # Replace the repoURL with your forked repository URL
   ```

3. **Apply the ArgoCD application**:
   ```bash
   kubectl apply -f k8s/argocd-application.yaml
   ```

4. **Monitor in ArgoCD UI**:
   - Access ArgoCD at `http://[NODE-IP]:30415`
   - Login with admin credentials
   - Watch the application sync and deploy

## Configuration

### Environment Variables

The application supports the following configuration options via ConfigMap:

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_SERVER_NAME` | `smart-file-search` | Server identifier |
| `MCP_HOST` | `0.0.0.0` | Server bind address |
| `MCP_PORT` | `9000` | Server port |
| `DEBUG` | `false` | Enable debug logging |
| `LOG_LEVEL` | `INFO` | Logging level |
| `DB_PATH` | `/app/data/file_index.sqlite3` | Database file path |
| `MAX_FILE_SIZE` | `10485760` | Maximum file size (10MB) |
| `ALLOWED_ROOTS` | `/app/data,/app/sample_data` | Allowed index directories |

### Secrets

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key for AI features (required) |

To update the OpenAI API key:
```bash
kubectl create secret generic smart-file-search-secrets \
  --from-literal=OPENAI_API_KEY=your-api-key \
  --namespace=smart-file-search \
  --dry-run=client -o yaml | kubectl apply -f -
```

## Storage

The application uses persistent storage:
- **PVC**: `smart-file-search-data` (10Gi)
- **Storage Class**: `local-path` (K3s default)
- **Mount Path**: `/app/data`

## Networking

### Services

1. **ClusterIP Service**: `smart-file-search-service:9000`
   - Internal cluster access
   - Used by other services within the cluster

2. **NodePort Service**: `smart-file-search-nodeport:30900`
   - External access from outside the cluster
   - Access via `http://[NODE-IP]:30900`

### Ingress (Optional)

To add ingress support, create an ingress resource:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: smart-file-search-ingress
  namespace: smart-file-search
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: smart-file-search.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: smart-file-search-service
            port:
              number: 9000
```

## Monitoring and Health Checks

### Health Endpoints

- **Health Check**: `GET /health`
- **Service Info**: `GET /`

### Kubernetes Probes

The deployment includes:
- **Liveness Probe**: Checks if the application is running
- **Readiness Probe**: Checks if the application is ready to serve traffic

### Monitoring Integration

The platform includes Prometheus and Grafana. To add custom metrics:

1. Expose metrics endpoint in your application
2. Add ServiceMonitor for Prometheus discovery
3. Create Grafana dashboards

## API Endpoints

| Endpoint | Method | Description |
|----------|---------|-------------|
| `/` | GET | Service information |
| `/health` | GET | Health check |
| `/tools/indexFolder` | POST | Index a folder |
| `/tools/searchFiles` | POST | Search indexed files |
| `/tools/openFile` | POST | Open/preview file |
| `/tools/summarizeResults` | POST | Summarize search results |

### Example API Usage

```bash
# Health check
curl http://[NODE-IP]:30900/health

# Index a folder
curl -X POST http://[NODE-IP]:30900/tools/indexFolder \
  -H "Content-Type: application/json" \
  -d '{"path": "/app/sample_data"}'

# Search files
curl -X POST http://[NODE-IP]:30900/tools/searchFiles \
  -H "Content-Type: application/json" \
  -d '{"query": "python functions", "k": 5}'
```

## Troubleshooting

### Common Issues

1. **Pod not starting**:
   ```bash
   kubectl logs -n smart-file-search deployment/smart-file-search
   kubectl describe pod -n smart-file-search -l app.kubernetes.io/name=smart-file-search
   ```

2. **Image pull errors**:
   ```bash
   # Check if image is in registry
   curl http://[NODE-IP]:30500/v2/smart-file-search/tags/list
   ```

3. **Database issues**:
   ```bash
   # Check PVC
   kubectl get pvc -n smart-file-search
   
   # Check volume mounts
   kubectl exec -n smart-file-search deployment/smart-file-search -- ls -la /app/data
   ```

### Debugging Commands

```bash
# Get deployment status
./deploy-gitops.sh status

# View application logs
kubectl logs -n smart-file-search -l app.kubernetes.io/name=smart-file-search -f

# Get into pod shell
kubectl exec -n smart-file-search -it deployment/smart-file-search -- /bin/bash

# Check service endpoints
kubectl get endpoints -n smart-file-search

# Test internal connectivity
kubectl run test-pod --image=busybox -it --rm -- wget -O- http://smart-file-search-service.smart-file-search.svc.cluster.local:9000/health
```

### Cleanup

To remove the application:
```bash
./deploy-gitops.sh cleanup
```

Or manually:
```bash
kubectl delete namespace smart-file-search
```

## Integration with GitOps Platform

This application integrates with the single-node GitOps platform features:

1. **ArgoCD**: Automated deployment and sync
2. **Monitoring**: Prometheus metrics and Grafana dashboards
3. **Security**: Pod security policies and network policies
4. **Storage**: Persistent volumes with local-path provisioner
5. **Registry**: Local container registry for images

## Next Steps

1. **Setup monitoring dashboards** in Grafana
2. **Configure alerting** for application health
3. **Add ingress** for custom domain access
4. **Implement backup** for persistent data
5. **Setup CI/CD pipeline** for automated deployments

For more information about the GitOps platform, visit: https://github.com/arnabdey73/single-node-gitops
