import atexit
import os
import subprocess
import sys
import time

processes = []


def cleanup():
    print("\n[FinSense] Shutting down services...")
    for p in processes:
        p.terminate()
        try:
            p.wait(timeout=3)
        except subprocess.TimeoutExpired:
            p.kill()
    print("[FinSense] All services safely shut down.")


# Register the cleanup function to run when the script exits
atexit.register(cleanup)


def run_service(name, command, log_file):
    print(f"[FinSense] Starting {name}...")
    p = subprocess.Popen(command, shell=True, stdout=open(log_file, "w"), stderr=subprocess.STDOUT)
    processes.append(p)
    return p


def main():
    print("==================================================")
    print("   FinSense Financial Conversation Intelligence")
    print("==================================================\n")

    # Create necessary directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs(os.path.join("data", "db"), exist_ok=True)

    # Resolve python from the virtual environment
    venv_python = os.path.join("venv", "Scripts", "python.exe")
    if not os.path.exists(venv_python):
        print("Warning: Virtual environment python not found at venv/Scripts/python.exe")
        venv_python = "python"  # Fallback to system python

    print("[FinSense] Initializing environment...\n")

    # 1. Start MongoDB Locally
    # Uses a local data directory so it doesn't conflict with existing services
    run_service("MongoDB Database", 'mongod --dbpath="data/db"', "logs/mongodb.log")
    time.sleep(3)  # Give MongoDB a moment to initialize

    # 2. Start FastAPI Backend Server
    run_service(
        "FastAPI Backend",
        f'"{venv_python}" -m uvicorn backend.app:app --host 127.0.0.1 --port 8000',
        "logs/backend.log",
    )
    time.sleep(15)  # Give Backend time to load heavy AI models into memory

    # 3. Start Streamlit Frontend
    print("[FinSense] Starting Streamlit Frontend...")
    p_frontend = subprocess.Popen(
        f'"{venv_python}" -m streamlit run frontend/dashboard.py', shell=True
    )
    processes.append(p_frontend)

    print("\n--------------------------------------------------")
    print(" All FinSense Services are running seamlessly!")
    print("--------------------------------------------------")
    print(" - Backend API:         http://127.0.0.1:8000")
    print(" - Streamlit Dashboard: http://localhost:8501")
    print(" - Log files are being written to the 'logs/' folder.")
    print("--------------------------------------------------")
    print(" \nPress Ctrl+C in this terminal to safely stop all services.\n")

    # Keep script alive to catch termination signals
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[FinSense] Received termination signal.")
        sys.exit(0)


if __name__ == "__main__":
    main()
