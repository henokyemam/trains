import os
import sys
import subprocess
from copy import deepcopy
import socket
from tempfile import mkstemp
# make sure we have jupter in the auto requirements
import jupyter
from trains import Task


# set default docker image, with network configuration
os.environ['TRAINS_DOCKER_IMAGE'] = 'nvidia/cuda --network host'

# initialize TRAINS
task = Task.init(project_name='examples', task_name='Remote Jupyter NoteBook')

# get rid of all the runtime TRAINS
preserve = ('TRAINS_API_HOST', 'TRAINS_WEB_HOST', 'TRAINS_FILES_HOST', 'TRAINS_CONFIG_FILE',
            'TRAINS_API_ACCESS_KEY', 'TRAINS_API_SECRET_KEY', 'TRAINS_API_HOST_VERIFY_CERT')

# setup os environment
env = deepcopy(os.environ)
for key in os.environ:
    if key.startswith('TRAINS') and key not in preserve:
        env.pop(key, None)

# Add jupyter server base folder
param = {
    'jupyter_server_base_directory': '',
}
task.connect(param)

# execute jupyter notebook
fd, local_filename = mkstemp()
cwd = os.path.expandvars(os.path.expanduser(param['jupyter_server_base_directory'])) \
    if param['jupyter_server_base_directory'] else os.getcwd()
print('Running Jupyter Notebook Server on {} [{}] at {}'.format(socket.gethostname(),
                                                                socket.gethostbyname(socket.gethostname()), cwd))
process = subprocess.Popen([sys.executable, '-m', 'jupyter', 'notebook', '--no-browser', '--allow-root'],
                           env=env, stdout=fd, stderr=fd, cwd=cwd)

# print stdout/stderr
prev_line_count = 0
process_running = True
while process_running:
    process_running = False
    try:
        process.wait(timeout=2.0 if prev_line_count == 0 else 15.0)
    except subprocess.TimeoutExpired:
        process_running = True

    with open(local_filename, "rt") as f:
        # read new lines
        new_lines = f.readlines()
        if not new_lines:
            continue
        output = ''.join(new_lines)
        print(output)
        # update task comment with jupyter notebook server links
        if prev_line_count == 0:
            task.comment += '\n' + ''.join(line for line in new_lines if 'http://' in line or 'https://' in line)
        prev_line_count += len(new_lines)

    os.lseek(fd, 0, 0)
    os.ftruncate(fd, 0)

# cleanup
os.close(fd)
try:
    os.unlink(local_filename)
except:
    pass
