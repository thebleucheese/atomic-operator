wget -O atomic_operator.zip https://github.com/swimlane/atomic-operator/zipball/main/


EXTRACT_COMMAND="""
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
"""

# Set minimum required versions
PYTHON_MINIMUM_MAJOR=3
PYTHON_MINIMUM_MINOR=6

# Get python references
PYTHON3_REF=$(which python3 | grep "/python3")
PYTHON_REF=$(which python | grep "/python")

PYTHON_VERSION=''

error_msg(){
    echo "NoPython"
}

python_ref(){
    local my_ref=$1
    echo $($my_ref -c 'import platform; major, minor, patch = platform.python_version_tuple(); print(major); print(minor);')
}

# Print success_msg/error_msg according to the provided minimum required versions
check_version(){
    local major=$1
    local minor=$2
    local python_ref=$3
    
    if [[ $major -ge $PYTHON_MINIMUM_MAJOR && $minor -ge $PYTHON_MINIMUM_MINOR ]]; then
        echo $($python_ref -c "$EXTRACT_COMMAND")
    else
        error_msg
    fi
}

# Logic
if [[ ! -z $PYTHON3_REF ]]; then
    version=($(python_ref python3))
    check_version ${version[0]} ${version[1]} $PYTHON3_REF
elif [[ ! -z $PYTHON_REF ]]; then
    # Didn't find python3, let's try python
    version=($(python_ref python))
    check_version ${version[0]} ${version[1]} $PYTHON_REF
else
    # Python is not installed at all
    error_msg
fi
