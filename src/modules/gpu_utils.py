# src/modules/gpu_utils.py

import os
import sys
import logging
import subprocess
import platform

def get_device():
    """Detect and return the best available device for PyTorch operations."""
    try:
        import torch
        
        if torch.cuda.is_available():
            device = torch.device("cuda")
            logging.info(f"GPU detected: {torch.cuda.get_device_name(0)}")
            logging.info(f"CUDA version: {torch.version.cuda}")
            logging.info(f"GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
            return device
        elif torch.backends.mps.is_available():  # For Apple Silicon Macs
            device = torch.device("mps")
            logging.info("Apple Silicon MPS device detected")
            return device
        else:
            device = torch.device("cpu")
            logging.info("No GPU detected, using CPU")
            return device
    except ImportError:
        logging.warning("PyTorch not available, using CPU")
        # Return a simple string identifier when torch is not available
        return "cpu"

def check_gpu_setup():
    """Comprehensive GPU setup checker and installation guide."""
    print("🔍 GPU Setup Checker")
    print("=" * 50)
    
    # Check CUDA availability
    try:
        import torch
        print(f"✅ PyTorch version: {torch.__version__}")
        
        if torch.cuda.is_available():
            print(f"✅ CUDA available: {torch.version.cuda}")
            print(f"✅ GPU count: {torch.cuda.device_count()}")
            
            for i in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(i)
                print(f"   GPU {i}: {props.name}")
                print(f"   Memory: {props.total_memory / 1024**3:.1f} GB")
                print(f"   Compute capability: {props.major}.{props.minor}")
        else:
            print("❌ CUDA not available")
            print_cuda_installation_guide()
            
        # Check MPS (Apple Silicon)
        if torch.backends.mps.is_available():
            print("✅ Apple Silicon MPS available")
        elif platform.system() == "Darwin" and platform.machine() == "arm64":
            print("❌ MPS not available (check PyTorch version)")
            
    except ImportError:
        print("❌ PyTorch not installed")
        print_pytorch_installation_guide()
        return False
    
    # Test embedding model with GPU
    try:
        from sentence_transformers import SentenceTransformer
        print("\n🧪 Testing GPU with sentence-transformers...")
        
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = SentenceTransformer('all-MiniLM-L6-v2', device=device)
        
        # Quick test
        test_texts = ["This is a test sentence.", "GPU acceleration test."]
        embeddings = model.encode(test_texts, convert_to_tensor=True)
        
        print(f"✅ Successfully created embeddings on {device}")
        print(f"   Embedding shape: {embeddings.shape}")
        print(f"   Device: {embeddings.device}")
        
        if device.type == "cuda":
            print(f"   GPU memory used: {torch.cuda.memory_allocated() / 1024**2:.1f} MB")
            torch.cuda.empty_cache()
            
    except Exception as e:
        print(f"❌ GPU test failed: {e}")
        return False
    
    print("\n🎉 GPU setup verification complete!")
    return True

def print_pytorch_installation_guide():
    """Print PyTorch installation instructions."""
    print("\n📦 PyTorch Installation Guide:")
    print("-" * 30)
    
    system = platform.system().lower()
    
    if system == "windows":
        print("For Windows with CUDA:")
        print("pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121")
        print("\nFor Windows CPU-only:")
        print("pip install torch torchvision torchaudio")
        
    elif system == "linux":
        print("For Linux with CUDA:")
        print("pip install torch torchvision torchaudio")
        print("\nFor Linux CPU-only:")
        print("pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu")
        
    elif system == "darwin":
        print("For macOS (CPU and Apple Silicon MPS):")
        print("pip install torch torchvision torchaudio")
    
    print("\n🔗 Visit https://pytorch.org/get-started/locally/ for detailed instructions")

def print_cuda_installation_guide():
    """Print CUDA installation guide."""
    print("\n🎯 CUDA Setup Guide:")
    print("-" * 20)
    print("1. Check your GPU: nvidia-smi")
    print("2. Install CUDA Toolkit from: https://developer.nvidia.com/cuda-downloads")
    print("3. Install PyTorch with CUDA support (see above)")
    print("4. Restart your terminal/IDE")

def optimize_gpu_settings():
    """Apply optimal GPU settings for the current setup."""
    try:
        import torch
        
        if torch.cuda.is_available():
            # Enable optimizations
            torch.backends.cudnn.benchmark = True
            torch.backends.cudnn.deterministic = False
            
            # Set memory allocation strategy
            os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:128'
            
            print("✅ GPU optimizations applied:")
            print("   - CuDNN benchmark enabled")
            print("   - Memory allocation optimized")
            
            return True
    except ImportError:
        pass
    
    return False

def get_recommended_batch_size():
    """Get recommended batch size based on available GPU memory."""
    try:
        import torch
        
        if not torch.cuda.is_available():
            return 8  # Conservative CPU batch size
        
        gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
        
        if gpu_memory_gb >= 24:  # RTX 4090, A100, etc.
            return 64
        elif gpu_memory_gb >= 12:  # RTX 4070 Ti, RTX 3080, etc.
            return 32
        elif gpu_memory_gb >= 8:   # RTX 3070, RTX 4060, etc.
            return 16
        else:  # Lower-end GPUs
            return 8
            
    except ImportError:
        return 8

if __name__ == "__main__":
    check_gpu_setup()
    optimize_gpu_settings() 