"""
Run script for LogEverything Dashboard with SCSS compilation
"""

import os
import sys
import time
import threading
import subprocess
from pathlib import Path

# Add the current directory to the path
sys.path.insert(0, '.')

def compile_scss():
    """Compile SCSS files to CSS"""
    try:
        from dashboard.compile_scss import SCSSCompiler
        
        print("Compiling SCSS to CSS...")
        base_dir = Path(__file__).parent / "dashboard"
        scss_dir = base_dir / "static" / "scss"
        css_dir = base_dir / "static" / "css"
        
        css_dir.mkdir(parents=True, exist_ok=True)
        
        compiler = SCSSCompiler(scss_dir, css_dir)
        compiler.compile_all()
        print("SCSS compilation complete")
        
        return True
    except Exception as e:
        print(f"Warning: SCSS compilation failed: {e}")
        print("Using existing CSS files if available")
        return False

def run_scss_watcher():
    """Run SCSS watcher in a separate thread"""
    from dashboard.compile_scss import SCSSCompiler
    
    base_dir = Path(__file__).parent / "dashboard"
    scss_dir = base_dir / "static" / "scss"
    css_dir = base_dir / "static" / "css"
    
    compiler = SCSSCompiler(scss_dir, css_dir)
    compiler.watch()

def run_dashboard(port=3001, host="0.0.0.0", reload=True):
    """Run the dashboard server"""
    import uvicorn
    
    print("Starting LogEverything Dashboard")
    print(f"URL: http://localhost:{port}")
    print()
    
    uvicorn.run(
        "dashboard.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description="Run LogEverything Dashboard")
    parser.add_argument("--port", type=int, default=3001, help="Port to run on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to run on")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")
    parser.add_argument("--no-scss-watch", action="store_true", help="Disable SCSS watcher")
    parser.add_argument("--data-dir", type=str, help="Data directory for monitoring data")
    parser.add_argument("--api-url", type=str, help="API URL for remote connection")
    
    args = parser.parse_args()
    
    # Set environment variables
    if args.data_dir:
        os.environ["DASHBOARD_MONITORING_DATA_DIR"] = args.data_dir
    else:
        os.environ["DASHBOARD_MONITORING_DATA_DIR"] = "../sample_monitoring_data"
    
    if args.api_url:
        os.environ["DASHBOARD_API_URL"] = args.api_url
    
    os.environ["DASHBOARD_DEBUG"] = "true"
    os.environ["DASHBOARD_DASHBOARD_PORT"] = str(args.port)
    
    # Compile SCSS
    success = compile_scss()
    
    # Start SCSS watcher in a background thread
    if not args.no_scss_watch:
        print("Starting SCSS watcher...")
        watcher_thread = threading.Thread(target=run_scss_watcher)
        watcher_thread.daemon = True
        watcher_thread.start()
    
    # Run the dashboard
    run_dashboard(
        port=args.port,
        host=args.host,
        reload=not args.no_reload
    )
