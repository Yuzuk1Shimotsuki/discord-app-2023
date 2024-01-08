import os

# This script will install all the packages required for this project one by one
# RUN THIS SCRIPT FIRST BEFORE executing "pip install -r requirements.txt"

if os.name == 'nt':
    # For Windows
    pip_name = "pip"
elif os.name == 'posix':
    # For Mac/Linux/BSD
    pip_name = "pip3"
else:
    raise("Runtime error: Unsupported OS")
    exit(1)

os.system(f"{pip_name} install discord.py[voice]")
os.system(f"{pip_name} install py-cord")
