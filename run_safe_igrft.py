#!/usr/bin/env python3
"""
MEMORY-SAFE IGRFT Runner

This script runs IGRFT with safety checks for memory-constrained systems.
Use this instead of the main module if you're experiencing crashes.
"""

import subprocess
import sys
from pathlib import Path


def check_system_resources():
    """Check if system has enough resources for training"""
    print("🔍 Checking system resources...")
    
    # Check memory
    try:
        with open('/proc/meminfo', 'r') as f:
            meminfo = f.read()
            for line in meminfo.split('\n'):
                if 'MemAvailable:' in line:
                    # Extract available memory in KB
                    mem_kb = int(line.split()[1])
                    mem_gb = mem_kb / (1024 * 1024)
                    print(f"   Available RAM: {mem_gb:.1f} GB")
                    
                    if mem_gb < 8:
                        print("\n⚠️  WARNING: Less than 8GB RAM available")
                        print("   Recommended actions:")
                        print("   1. Close Chrome/browsers: pkill chrome")
                        print("   2. Close VS Code if not editing: pkill code")
                        print("   3. Use smaller model (TinyLlama)")
                        response = input("\n   Continue anyway? (y/N): ")
                        if response.lower() != 'y':
                            print("❌ Aborted for safety")
                            return False
                    else:
                        print("   ✅ Sufficient RAM available")
                    break
    except Exception as e:
        print(f"   ⚠️  Could not check memory: {e}")
    
    # Check disk space
    try:
        result = subprocess.run(
            ['df', '-h', '/tmp'],
            capture_output=True,
            text=True
        )
        lines = result.stdout.strip().split('\n')
        if len(lines) > 1:
            parts = lines[1].split()
            use_pct = parts[4].rstrip('%')
            print(f"   /tmp disk usage: {use_pct}%")
            
            if int(use_pct) > 80:
                print("   ⚠️  /tmp is >80% full - may cause issues")
                print("   Clear space with: sudo rm -rf /tmp/tmp* /tmp/pytorch*")
    except Exception as e:
        print(f"   ⚠️  Could not check disk: {e}")
    
    return True


def kill_memory_hogs():
    """Offer to kill memory-intensive processes"""
    print("\n🧹 Memory optimization...")
    
    processes_to_check = [
        ('chrome', 'Chrome browser'),
        ('chromium', 'Chromium browser'),
        ('firefox', 'Firefox browser'),
    ]
    
    for proc_name, description in processes_to_check:
        try:
            result = subprocess.run(
                ['pgrep', proc_name],
                capture_output=True,
                text=True
            )
            if result.stdout.strip():
                response = input(f"   Kill {description}? (y/N): ")
                if response.lower() == 'y':
                    subprocess.run(['pkill', '-9', proc_name])
                    print(f"   ✅ Killed {proc_name}")
        except Exception:
            pass


def run_safe_igrft(dataset_path: str, cycles: int = 3, model: str = None):
    """Run IGRFT with memory safety"""
    
    if not check_system_resources():
        return
    
    kill_memory_hogs()
    
    # Note: Model selection is currently hardcoded in IGRFT module
    # To use TinyLlama, you need to modify src/peachtree/inference_recursive_learning.py
    # Change line 158: model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    
    print(f"\n🚀 Starting IGRFT with {cycles} cycles...")
    print(f"   Dataset: {dataset_path}")
    print(f"   ⚠️  Note: Model is hardcoded in IGRFT (currently Mistral-7B)")
    print(f"   For low-memory systems, edit src/peachtree/inference_recursive_learning.py")
    print(f"   Change line 158 to: model_name = 'TinyLlama/TinyLlama-1.1B-Chat-v1.0'")
    
    # Run with memory monitoring (no --model arg, it's not supported)
    cmd = [
        sys.executable, '-m', 'peachtree.inference_recursive_learning',
        '--dataset', dataset_path,
        '--cycles', str(cycles),
        '--verbose'
    ]
    
    print(f"\n   Command: {' '.join(cmd)}\n")
    
    try:
        subprocess.run(cmd, check=True)
        print("\n✅ IGRFT completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ IGRFT failed with exit code {e.returncode}")
        print("\n🔍 Troubleshooting:")
        print("   1. Check memory: free -h")
        print("   2. Check logs: tail -50 /tmp/peachtree.log")
        print("   3. See: IGRFT-MEMORY-OPTIMIZATION.md")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(130)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Memory-safe IGRFT runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run IGRFT (uses hardcoded model - currently Mistral-7B)
  python run_safe_igrft.py data/hancock/unified-expanded.jsonl
  
  # Run with more cycles
  python run_safe_igrft.py data/hancock/unified-expanded.jsonl --cycles 5
  
  # For low-memory systems, edit src/peachtree/inference_recursive_learning.py
  # Change line 158 to use TinyLlama instead of Mistral-7B
        """
    )
    
    parser.add_argument(
        'dataset',
        help='Path to JSONL dataset'
    )
    parser.add_argument(
        '--cycles',
        type=int,
        default=3,
        help='Number of IGRFT cycles (default: 3)'
    )
    # NOTE: --model removed because IGRFT doesn't support it
    # Model is hardcoded in src/peachtree/inference_recursive_learning.py
    
    args = parser.parse_args()
    
    if not Path(args.dataset).exists():
        print(f"❌ Dataset not found: {args.dataset}")
        sys.exit(1)
    
    run_safe_igrft(args.dataset, args.cycles)
