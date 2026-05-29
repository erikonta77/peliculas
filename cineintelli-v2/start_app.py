import os
import sys
import subprocess
import time
import webbrowser
import socket

def check_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def run_command(cmd, cwd=None, shell=False):
    print(f"Executing: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    res = subprocess.run(cmd, cwd=cwd, shell=shell)
    if res.returncode != 0:
        print(f"Error executing command: {cmd}")
        sys.exit(res.returncode)

def main():
    print("====================================================")
    print("           CineIntelli V2 - Local Launcher          ")
    print("====================================================\n")

    # 1. Detect OS and set paths
    is_windows = sys.platform.startswith("win")
    python_exe = sys.executable
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(base_dir, "backend")
    frontend_dir = os.path.join(base_dir, "frontend")
    
    # Virtual Environment Path
    venv_dir = os.path.join(backend_dir, ".venv")
    if is_windows:
        venv_python = os.path.join(venv_dir, "Scripts", "python.exe")
        venv_pip = os.path.join(venv_dir, "Scripts", "pip.exe")
    else:
        venv_python = os.path.join(venv_dir, "bin", "python")
        venv_pip = os.path.join(venv_dir, "bin", "pip")

    # Verify or create Virtual Environment
    if not os.path.exists(venv_dir):
        print(f"[*] Creating Virtual Environment in {venv_dir}...")
        run_command([python_exe, "-m", "venv", venv_dir])
        print("[OK] Virtual Environment created.\n")

    # Install Python Requirements
    requirements_file = os.path.join(backend_dir, "requirements_sqlite.txt")
    print("[*] Installing Python dependencies...")
    run_command([venv_pip, "install", "-r", requirements_file])
    print("[OK] Python dependencies installed.\n")

    # 2. Check Frontend Build
    dist_dir = os.path.join(frontend_dir, "dist")
    if not os.path.exists(dist_dir) or not os.listdir(dist_dir):
        print("[*] Frontend build (dist/) not found. Building frontend...")
        # Check npm
        npm_cmd = "npm.cmd" if is_windows else "npm"
        try:
            print("[*] Running npm install...")
            subprocess.run([npm_cmd, "install"], cwd=frontend_dir, shell=True, check=True)
            print("[*] Running npm run build...")
            subprocess.run([npm_cmd, "run", "build"], cwd=frontend_dir, shell=True, check=True)
            print("[OK] Frontend built successfully.\n")
        except Exception as e:
            print(f"[ERROR] Failed to build frontend: {e}")
            print("[WARNING] The backend will run, but frontend pages might not load correctly if dist/ is missing.")

    # 3. Check if port 8000 is occupied
    port = 8000
    if check_port_in_use(port):
        print(f"[ERROR] Port {port} is already in use!")
        print("Please terminate any running instances of CineIntelli or other apps on port 8000, then try again.")
        sys.exit(1)

    # 4. Run Backend Server
    print(f"[*] Starting CineIntelli Backend Server on port {port}...")
    
    # Run uvicorn in a separate subprocess
    # We run it with cwd=backend so app module can be resolved
    uvicorn_cmd = [
        venv_python, "-m", "uvicorn", 
        "app.main_sqlite:app", 
        "--host", "127.0.0.1", 
        "--port", str(port)
    ]
    
    try:
        # We start the backend server
        backend_process = subprocess.Popen(uvicorn_cmd, cwd=backend_dir)
        
        # Wait for the backend to initialize
        print("[*] Waiting for server to initialize...")
        time.sleep(4)
        
        # Open browser
        url = f"http://localhost:{port}"
        print(f"\n[SUCCESS] CineIntelli corriendo en {url}")
        print("Opening browser automatically...")
        webbrowser.open(url)
        
        print("\nPress Ctrl+C to stop the application...\n")
        
        # Wait for backend process to terminate
        backend_process.wait()
        
    except KeyboardInterrupt:
        print("\n[*] Stopping CineIntelli application...")
        backend_process.terminate()
        try:
            backend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            backend_process.kill()
        print("[OK] CineIntelli stopped.")
    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")
        if 'backend_process' in locals():
            backend_process.kill()

if __name__ == "__main__":
    main()
