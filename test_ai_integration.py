#!/usr/bin/env python3
"""
Test script for AI integration in Smart File Search.
Tests OpenAI connectivity and AI enhancement features.
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Add search_agent to path
sys.path.insert(0, str(Path(__file__).parent))

from search_agent.config import SearchConfig
from search_agent.ai_enhancer import AISearchEnhancer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def test_ai_integration():
    """Test AI integration functionality."""
    logger.info("🧪 Testing AI Integration for Smart File Search")
    
    try:
        # Initialize configuration
        config = SearchConfig()
        logger.info(f"✅ Configuration loaded")
        logger.info(f"   - OpenAI API Key: {'✅ Configured' if config.openai_api_key else '❌ Missing'}")
        logger.info(f"   - Query Rewrite: {'✅ Enabled' if config.enable_query_rewrite else '❌ Disabled'}")
        logger.info(f"   - Summarization: {'✅ Enabled' if config.enable_summarization else '❌ Disabled'}")
        
        # Initialize AI enhancer
        ai_enhancer = AISearchEnhancer(config)
        logger.info(f"✅ AI Enhancer initialized")
        logger.info(f"   - AI Available: {'✅ Yes' if ai_enhancer.is_available() else '❌ No'}")
        
        if not ai_enhancer.is_available():
            logger.error("❌ AI features not available. Check OpenAI API key configuration.")
            return False
        
        # Test query enhancement
        logger.info("\n🔍 Testing Query Enhancement...")
        test_queries = [
            "budget spreadsheets",
            "meeting notes from last week", 
            "project proposal documents",
            "financial reports Q4"
        ]
        
        for query in test_queries:
            enhanced = ai_enhancer.enhance_query(query)
            logger.info(f"   Original: '{query}'")
            logger.info(f"   Enhanced: '{enhanced}'")
            logger.info("")
        
        # Test summarization
        logger.info("📄 Testing Result Summarization...")
        sample_results = [
            {
                'file_path': 'C:\\Documents\\Budget_2024.xlsx',
                'snippet': 'Annual budget planning document with quarterly breakdowns and expense categories.',
                'score': 0.95
            },
            {
                'file_path': 'C:\\Documents\\Meeting_Notes_Jan.docx', 
                'snippet': 'Team meeting notes discussing budget allocation and project priorities.',
                'score': 0.87
            },
            {
                'file_path': 'C:\\Documents\\Financial_Report_Q4.pdf',
                'snippet': 'Quarterly financial performance review with year-over-year comparisons.',
                'score': 0.82
            }
        ]
        
        summary = ai_enhancer.summarize_results("budget documents", sample_results)
        logger.info(f"Summary:\n{summary}")
        
        # Test related queries
        logger.info("\n🔗 Testing Related Query Suggestions...")
        related_queries = ai_enhancer.suggest_related_queries("budget documents", sample_results)
        for i, query in enumerate(related_queries, 1):
            logger.info(f"   {i}. {query}")
        
        logger.info("\n✅ All AI integration tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ AI integration test failed: {e}")
        return False

def test_config():
    """Test configuration loading."""
    logger.info("⚙️  Testing Configuration...")
    
    config = SearchConfig()
    
    # Check environment variables
    env_vars = [
        'OPENAI_API_KEY',
        'ENABLE_AI_FEATURES', 
        'ENABLE_QUERY_REWRITE',
        'ENABLE_SUMMARIZATION'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        logger.info(f"   {var}: {'✅ Set' if value else '❌ Not set'}")
    
    return True

async def main():
    """Main test function."""
    print("=" * 60)
    print("🤖 Smart File Search - AI Integration Test")
    print("=" * 60)
    
    # Test configuration
    test_config()
    print()
    
    # Test AI integration
    await test_ai_integration()
    
    print("\n" + "=" * 60)
    print("Test complete! Check the logs above for results.")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
