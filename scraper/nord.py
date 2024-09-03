import subprocess

nordvpn_path = r"C:\Program Files\NordVPN\NordVPN.exe"
command = f'& "{nordvpn_path}" -c'

try:
    result = subprocess.run(
        ["powershell", "-Command", command],
        capture_output=True,
        text=True,
        check=True  # Raises CalledProcessError if command fails
    )
    print(result.stdout)
except subprocess.CalledProcessError as e:
    print(f"An error occurred: {e.stderr}")
