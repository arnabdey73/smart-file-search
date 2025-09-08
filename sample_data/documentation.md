# Smart File Search Documentation

Welcome to the Smart File Search system! This is a comprehensive document search platform that combines full-text search capabilities with AI-powered enhancements.

## Features

- **Multi-format support**: Search across PDF, DOCX, PPTX, XLSX, text files, and more
- **Intelligent search**: Natural language queries with AI-powered query rewriting
- **Fast indexing**: Incremental indexing with SQLite FTS5
- **Semantic search**: Optional semantic similarity ranking
- **Web interface**: Modern React-based user interface
- **Security**: Built-in content redaction and access controls

## Getting Started

1. **Installation**: Follow the setup instructions in the main README
2. **Configuration**: Set your OpenAI API key and allowed directories
3. **Indexing**: Use the CLI or web interface to index your documents
4. **Searching**: Start searching with natural language queries

## Search Tips

### Basic Search
- Use natural language: "Python programming tutorials"
- Add quotes for exact phrases: "machine learning algorithms"
- Combine terms: API documentation AND REST

### Filters
- File types: Add extensions like .py, .md, .pdf
- Date ranges: Specify years like 2023, 2024
- Directories: Limit to specific folders

### Advanced Features
- **AI Summarization**: Get AI-generated summaries of search results
- **Query Rewriting**: Automatic query optimization for better results
- **Semantic Ranking**: Results ranked by meaning, not just keywords

## Technical Details

The system uses:
- SQLite FTS5 for full-text search
- OpenAI GPT-4.1 mini for AI features
- React + TypeScript frontend
- FastAPI backend
- Docker for deployment

## Support

For questions and issues, please refer to the main documentation or contact support.
