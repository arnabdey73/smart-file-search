"""Configuration for Windows network folder search - Web Deployment Optimized."""
import os
from pathlib import Path
from typing import List, Dict, Any
import yaml

class SearchConfig:
    """Configuration for Windows network folder search - optimized for web deployment."""
    
    def __init__(self):
        # Web deployment mode
        self.deployment_mode = os.getenv("DEPLOYMENT_MODE", "web")  # "web" or "local"
        self.web_access_enabled = True
        
        # Windows network folder specific settings (accessed via web UI)
        self.allowed_network_paths = []  # Will be populated by user input via web
        
        # Simple search settings - prioritize speed for web users
        self.max_file_size_mb = 50  # Skip very large files for web performance
        self.max_results = 100      # Keep results manageable for web display
        self.chunk_size = 1000      # Smaller chunks for faster web response
        self.enable_semantic_search = False  # Disable by default for speed
        
        # Web UI timeout settings
        self.web_request_timeout = 30  # Seconds for web requests
        self.indexing_timeout = 300    # 5 minutes max for web indexing
        
        # Windows file types commonly found in network folders
        self.supported_extensions = {
            '.txt', '.md', '.docx', '.pdf', '.xlsx', '.pptx',
            '.csv', '.json', '.xml', '.html', '.py', '.js',
            '.sql', '.log', '.ini', '.cfg', '.yaml', '.yml'
        }
        
        # GPT settings for query enhancement and summarization (optional via web UI)
        self.gpt_model = "gpt-4o-mini"  # Fast and cost-effective for web users
        self.max_tokens = 1000
        self.enable_query_rewrite = True
        self.enable_summarization = True
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "your_openai_api_key_here")
        
        # Token conservation settings
        self.daily_token_limit = int(os.getenv("DAILY_TOKEN_LIMIT", "5000"))
        self.max_tokens_per_request = int(os.getenv("MAX_TOKENS_PER_REQUEST", "100"))
        self.require_explicit_ai_opt_in = os.getenv("REQUIRE_EXPLICIT_AI_OPT_IN", "true").lower() == "true"
        self.auto_disable_on_limit = os.getenv("AUTO_DISABLE_ON_LIMIT", "true").lower() == "true"
        self.enable_token_warnings = os.getenv("ENABLE_TOKEN_WARNINGS", "true").lower() == "true"
        
        # Windows network specific - optimized for containerized deployment
        self.index_hidden_files = False
        self.follow_symlinks = False
        self.timeout_seconds = 30
        
        # Database settings - persistent for web deployment
        self.database_path = os.getenv("DB_PATH", "/data/file_index.sqlite3")  # Container path
        
        # Web deployment security
        self.max_concurrent_users = int(os.getenv("MAX_CONCURRENT_USERS", "10"))
        self.rate_limit_per_minute = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))
        
    def is_network_path_allowed(self, path: str) -> bool:
        """Check if network path is in allowlist (for web security)."""
        if not self.allowed_network_paths:
            return True  # Allow any path if none configured
        path = os.path.normpath(path)
        return any(path.startswith(allowed) for allowed in self.allowed_network_paths)
    
    def add_network_path(self, path: str):
        """Add a new network path to the allowed list (via web UI)."""
        normalized_path = os.path.normpath(path)
        if normalized_path not in self.allowed_network_paths:
            self.allowed_network_paths.append(normalized_path)
    
    def load_from_file(self, config_path: str = "config/settings.yaml"):
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
                
            # Update network paths from config
            if 'network_paths' in config_data:
                self.allowed_network_paths = config_data['network_paths']
                
            if 'search' in config_data:
                search_config = config_data['search']
                self.max_results = search_config.get('max_results', self.max_results)
                self.chunk_size = search_config.get('chunk_size', self.chunk_size)
                self.enable_semantic_search = search_config.get('enable_semantic_search', False)
                
            if 'gpt' in config_data:
                gpt_config = config_data['gpt']
                self.gpt_model = gpt_config.get('model', self.gpt_model)
                self.max_tokens = gpt_config.get('max_tokens', self.max_tokens)
                
        except FileNotFoundError:
            print(f"Config file {config_path} not found, using defaults")
        except Exception as e:
            print(f"Error loading config: {e}, using defaults")

# Global config instance
config = SearchConfig()

# Backwards compatibility functions
def get_config() -> Dict[str, Any]:
    """Get configuration settings for backwards compatibility."""
    return {
        "server_name": os.getenv("MCP_SERVER_NAME", "smart-file-search"),
        "host": os.getenv("MCP_HOST", "0.0.0.0"),
        "port": int(os.getenv("MCP_PORT", "9000")),
        "debug": os.getenv("DEBUG", "false").lower() == "true",
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "database_path": config.database_path,
        "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
        "max_file_size": config.max_file_size_mb * 1024 * 1024,
        "allowed_roots": config.allowed_network_paths,
        "supported_extensions": list(config.supported_extensions)
    }

def get_database_path() -> str:
    """Get the database path, creating directory if needed."""
    db_path = config.database_path
    
    # Create directory if it doesn't exist
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    return db_path
