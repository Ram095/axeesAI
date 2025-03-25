@echo off
REM This command turns off the display of commands in the batch file, so only the output is shown.

python -m venv venv
REM This command creates a virtual environment named 'venv' in the current directory.

call venv\Scripts\activate
REM This command activates the virtual environment. On Windows, it runs the activate script located in the 'venv\Scripts' directory.

pip install -r requirements.txt
REM This command installs the Python packages listed in the 'requirements.txt' file into the virtual environment.

set MLFLOW_TRACKING_URI=sqlite:///mlflow.db
REM This command sets an environment variable 'MLFLOW_TRACKING_URI' to use a SQLite database named 'mlflow.db' for MLflow tracking.

echo Virtual environment setup complete!
REM This command prints a message indicating that the virtual environment setup is complete.
