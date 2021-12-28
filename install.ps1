Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))


$Url = 'https://github.com/swimlane/atomic-operator/zipball/main/'
$DownloadZipFile = "$([Environment]::GetFolderPath("Desktop"))/atomic-operator.zip"

Invoke-RestMethod -Uri $Url -ContentType 'application/zip' -OutFile $DownloadZipFile

Set-Location -Path [Environment]::GetFolderPath("Desktop")

$EXTRACT_COMMAND="
import os
import sys
import subprocess
from io import BytesIO
from zipfile import ZipFile
directory = None
with ZipFile('atomic_operator.zip') as zf:
    for member in zf.infolist():
        file_path=os.path.realpath(os.path.join(os.getcwd(), member.filename))
        if file_path.startswith(os.path.realpath(os.getcwd())):
            zf.extract(member, os.getcwd())
        if not directory:
            directory = file_path
if directory:
    os.chdir(directory)
    subprocess.check_call([sys.executable, 'setup.py', 'install'])
"

python -c "$EXTRACT_COMMAND"
