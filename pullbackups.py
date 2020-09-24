import paramiko
import time
from scp import SCPClient
import os
import sys
from appJar import gui
import platform
import subprocess

DOCKER_PATH = "/var/lib/pgadmin/storage/"

app = gui("sqls下载", "400x200")

def open_explorer(folder):
    if platform.system() == "Linux":
        subprocess.run(["xdg-open", folder])
    elif platform.system() == "Windows":
        os.startfile(folder)
    elif platform.system() == "Darwin":
        subprocess.run(["open", folder])


def print_info(handler):
    out = handler.read().decode()
    if out:
        print(out)


def print_exec(client, command):
    _, stdout, stderr = client.exec_command(command)
    for io_ in [stdout, stderr]:
        print_info(io_)


def create_client(host, username, password):
    client = paramiko.client.SSHClient()
    client.load_system_host_keys()
    client.connect(host, username=username, password=password)
    return client


def dump_backupfiles(client, docker_path=DOCKER_PATH, dump_path="/tmp"):
    _, stdout, _ = client.exec_command(
        'docker ps -f name=pgadmin --format "{{.ID}}"', timeout=None
    )
    docker_id = stdout.read().decode().strip()
    client.exec_command(f"docker cp {docker_id}:{docker_path} {dump_path}")


def progress(filename, size, sent):
    size = float(sent) / float(size) * 100
    sys.stdout.write("%s's progress: %.2f%%   \r" % (filename, size))


def copy_to_local(client, dest):
    if not os.path.exists(dest):
        os.mkdir(dest)
    with SCPClient(client.get_transport(), progress=progress) as scp:
        scp.get("/tmp/storage/gykj_mail.com", dest, recursive=True)


def clean(client):
    print_exec(client, "rm -rf /tmp/storage")


def press(button):
    if button == "Cancel":
        app.stop()
    else:
        usr = app.getEntry("Username")
        pwd = app.getEntry("Password")
        host = app.getEntry("Ip")
        directory = app.getEntry("path")
        if not directory:
            directory = os.path.expanduser("~/sqls")
        if usr and pwd and host:
            process(host, usr, pwd, directory)

def gui_run():
    app.setFont(13)

    app.addLabel("title", "下载sqls")
    app.addDirectoryEntry("path")
    app.setEntryDefault("path", os.path.expanduser("~/sqls"))
    app.addLabelEntry("Ip")
    app.addLabelEntry("Username")
    app.addLabelSecretEntry("Password")

    app.addButtons(["Download", "Cancel"], press)
    app.setFocus("Username")

    # start the GUI
    app.go()


def process(host, username, password, dest):
    client = create_client(host, username, password)
    dump_backupfiles(client)
    copy_to_local(client, dest)
    clean(client)
    path = os.path.abspath(dest)
    open_explorer(path)


if __name__ == "__main__":
    gui_run()
