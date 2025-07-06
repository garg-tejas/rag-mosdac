#!/usr/bin/env python3
"""
GPU Setup Checker for RAG-Crawl4AI
Run this script to verify your GPU setup and get installation instructions.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from modules.gpu_utils import check_gpu_setup, optimize_gpu_settings
    
    if __name__ == "__main__":
        print("🚀 RAG-Crawl4AI GPU Setup Checker")
        print("=" * 50)
        
        success = check_gpu_setup()
        
        if success:
            print("\n🎯 Performance Tips:")
            print("- Your GPU will significantly speed up embedding generation")
            print("- Larger batch sizes will be used automatically on GPU")
            print("- Vector database creation will be 3-10x faster")
            
            print("\n⚡ Run the pipeline to see GPU acceleration in action:")
            print("python run_pipeline.py --step vectordb")
        else:
            print("\n⚠️  GPU acceleration is not available")
            print("The pipeline will still work with CPU, but will be slower")
            
        optimize_gpu_settings()
        
except ImportError as e:
    print(f"❌ Error importing GPU utilities: {e}")
    print("Make sure you're in the project directory and dependencies are installed")
    sys.exit(1) 