#!/usr/bin/env python3
"""
RAG-Crawl4AI Launcher
Quick access to all tools and interfaces
"""

import os
import sys
import subprocess

def print_banner():
    """Print the welcome banner."""
    print("""
🚀 RAG-Crawl4AI Launcher
========================

⚠️  PROTOTYPE DEMONSTRATION
This is a research prototype for educational purposes only.

Choose an option:
""")

def launch_streamlit():
    """Launch the Streamlit web interface."""
    print("🌐 Launching Streamlit web interface...")
    subprocess.run([sys.executable, "-m", "streamlit", "run", "streamlit_app.py"])

def check_gpu():
    """Run GPU setup checker."""
    print("🖥️  Checking GPU setup...")
    subprocess.run([sys.executable, "check_gpu.py"])

def run_pipeline():
    """Interactive pipeline runner."""
    print("\n📋 Pipeline Steps:")
    print("1. crawl    - Web crawling and markdown extraction")
    print("2. kg       - Knowledge graph building")
    print("3. vectordb - Vector database creation") 
    print("4. qa       - Interactive Q&A session")
    print("5. all      - Run all steps")
    
    step = input("\nSelect step (or 'back'): ").strip().lower()
    
    if step == 'back':
        return
    
    if step in ['crawl', 'kg', 'vectordb', 'qa', 'all']:
        force = input("Force re-run? (y/N): ").strip().lower() == 'y'
        cmd = [sys.executable, "run_pipeline.py", "--step", step]
        if force:
            cmd.append("--force")
        
        print(f"\n🚀 Running pipeline step: {step}")
        subprocess.run(cmd)
    else:
        print("❌ Invalid step. Please try again.")

def main():
    """Main launcher menu."""
    while True:
        print_banner()
        print("1. 🌐 Web Interface (Streamlit)")
        print("2. 🖥️  Check GPU Setup")
        print("3. ⚡ Run Pipeline Steps")
        print("4. 📊 View Project Status")
        print("5. ❓ Help & Documentation")
        print("6. 🚪 Exit")
        
        choice = input("\nEnter choice (1-6): ").strip()
        
        if choice == '1':
            launch_streamlit()
        
        elif choice == '2':
            check_gpu()
            input("\nPress Enter to continue...")
        
        elif choice == '3':
            run_pipeline()
            input("\nPress Enter to continue...")
        
        elif choice == '4':
            show_status()
            input("\nPress Enter to continue...")
        
        elif choice == '5':
            show_help()
            input("\nPress Enter to continue...")
        
        elif choice == '6':
            print("\n👋 Thanks for using RAG-Crawl4AI!")
            break
        
        else:
            print("\n❌ Invalid choice. Please try again.")
            input("Press Enter to continue...")

def show_status():
    """Show project status."""
    print("\n📊 Project Status:")
    print("=" * 30)
    
    # Check if output directories exist
    output_dir = "output"
    markdown_dir = os.path.join(output_dir, "markdown")
    kg_file = os.path.join(output_dir, "knowledge_graph.json")
    vector_db = os.path.join(output_dir, "vector_db")
    
    print(f"📁 Output directory: {'✅' if os.path.exists(output_dir) else '❌'}")
    print(f"📄 Markdown files: {'✅' if os.path.exists(markdown_dir) else '❌'}")
    print(f"🧠 Knowledge graph: {'✅' if os.path.exists(kg_file) else '❌'}")
    print(f"🔍 Vector database: {'✅' if os.path.exists(vector_db) else '❌'}")
    
    # Count files if they exist
    if os.path.exists(markdown_dir):
        md_files = len([f for f in os.listdir(markdown_dir) if f.endswith('.md')])
        print(f"   📋 Markdown files: {md_files}")
    
    if os.path.exists(kg_file):
        try:
            import json
            with open(kg_file) as f:
                kg_data = json.load(f)
            print(f"   🎯 Entities: {len(kg_data.get('entities', []))}")
            print(f"   🔗 Relationships: {len(kg_data.get('relationships', []))}")
        except:
            print("   ⚠️  Knowledge graph file exists but couldn't be read")

def show_help():
    """Show help and documentation."""
    print("""
📚 RAG-Crawl4AI Help
===================

🎯 Quick Start:
1. Run: python launch.py
2. Choose option 1 for web interface
3. Or run pipeline steps manually

⚡ Pipeline Steps:
• crawl    - Downloads and converts web pages to markdown
• kg       - Extracts knowledge graph using LLM
• vectordb - Creates semantic search index  
• qa       - Interactive question answering

🌐 Web Interface:
• Beautiful dashboard for all operations
• Document browser with markdown preview
• Knowledge graph visualization
• Interactive Q&A system

🖥️  GPU Acceleration:
• Automatic GPU detection
• 3-10x faster embedding generation
• Run 'python check_gpu.py' to verify setup

📋 Requirements:
• Python 3.8+
• Gemini API key (set in .env file)
• Optional: CUDA-compatible GPU

🔗 More Info:
• README.md - Detailed documentation
• streamlit_app.py - Web interface source
• src/config.py - Configuration settings

⚠️  Remember: This is a prototype for demonstration purposes!
""")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Thanks for using RAG-Crawl4AI!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Please check your setup and try again.") 