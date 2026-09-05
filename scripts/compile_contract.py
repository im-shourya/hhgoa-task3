import os
import sys
import subprocess

def main():
    print("Compiling EvidenceRegistry.sol via solcjs...")
    
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    build_dir = os.path.join(project_root, "build")
    contracts_dir = os.path.join(project_root, "contracts")
    node_modules_dir = os.path.join(project_root, "node_modules")
    
    os.makedirs(build_dir, exist_ok=True)
    
    # Run solcjs to compile
    try:
        subprocess.run(
            [
                "npx", "solcjs",
                "--bin", "--abi",
                "--include-path", node_modules_dir,
                "--base-path", project_root,
                "-o", build_dir,
                os.path.join(contracts_dir, "EvidenceRegistry.sol")
            ],
            check=True,
            cwd=project_root
        )
    except subprocess.CalledProcessError as e:
        print(f"Compilation failed: {e}")
        sys.exit(1)
        
    print(f"Compilation successful! Outputs saved to {build_dir}/")

if __name__ == "__main__":
    main()
