# Smart File Search - GitOps Deployment Summary

## 🚀 Ready for Deployment

Your Smart File Search application is now prepared for deployment to the [single-node-gitops](https://github.com/arnabdey73/single-node-gitops) platform!

## 📁 What's Been Created

### Kubernetes Manifests (`k8s/`)
- `namespace.yaml` - Application namespace
- `configmap.yaml` - Configuration settings
- `secret.yaml` - OpenAI API key storage
- `pvc.yaml` - Persistent volume for data
- `deployment.yaml` - Main application deployment
- `service.yaml` - ClusterIP and NodePort services
- `argocd-application.yaml` - ArgoCD application definition

### Container Setup
- `Dockerfile` - Multi-stage production-ready container
- `.dockerignore` - Optimized build context

### Deployment Tools
- `deploy-gitops.sh` - Automated deployment script
- `Makefile` - Development and deployment shortcuts
- `DEPLOYMENT.md` - Comprehensive deployment guide

## 🎯 Quick Start

### Prerequisites
1. **GitOps Platform Running**:
   ```bash
   git clone https://github.com/arnabdey73/single-node-gitops
   cd single-node-gitops
   ./install.sh
   ```

2. **Configure OpenAI API Key**:
   ```bash
   # Get base64 encoded key
   echo -n "your-openai-api-key" | base64
   
   # Edit k8s/secret.yaml and replace the OPENAI_API_KEY value
   ```

### Deploy Options

#### Option 1: Automated (Recommended)
```bash
# Make script executable and deploy
chmod +x deploy-gitops.sh
./deploy-gitops.sh deploy
```

#### Option 2: Using Makefile
```bash
# Build and deploy
make deploy

# Or for local development
make deploy-local
```

#### Option 3: Manual Kubernetes
```bash
# Apply all manifests
kubectl apply -f k8s/
```

## 🌐 Access Your Application

After deployment, your application will be available at:

- **External Access**: `http://[NODE-IP]:30900`
- **Internal Access**: `http://smart-file-search-service.smart-file-search.svc.cluster.local:9000`
- **Health Check**: `http://[NODE-IP]:30900/health`

## 🔧 Management Commands

```bash
# Check deployment status
./deploy-gitops.sh status
# or
make status

# View logs
make logs

# Restart application
make restart

# Cleanup
./deploy-gitops.sh cleanup
# or
make cleanup
```

## 📊 GitOps Platform Integration

Your application integrates with:

1. **ArgoCD**: Automated GitOps deployment
   - Access: `http://[NODE-IP]:30415`
   - Application: `smart-file-search`

2. **Monitoring**: Prometheus & Grafana
   - Grafana: `http://[NODE-IP]:30300`
   - Health checks and metrics ready

3. **Container Registry**: Local registry
   - Registry: `http://[NODE-IP]:30500`
   - Image: `smart-file-search:latest`

## 🔐 Security Features

- Non-root container user (UID 1000)
- Read-only root filesystem capability
- Security context with dropped capabilities
- Secret management for API keys
- Network policies ready

## 📈 Monitoring & Health

- **Health Endpoint**: `/health`
- **Liveness Probe**: HTTP health check
- **Readiness Probe**: Service availability
- **Resource Limits**: CPU and memory constraints

## 🗄️ Data Persistence

- **Persistent Volume**: 10Gi local storage
- **Database**: SQLite with FTS5
- **Mount Path**: `/app/data`
- **Backup Ready**: Standard PVC backup tools

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|---------|-------------|
| `/health` | GET | Health check |
| `/` | GET | Service info |
| `/tools/indexFolder` | POST | Index files in folder |
| `/tools/searchFiles` | POST | Search indexed content |
| `/tools/openFile` | POST | Preview file content |
| `/tools/summarizeResults` | POST | AI-powered summaries |

## 🎛️ Configuration

### Environment Variables (ConfigMap)
- `MCP_HOST`: `0.0.0.0`
- `MCP_PORT`: `9000`
- `DB_PATH`: `/app/data/file_index.sqlite3`
- `MAX_FILE_SIZE`: `10485760` (10MB)
- `LOG_LEVEL`: `INFO`

### Secrets
- `OPENAI_API_KEY`: Required for AI features

## 🚨 Troubleshooting

### Common Issues

1. **Pod not starting**: Check logs with `make logs`
2. **Service not accessible**: Verify NodePort 30900 is open
3. **Database errors**: Check PVC mounting with `make shell`
4. **API key issues**: Verify secret configuration

### Debug Commands
```bash
# Get pod shell
make shell

# Port forward for local testing
make port-forward

# Check resource status
make status

# View detailed pod information
kubectl describe pod -n smart-file-search -l app.kubernetes.io/name=smart-file-search
```

## 🔄 CI/CD Integration

### GitOps Workflow
1. **Code Push** → GitHub repository
2. **ArgoCD Sync** → Detects changes
3. **Automatic Deploy** → Updates application
4. **Health Checks** → Validates deployment

### Manual Updates
```bash
# Update image tag in deployment.yaml
# Commit changes to repository
# ArgoCD will automatically sync
```

## 📚 Next Steps

1. **Setup Custom Domain**: Configure ingress for custom URLs
2. **Monitoring Dashboards**: Create Grafana dashboards
3. **Backup Strategy**: Implement data backup procedures
4. **Scaling**: Configure horizontal pod autoscaling
5. **Security Hardening**: Add network policies

## 🤝 Platform Features Used

✅ **K3s Kubernetes**: Lightweight container orchestration  
✅ **ArgoCD**: GitOps continuous deployment  
✅ **Local Storage**: Persistent data with local-path  
✅ **Container Registry**: Local image storage  
✅ **Monitoring**: Prometheus & Grafana ready  
✅ **Security**: Pod security standards  
✅ **Networking**: NodePort and ClusterIP services  

## 📞 Support

- **Platform Docs**: [single-node-gitops documentation](https://github.com/arnabdey73/single-node-gitops/docs)
- **Application Issues**: Check logs and health endpoints
- **GitOps Questions**: Refer to ArgoCD documentation

---

**Your Smart File Search application is ready for the GitOps platform! 🎉**

Start with: `./deploy-gitops.sh deploy`
