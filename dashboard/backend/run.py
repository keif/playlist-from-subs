#!/usr/bin/env python3
"""
Convenience script to start the dashboard backend server.

This script provides a simple way to start the backend with proper
environment setup and logging configuration.
"""

import os
import sys
from pathlib import Path

def setup_environment():
    """Set up the Python path and environment for the backend."""
    # Add project root to Python path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    # Change to project root directory (important for CLI integration)
    os.chdir(project_root)
    
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🐍 Python path includes: {project_root}")

def main():
    """Start the backend server."""
    print("🚀 Starting YouTube Playlist Dashboard Backend...")
    
    setup_environment()
    
    # Import and run the Flask app
    from app import app, logger
    
    logger.info("Starting Flask development server")
    
    try:
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=True,
            use_reloader=True
        )
    except KeyboardInterrupt:
        print("\n👋 Backend server stopped")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()