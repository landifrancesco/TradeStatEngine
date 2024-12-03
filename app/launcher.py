import subprocess
import sys


def run_app():
    try:
        flask_process = subprocess.Popen([sys.executable, "app.py"])
        dash_process = subprocess.Popen([sys.executable, "dashboard.py"])

        flask_process.wait()
        dash_process.wait()
    except KeyboardInterrupt:
        flask_process.terminate()
        dash_process.terminate()


if __name__ == "__main__":
    run_app()
