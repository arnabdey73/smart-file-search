# Smart File Search System

**Windows Network Folder Edition** - A production-ready intelligent document search system optimized for Windows network folders with simple search functionality prioritized.

## 📋 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Windows Network Folders](#windows-network-folders)
- [Search Features](#search-features)
- [AI Enhancement](#ai-enhancement)
- [Supported File Types](#supported-file-types)
- [Configuration](#configuration)
- [Architecture](#architecture)
- [Manual Setup](#manual-setup)
- [Security Features](#security-features)
- [Performance](#performance)
- [Troubleshooting](#troubleshooting)
- [GitOps CI/CD Deployment](#gitops-cicd-deployment)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

This system is specifically designed for searching across Windows network folders (UNC paths) with an emphasis on simplicity and speed. It provides:

- **Windows Network Folder Support**: Search across `\\server\share` paths
- **Simple Search Priority**: Fast, straightforward search over complex features  
- **Real-time Path Validation**: Verify network folder accessibility
- **Quick Indexing**: Fast file discovery and content extraction
- **Native Windows Deployment**: No Docker or virtualization required
- **Multi-format Support**: PDF, DOCX, PPTX, XLSX, text files, and more
- **Optional AI Enhancement**: GPT-4o-mini for query improvement and summarization

## 🚀 Quick Start

### 🌐 Web-Based Access (Production)

The Smart File Search system is **hosted on the GitOps platform** and accessed entirely through the web interface:

**Access URL**: [Your GitOps Platform URL]/smart-file-search

**No local installation required** - simply open the web UI in your browser and start using the system immediately.

### Using the Web Interface
1. **Access the Application**: Navigate to the hosted web UI
2. **Add Network Folder**: Enter UNC path like `\\fileserver\documents`
3. **Validate Path**: System checks accessibility and shows file count
4. **Index Folder**: Click to start indexing (quick scan recommended)
5. **Search Files**: Use natural language queries to find documents

### 🛠️ Local Development (Optional)

For developers who need to run locally:

```batch
scripts\start_all.bat
```

This will start:
- Backend server (http://localhost:8000)
- Frontend UI (http://localhost:3000)

## 🗂️ Windows Network Folders

### Supported Path Formats
```
\\fileserver\departments\hr     # UNC paths (recommended)
\\nas\projects\active\2024      # Network shares
\\server\share\subfolder        # Deep folder paths
C:\Shared\NetworkFolders        # Local folders also supported
```

### Network Folder Features
- **Real-time Validation**: Instant feedback on path accessibility
- **Quick Scan Mode**: Index only new/modified files for speed
- **Multi-folder Support**: Index and search across multiple network locations
- **Access Control**: Automatic handling of permission restrictions

## 🤖 AI Enhancement

The system includes powerful AI capabilities powered by OpenAI GPT-4o-mini:

### AI Features
- **Query Enhancement**: Transform natural language into optimized search terms
- **Smart Summarization**: AI-generated summaries of search results  
- **Related Queries**: Intelligent suggestions for follow-up searches
- **Context Understanding**: Better matching through semantic analysis

### Usage
1. **Enable AI**: Check the "🤖 AI-Enhanced Search" checkbox in the web interface
2. **Natural Queries**: Use conversational language like "meeting notes from last week"
3. **View Results**: See enhanced queries, summaries, and related suggestions

### Configuration
```bash
# In .env file
OPENAI_API_KEY=your_api_key_here
ENABLE_AI_FEATURES=true
ENABLE_QUERY_REWRITE=true
ENABLE_SUMMARIZATION=true
```

For detailed AI features documentation, see [docs/ai-features.md](docs/ai-features.md).

## 🔍 Search Features

### Core Search Capabilities
- **Full-Text Search**: SQLite FTS5 for fast content searching
- **File Type Filtering**: Search specific document types
- **Real-time Results**: Instant search as you type
- **Snippet Highlighting**: Context around matching content
- **Multi-folder Search**: Search across all indexed network folders

### Advanced Features
- **Boolean Search**: Use AND, OR, NOT operators
- **Phrase Search**: Exact phrase matching with quotes
- **Wildcard Search**: Pattern matching with * and ?
- **Date Filtering**: Search by file modification dates
- **Size Filtering**: Find files by size ranges

## 📄 Supported File Types

The system supports a wide range of document formats:

| Format | Library | Content Extraction |
|--------|---------|-------------------|
| PDF | PyPDF2 | ✓ Text content |
| DOCX | python-docx | ✓ Full document text |
| PPTX | python-pptx | ✓ Slide content |
| XLSX/XLS | openpyxl | ✓ Cell data |
| CSV | csv (built-in) | ✓ All rows/columns |
| TXT/MD | built-in | ✓ Full content |
| HTML/XML | BeautifulSoup4 | ✓ Text extraction |
| ZIP | zipfile | ✓ Archive listing |

   cp .env.example .env
   # Edit .env with your settings
   ```

2. **Docker Deployment**
   ```bash
   docker-compose up --build
   ```

3. **Access the Application**
   - Frontend: http://localhost:8080
   - API: http://localhost:8081
   - Health: http://localhost:8081/healthz

## Configuration

### Environment Variables

- `GPT_API_KEY`: OpenAI API key for AI features
- `DB_PATH`: SQLite database path (default: ./data/file_index.sqlite3)
- `ALLOWED_ROOTS`: Comma-separated allowed root directories
- `UI_BACKEND_PORT`: Backend API port (default: 8081)
- `UI_FRONTEND_PORT`: Frontend port (default: 8080)
- `MCP_PORT`: MCP server port (default: 9000)

### Security Settings

The system implements multiple security layers:
- **Path Allowlists**: Only configured directories can be indexed
- **Content Redaction**: Automatic removal of emails, tokens, credit cards
- **Snippet Limits**: Content size restrictions for AI processing
- **Rate Limiting**: API request throttling

## Architecture

```
User → React Frontend → FastAPI Backend → MCP Server
                                      ├─ Search Agent (SQLite FTS5)
                                      └─ GPT-4.1 mini (Query + Summary)
```

### Components

- **MCP Server**: Model Context Protocol server exposing search tools
- **Search Agent**: File indexing and search using SQLite FTS5
- **LLM Client**: GPT-4.1 mini integration for AI features  
- **UI Backend**: FastAPI REST API for frontend communication
- **Frontend**: React + TypeScript + Tailwind CSS interface

## API Endpoints

### Search
```
GET /api/search?query=python&k=10&exts=.py,.js
```

### File Preview
```
GET /api/file-preview?path=/path/to/file&pointer=chunk_1
```

### Summarization
```
POST /api/summarize
{
  "query": "search terms",
  "results": [...],
  "style": "bullets"
}
```

## Development

### Local Setup

1. **Python Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```

2. **Frontend Setup**
   ```bash
   cd ui/frontend
   npm install
   npm run dev
   ```

3. **Backend Services**
   ```bash
   # MCP Server
   python -m mcp_server.server

   # UI Backend
   cd ui/backend
   python api_network_main.py
   ```

### Testing

```bash
# Python tests
pytest tests/

# Frontend tests
cd ui/frontend
npm test
```

### Code Quality

```bash
# Python linting
black .
ruff check .
mypy .

# Frontend linting
cd ui/frontend
npm run lint
npm run type-check
```

## Deployment

### Docker Compose

The included `docker-compose.yaml` provides a complete deployment:

```bash
# Production deployment
docker-compose -f docker/docker-compose.yaml up -d

# Development with rebuild
docker-compose up --build
```

### Health Monitoring

- **Health Endpoint**: `/healthz`
- **Structured Logging**: JSON format with correlation IDs
- **Metrics**: Request timing and error rates

## GitOps CI/CD Deployment

### 🌐 Web-Hosted Application

The Smart File Search system is designed to be **hosted on your GitOps platform** and accessed entirely through the web interface. Users connect via web browser to search Windows network folders without any local installation required.

#### Production Deployment Model
```
GitOps Platform (Kubernetes)
├── 🌐 Web Frontend (React) - Public access via browser
├── ⚙️ API Backend (FastAPI) - Internal network folder access  
├── 💾 SQLite Database - Persistent indexing data
└── 🔗 Network Mounts - Windows share connectivity (\\server\share)
```

### GitOps Platform Support

This application includes comprehensive support for the [single-node-gitops](https://github.com/arnabdey73/single-node-gitops) platform:

- **🚀 ArgoCD Integration**: Automated GitOps deployment and synchronization
- **☸️ Kubernetes Manifests**: Complete K8s deployment configuration optimized for web access
- **📦 Container Registry**: Local registry support with automated image builds
- **📊 Monitoring Integration**: Prometheus metrics and Grafana dashboards ready
- **🔒 Security Hardening**: Pod security standards and network policies
- **🌐 Web Access**: Ingress/LoadBalancer configured for browser access
- **📁 Network Folder Support**: Windows share mounting and access from containers

### Quick GitOps Deployment

1. **Prerequisites**: Ensure GitOps platform is running
   ```bash
   git clone https://github.com/arnabdey73/single-node-gitops
   cd single-node-gitops
   ./install.sh
   ```

2. **Configure Secrets**: Set up your OpenAI API key
   ```bash
   # Encode your API key
   echo -n "your-openai-api-key" | base64
   
   # Edit k8s/secret.yaml with the encoded value
   ```

3. **Deploy Application**: Use the automated deployment script
   ```bash
   chmod +x deploy-gitops.sh
   ./deploy-gitops.sh deploy
   ```

4. **Access Services**:
   - Application: `http://[NODE-IP]:30900`
   - Health Check: `http://[NODE-IP]:30900/health`
   - ArgoCD UI: `http://[NODE-IP]:30415`

### GitOps Features

#### Automated Deployment Pipeline
```mermaid
graph LR
    A[Code Push] --> B[Container Build]
    B --> C[Registry Push]
    C --> D[ArgoCD Sync]
    D --> E[K8s Deploy]
    E --> F[Health Check]
    F --> G[Monitoring]
```

#### Kubernetes Resources
- **Namespace**: `smart-file-search`
- **Deployment**: High-availability with rolling updates
- **Services**: ClusterIP (internal) + NodePort (external)
- **Storage**: 10Gi persistent volume for search index
- **ConfigMaps**: Environment configuration
- **Secrets**: Secure API key management

#### CI/CD Integration
```yaml
# ArgoCD Application (k8s/argocd-application.yaml)
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: smart-file-search
spec:
  project: default
  source:
    repoURL: https://github.com/your-username/smart-file-search
    targetRevision: HEAD
    path: k8s
  destination:
    server: https://kubernetes.default.svc
    namespace: smart-file-search
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

### Management Commands

#### Using Make
```bash
# Build and deploy
make deploy

# Check status
make status

# View logs
make logs

# Restart deployment
make restart

# Cleanup
make cleanup
```

#### Using Deployment Script
```bash
# Deploy application
./deploy-gitops.sh deploy

# Check deployment status
./deploy-gitops.sh status

# Remove application
./deploy-gitops.sh cleanup
```

### Platform Integration

#### Monitoring & Observability
- **Prometheus Metrics**: Application performance monitoring
- **Grafana Dashboards**: Visual monitoring and alerting
- **Health Probes**: Kubernetes liveness and readiness checks
- **Structured Logging**: Centralized log aggregation

#### Security & Compliance
- **Pod Security Standards**: Non-root containers with dropped capabilities
- **Network Policies**: Secure inter-service communication
- **Secret Management**: Encrypted storage for sensitive data
- **RBAC**: Role-based access control for service accounts

#### High Availability
- **Rolling Updates**: Zero-downtime deployments
- **Resource Limits**: CPU and memory constraints
- **Auto-Healing**: Automatic pod restart on failures
- **Persistent Storage**: Data survival across pod restarts

### Environment Configuration

#### Production Settings
```yaml
# ConfigMap values for production
MCP_HOST: "0.0.0.0"
MCP_PORT: "9000"
LOG_LEVEL: "INFO"
MAX_FILE_SIZE: "10485760"
DB_PATH: "/app/data/file_index.sqlite3"
```

#### Resource Requirements
```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### Troubleshooting GitOps Deployment

#### Common Issues
1. **Pod Not Starting**: Check resource constraints and image pull status
2. **Service Unavailable**: Verify NodePort accessibility and security groups
3. **Database Errors**: Ensure persistent volume is properly mounted
4. **ArgoCD Sync Failures**: Check repository access and manifest syntax

#### Debug Commands
```bash
# Check pod status
kubectl get pods -n smart-file-search

# View application logs
kubectl logs -n smart-file-search -l app.kubernetes.io/name=smart-file-search

# Get pod shell access
kubectl exec -n smart-file-search -it deployment/smart-file-search -- /bin/bash

# Test service connectivity
kubectl run test-pod --image=busybox -it --rm -- \
  wget -O- http://smart-file-search-service.smart-file-search.svc.cluster.local:9000/health
```

#### ArgoCD Management
```bash
# Get ArgoCD admin password
kubectl get secret argocd-initial-admin-secret -n argocd \
  -o jsonpath="{.data.password}" | base64 -d

# Force sync application
kubectl patch app smart-file-search -n argocd \
  --type json -p='[{"op": "replace", "path": "/operation", "value": {"sync": {}}}]'
```

## 📚 Documentation

Comprehensive documentation is available in the `docs/` folder:

### 🏗️ Architecture & Design
- **[Architecture Overview](docs/architecture.md)** - System design, components, and data flow
- **[API Documentation](docs/api.md)** - Complete REST API reference and examples

### 🤖 AI Features  
- **[AI Features Guide](docs/ai-features.md)** - OpenAI integration, query enhancement, and summarization
- **[AI Integration Status](docs/AI-INTEGRATION-COMPLETE.md)** - Complete implementation details and usage

### 🚀 Deployment & Operations
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Comprehensive deployment instructions for all environments
- **[Web Deployment](docs/web-deployment.md)** - GitOps platform hosting and web-specific configurations  
- **[GitOps Ready Guide](docs/GITOPS-READY.md)** - ArgoCD integration and Kubernetes deployment

### 🔧 Development & Maintenance
- **[MCP Tools Reference](docs/mcp_tools.md)** - Model Context Protocol server tools and integration
- **[Cleanup Report](docs/CLEANUP-REPORT.md)** - Codebase organization and maintenance status

### 📋 Quick Reference
- **README.md** (this file) - Quick start guide and overview
- **LICENSE** - MIT license terms
- **requirements.txt** - Python dependencies
- **.env.example** - Environment configuration template

### 🔗 External Dependencies
- **[OpenAI API](https://platform.openai.com/docs)** - GPT-4o-mini integration
- **[FastAPI](https://fastapi.tiangolo.com/)** - Backend API framework
- **[React](https://react.dev/)** - Frontend user interface
- **[SQLite FTS5](https://www.sqlite.org/fts5.html)** - Full-text search engine
- **[Model Context Protocol](https://modelcontextprotocol.io/)** - AI tool integration standard

### 📖 Getting Help
1. **Check the relevant documentation** in the `docs/` folder first
2. **Review error logs** using the debugging commands in deployment docs
3. **Test AI features** using the integration test script: `python test_ai_integration.py`
4. **Verify configuration** by checking environment variables and API connectivity

For detailed deployment instructions, see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

## License

MIT License - see LICENSE file for details.
