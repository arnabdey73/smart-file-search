# Smart File Search System

**Windows Network Folder Edition** - A production-ready intelligent document search system optimized for Windows network folders with simple search functionality prioritized.

## 📋 Table of Contents

- [Overview](#overview)
- [🚀 GitOps Deployment (Recommended)](#-gitops-deployment-recommended)
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

## 🚀 GitOps Deployment (Recommended)

### 🌐 Production-Ready Web Application

The **preferred deployment method** is through GitOps platform hosting. This provides a fully-managed, production-ready solution accessible via web browser.

#### ✅ Why GitOps Deployment?

- **🌍 Zero Installation**: Access via any web browser - no local setup required
- **🔄 Auto-Updates**: Continuous deployment with GitOps synchronization  
- **📈 Production Scale**: Kubernetes-based infrastructure with monitoring
- **🔒 Enterprise Security**: Built-in security hardening and access controls
- **💾 Persistent Data**: Reliable database storage with backup capabilities
- **🌐 Network Access**: Direct connectivity to Windows network shares

#### 🚀 Quick GitOps Setup

1. **Deploy GitOps Platform** (if not already available):
   ```bash
   git clone https://github.com/arnabdey73/single-node-gitops
   cd single-node-gitops
   ./install.sh
   ```

2. **Deploy Smart File Search**:
   ```bash
   # Clone this repository
   git clone https://github.com/arnabdey73/smart-file-search
   cd smart-file-search
   
   # Apply Kubernetes manifests
   kubectl apply -k k8s/
   ```

3. **Configure Secrets**:
   ```bash
   # Set your OpenAI API key
   kubectl create secret generic smart-file-search-secrets \
     --from-literal=OPENAI_API_KEY=your-api-key-here \
     -n smart-file-search
   ```

4. **Access Application**:
   - **URL**: `https://your-gitops-domain/smart-file-search`
   - **Login**: Use your GitOps platform credentials
   - **Ready**: Start indexing network folders immediately!

#### 🏗 GitOps Architecture

```
GitOps Platform (Kubernetes Cluster)
├── 🌐 Smart File Search Web UI (React)
│   ├── Public ingress with TLS termination
│   ├── Responsive design for all devices  
│   └── Real-time search interface
├── ⚙️ Search API Backend (FastAPI)
│   ├── Windows network folder connectivity
│   ├── SQLite FTS5 search engine
│   └── OpenAI GPT-4o-mini integration
├── 💾 Persistent Storage
│   ├── Database volume for search index
│   └── Configuration and logs storage
└── 🔗 Network Integration
    ├── Windows share mounting (CIFS/SMB)
    ├── Authentication passthrough
    └── Real-time folder synchronization
```

#### 📊 GitOps Features

- **🔄 ArgoCD Integration**: Automated deployment and sync
- **📈 Monitoring Ready**: Prometheus metrics + Grafana dashboards
- **🛡️ Security Hardened**: Pod security policies and network controls
- **🌐 Web-First Design**: Optimized for browser-based access
- **📱 Mobile Responsive**: Works on phones, tablets, and desktops
- **⚡ High Performance**: Container-optimized with resource limits

#### 🎯 For Enterprise Users

**GitOps deployment is recommended for**:
- **Production environments** requiring reliability and monitoring
- **Team collaboration** where multiple users need access
- **Enterprise networks** with Windows file server integration  
- **Compliance requirements** needing audit trails and security
- **Scalable usage** with growing document repositories

---

## 🚀 Quick Start

### 🌐 Production Access (GitOps Hosted)

**Access the application directly via your GitOps platform**:

🌍 **Web URL**: `https://your-gitops-domain/smart-file-search`

✅ **Ready to Use**: No installation, no configuration - just open and search!

### 📖 Using the Web Interface

1. **🌐 Open Browser**: Navigate to the GitOps-hosted application
2. **📁 Add Network Folders**: Enter UNC paths like `\\fileserver\documents`
3. **✅ Validate Access**: System verifies connectivity and shows file counts
4. **⚡ Quick Index**: Start indexing with recommended quick scan mode
5. **🔍 Search**: Use natural language queries to find documents instantly
6. **🤖 Enable AI** (Optional): Toggle AI enhancement for better results

### 🛠️ Local Development (For Developers Only)

If you're developing or customizing the application:

```bash
# Start local development environment
scripts/start_all.bat
```

**Local URLs**:
- API Backend: <http://localhost:8000>
- Web Frontend: <http://localhost:3000>

> **Note**: Production users should use the GitOps-hosted version for best performance and reliability.

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
