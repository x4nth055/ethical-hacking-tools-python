import platform
import subprocess

def end_python_processes():
    """
    Terminates all running python.exe processes on the system.
    This function is designed to work across different platforms (Windows, macOS, Linux).
    """
    system = platform.system().lower()

    try:
        if system == "windows":
            # For Windows
            subprocess.run(["taskkill", "/F", "/IM", "python.exe"], check=True)
        elif system in ["darwin", "linux"]:
            # For macOS and Linux
            subprocess.run(["pkill", "-f", "python"], check=True)
        else:
            print(f"Unsupported operating system: {system}")
            return

        print("All Python processes have been terminated successfully.")
    except subprocess.CalledProcessError:
        print("No Python processes found or unable to terminate processes.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    # Confirm with the user before proceeding
    confirmation = input("This will terminate all Python processes. Are you sure? (y/n): ")
    
    if confirmation.lower() == 'y':
        end_python_processes()
    else:
        print("Operation cancelled.")
