import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

# ----- Utility Functions ----- #

def is_windows() -> bool:
    """Check if the current platform is Windows."""
    return sys.platform.startswith("win")

def is_macos() -> bool:
    """Check if the current platform is macOS."""
    return sys.platform == "darwin"

def get_venv_python() -> str:
    """Return the path to the Python executable inside the virtual environment."""
    if is_windows():
        return os.path.join("chirp_env", "Scripts", "python")
    else:
        return os.path.join("chirp_env", "bin", "python3")

def run_in_venv(command: str | list) -> None:
    """
    Run a Python command inside the virtual environment.
    
    Args:
        command: A string (to run via '-c') or a list of command arguments.
    """
    venv_python = get_venv_python()
    if isinstance(command, list):
        full_command = [venv_python] + command
    else:
        full_command = [venv_python, "-c", command]
    try:
        subprocess.run(full_command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running command in virtual environment: {e}")
        sys.exit(1)

def copy_file(src: str, dest: str) -> None:
    """
    Copy a file from src to dest.
    
    If the destination exists, prompt the user before overwriting.
    """
    if os.path.exists(dest):
        prompt = f"[?] {dest} already exists. Overwrite? (y/n): "
        if input(prompt).strip().lower() != "y":
            print(f"[!] Skipping {dest}")
            return
    shutil.copy(src, dest)
    print(f"[+] Copied {src} to {dest}")

# ----- Virtual Environment & Dependency Setup ----- #

def create_virtualenv(force: bool = False) -> None:
    """Create a virtual environment in the 'chirp_env' folder."""
    venv_path = Path("chirp_env")
    if venv_path.exists() and not force:
        print("[!] Virtual environment already exists.")
        return

    if force and venv_path.exists():
        print("[!] Removing existing virtual environment...")
        shutil.rmtree(venv_path)
    
    print("[*] Creating virtual environment...")
    subprocess.run([sys.executable, "-m", "venv", "chirp_env"], check=True)
    print("[+] Virtual environment created.")

def install_python_dependencies(requirements_file: str) -> None:
    """Install Python dependencies from the specified requirements file."""
    python_executable = get_venv_python()
    print(f"[*] Installing dependencies from {requirements_file}...")
    try:
        subprocess.check_call([python_executable, "-m", "pip", "install", "-r", requirements_file])
        print(f"[+] Installed dependencies from {requirements_file}.")
    except subprocess.CalledProcessError as e:
        print(f"[-] Error installing dependencies: {e}")
        sys.exit(1)

def install_os_dependencies() -> None:
    """Install OS-level dependencies based on the current platform."""
    if is_macos():
        try:
            print("[*] Installing macOS dependencies via Homebrew...")
            subprocess.check_call(["brew", "install", "xclip", "ffmpeg", "portaudio"])
            print("[+] macOS dependencies installed.")
        except subprocess.CalledProcessError as e:
            print(f"[-] Error installing dependencies with Homebrew: {e}")
            sys.exit(1)
    elif not is_windows():
        # Assume Linux – try apt-get and pacman
        package_managers = {
            "apt-get": ["sudo", "apt-get", "install", "-y", "xclip", "ffmpeg", "portaudio19-dev"],
            "pacman": ["sudo", "pacman", "-Sy", "xclip", "ffmpeg", "portaudio"]
        }
        installed = False
        for manager, cmd in package_managers.items():
            try:
                print(f"[*] Installing Linux dependencies via {manager}...")
                subprocess.check_call(cmd)
                print(f"[+] Dependencies installed using {manager}.")
                installed = True
                break
            except subprocess.CalledProcessError:
                print(f"[-] Failed to install dependencies with {manager}.")
        if not installed:
            print("[-] Could not install OS-level dependencies automatically. Please install them manually.")
            sys.exit(1)
    else:
        print("[*] Windows detected – OS-level dependency installation is skipped (please install manually if needed).")

def create_run_file() -> None:
    """Create a run file appropriate for the current platform."""
    if is_windows():
        bat_file = "Chirp.bat"
        with open(bat_file, "w", encoding="utf-8") as f:
            f.write("@echo off\n")
            f.write('cd /d "%~dp0"\n')
            f.write("call chirp_env\\Scripts\\activate.bat\n")
            f.write("python main.py\n")
            f.write("pause\n")
        print(f"[+] Created Windows run file: {bat_file}")
    else:
        sh_file = "Chirp.sh"
        with open(sh_file, "w", encoding="utf-8") as f:
            f.write("#!/bin/bash\n")
            f.write("source chirp_env/bin/activate\n")
            f.write("python3 main.py\n")
        os.chmod(sh_file, 0o755)
        print(f"[+] Created run file for Linux/macOS: {sh_file}")

def add_to_startup(run_file: str) -> None:
    """Add the run file to startup (currently implemented for Windows only)."""
    if is_windows():
        confirm = input("[?] Add Chirp to startup? (y/n): ").strip().lower()
        if confirm != "y":
            print("[!] Skipping startup configuration.")
            return

        startup_dir = os.path.join(
            os.path.expanduser("~"),
            "AppData",
            "Roaming",
            "Microsoft",
            "Windows",
            "Start Menu",
            "Programs",
            "Startup"
        )
        os.makedirs(startup_dir, exist_ok=True)
        startup_file = os.path.join(startup_dir, "Chirp.bat")
        with open(startup_file, "w", encoding="utf-8") as f:
            f.write("@echo off\n")
            f.write(f'cd /d "{os.path.dirname(os.path.abspath(__file__))}"\n')
            f.write(f"start cmd /k \"{run_file}\"\n")
        print(f"[+] Added {run_file} to startup.")
    else:
        print("[!] Startup configuration is currently only supported on Windows.")

# ----- Ollama & CUDA Installation ----- #

def is_ollama_installed() -> bool:
    """Check if Ollama is already installed by looking for its command."""
    return shutil.which("ollama") is not None

def install_ollama() -> None:
    """Install Ollama if it is not already installed."""
    if is_ollama_installed():
        print("[*] Ollama is already installed.")
    else:
        print("[*] Ollama is not installed. Installing Ollama...")
        try:
            if is_windows():
                installer_url = "https://ollama.com/download/OllamaSetup.exe"
                installer_file = "ollama_installer.exe"
                print("[*] Downloading Ollama installer for Windows...")
                subprocess.check_call(
                    ["powershell", "-Command", f"Invoke-WebRequest -Uri '{installer_url}' -OutFile '{installer_file}'"],
                    shell=True
                )
                print("[*] Launching Ollama installer. Please follow the installer prompts.")
                subprocess.check_call(["start", installer_file], shell=True)
            else:
                print("[*] Downloading and running Ollama installer script...")
                subprocess.check_call("curl -fsSL https://ollama.com/install.sh | sh", shell=True)
            print("[+] Ollama installation initiated.")
        except subprocess.CalledProcessError as e:
            print(f"[-] Error installing Ollama: {e}")
            sys.exit(1)

    # Add verification check
    print("[*] Verifying Ollama installation...")
    try:
        subprocess.run(["ollama", "--version"], check=True, capture_output=True)
        print("[+] Ollama is working correctly!")
    except subprocess.CalledProcessError:
        print("[-] Ollama installation verification failed. Please ensure Ollama is properly installed and in your PATH.")
        print("    You may need to restart your terminal or computer for the changes to take effect.")
        sys.exit(1)

def is_cuda_installed() -> bool:
    """Check if CUDA is installed by looking for the nvcc command."""
    return shutil.which("nvcc") is not None

def install_cuda() -> None:
    """Install CUDA if it is not already installed."""
    if is_cuda_installed():
        print("[*] CUDA is already installed.")
        return

    print("[*] CUDA is not installed. Installing CUDA...")
    try:
        if is_windows():
            # Example: Download and run the CUDA installer for Windows.
            cuda_installer_url = "https://developer.nvidia.com/compute/cuda/11.8.0/local_installers/cuda_11.8.0_win10.exe"
            cuda_installer_file = "cuda_installer.exe"
            print("[*] Downloading CUDA installer for Windows...")
            subprocess.check_call(
                ["powershell", "-Command", f"Invoke-WebRequest -Uri '{cuda_installer_url}' -OutFile '{cuda_installer_file}'"],
                shell=True
            )
            print("[*] Launching CUDA installer. Please follow the installer prompts.")
            subprocess.check_call(["start", cuda_installer_file], shell=True)
        elif is_macos():
            print("[*] CUDA is not typically supported on macOS. Skipping CUDA installation.")
        else:
            # For Linux (e.g., Ubuntu), attempt to install via apt-get.
            print("[*] Installing CUDA via apt-get (Linux)...")
            subprocess.check_call(["sudo", "apt-get", "install", "-y", "nvidia-cuda-toolkit"])
        print("[+] CUDA installation initiated.")
    except subprocess.CalledProcessError as e:
        print(f"[-] Error installing CUDA: {e}")
        sys.exit(1)

# ----- Main Setup Flow ----- #

def main() -> None:
    print("===== Chirp Setup =====\n")

    # --- Virtual Environment Creation --- #
    if os.path.isdir("chirp_env"):
        response = input("[?] A virtual environment already exists. Create a new one? (y/n): ").strip().lower()
        if response == "y":
            create_virtualenv(force=True)
        else:
            print("[!] Using existing virtual environment.")
    else:
        create_virtualenv()

    # --- OS-Level Dependencies --- #
    if not is_windows():
        install_os_dependencies()

    # --- Python Package Installation --- #
    install_python_dependencies("requirements.txt")

    # --- Copy Configuration Files --- #
    copy_file("config_default.yaml", "config.yaml")
    copy_file(".env.example", ".env")
    print("[!] Please open .env and configure your API keys as needed.")

    # --- Install Ollama --- #
    install_ollama()

    # --- Install CUDA --- #
    # install_cuda()

    # --- Create Run Files --- #
    create_run_file()

    # --- Optional: Add to Startup (Windows only) --- #
    if is_windows():
        if input("[?] Do you want to add Chirp to startup? (y/n): ").strip().lower() == "y":
            add_to_startup("Chirp.bat")
        else:
            print("[*] Skipping startup configuration.")

    print("\n===== Setup Complete =====\n")

    # --- Activate Virtual Environment --- #
    if is_windows():
        activate_script = os.path.join("chirp_env", "Scripts", "activate.bat")
        print("[*] Activating virtual environment. A new command prompt will open.")
        subprocess.run(["cmd", "/k", activate_script])
    else:
        activate_script = os.path.join("chirp_env", "bin", "activate")
        print("[*] Activating virtual environment. A new shell will open.")
        subprocess.run(["bash", "-c", f"source {activate_script} && exec $SHELL"])

    print("===== Setup Complete =====\n")
    print("To start Chirp, run the following command:")
    print("python run.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Setup cancelled by user.")
        sys.exit(1)
