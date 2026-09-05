import os
import sys
import subprocess

def main():
    print("Compiling EvidenceRegistry.sol via solcjs...")
    
    build_dir = os.path.join(os.path.dirname(__file__), "..", "build")
    
    os.makedirs(build_dir, exist_ok=True)
    
    # Run solcjs to compile
    try:
        subprocess.run(
            [
                "npx", "solcjs",
                "--bin", "--abi",
                "--include-path", "node_modules/",
                "--base-path", ".",
                "-o", "build",
                os.path.join("contracts", "EvidenceRegistry.sol")
            ],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Compilation failed: {e}")
        sys.exit(1)
        
    print(f"Compilation successful! Outputs saved to {build_dir}/")

if __name__ == "__main__":
    main()
