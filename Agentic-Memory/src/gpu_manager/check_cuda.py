"""
Simple script to check CUDA availability through PyTorch.
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

try:
    import torch
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"CUDA version: {torch.version.cuda}")
        print(f"Number of CUDA devices: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            print(f"Device {i}: {torch.cuda.get_device_name(i)}")
            print(f"  Memory: {torch.cuda.get_device_properties(i).total_memory / 1024 / 1024 / 1024:.2f} GB")
    else:
        print("CUDA is not available. Possible reasons:")
        print("1. No CUDA-capable GPU is installed")
        print("2. CUDA drivers are not installed or are incompatible")
        print("3. PyTorch was not installed with CUDA support")
        
except ImportError:
    print("PyTorch is not installed. Please install PyTorch with:")
    print("pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126")

if __name__ == "__main__":
    # Import and check GPU manager functionality
    try:
        from src.gpu_manager.utils import is_gpu_available
        print(f"\nGPU manager detection: {is_gpu_available()}")
    except ImportError:
        print("\nCould not import GPU manager utilities")
        
    # Check environment variables
    print("\nEnvironment settings:")
    from dotenv import load_dotenv
    load_dotenv()
    enable_gpus = os.getenv("ENABLE_GPUS", "FALSE")
    print(f"ENABLE_GPUS setting: {enable_gpus}") 