import sys
import os
import subprocess

def git_diff():
  args = sys.argv
  res = subprocess.run(f"git diff --name-only {args[1]} {args[2]}", capture_output=True, shell=True, text=True)
  return [x for x in res.stdout.strip().split("\n") if "tasks/" in x or "roles/" in x or "host_vars" in x]

def construct_command(tag = None, host = None):
  command = f"ANSIBLE_CONFIG=ansible.cfg /usr/bin/ansible-playbook main.yml --vault-password-file ~/.vault_pass.txt"

  if host:
    command += f" -l {host}"
  if tag:
    command += f" --tags {tag}_deploy"

  return command

def deploy(tag = None, host = None):
  command = construct_command(tag, host)
  
  if tag:
    print(f"Deploying {tag}...\n")
  else:
    print(f"Deploying {host}...\n")
  res = subprocess.run(command, shell=True)

  return res.returncode == 0

def main():
  tasks_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../tasks")
  diff = git_diff()
  host_vars_changed_for = []
  vpn_containers = [
    "tasks/qbittorrent.yml",
    "tasks/jackett.yml"
  ]

  # because these containers rely on gluetun for network, they need to be recreated when gluetun is recreated
  if "tasks/gluetun.yml" in diff:
    print("Gluetun detected in diff, queuing dependent containers for recreation")
    for container in vpn_containers:
      if container not in diff:
        diff.append(container)

  # when variables update for a host & there are no other modified containers, recreate containers on host
  # for file in diff:
  #   if "host_vars" in file:
  #     hostname = file.split("/")[1].split(".")[0]
  #     print(f"Secret file for '{hostname}' changed, will recreate containers on host after deployment")
  #     host_vars_changed_for.append(hostname)

  deployed = []
  failed = []
  removed = []
  for file in diff:
    # separating these for now because roles will typically
    # have a bunch of other things tied to them
    if "roles/" not in file and "host_vars/" not in file:
      task_name = file.split("/")[1].split(".")[0]
      task_file_path = os.path.join(tasks_path, file.split("/")[1])

      if not os.path.exists(task_file_path):
        print(f"{task_name} doesn't exist, running cleanup")
        res = subprocess.run(f"/usr/bin/docker container stop {task_name}", shell=True)
        if res.returncode == 0:
          subprocess.run(f"/usr/bin/docker container rm {task_name}", shell=True)
          subprocess.run("/usr/bin/docker image prune -f", shell=True)
          subprocess.run("/usr/bin/docker container prune -f", shell=True)

          print(f"Cleaned up container {task_name}")
          removed.append(task_name)


    if "host_vars" not in file and task_name not in removed:
      # deploy the task, regardless of its status
      if "roles/" not in file:
        if task_name not in deployed:
          task = deploy(tag=task_name)
      else:
        task_name = file.split("/")[1]
        
        if task_name not in deployed:
          task = deploy(tag=task_name)

      if not task:
        failed.append(task_name)
      else:
        deployed.append(task_name)

  if len(host_vars_changed_for) > 0:
    for host in host_vars_changed_for:
      print(f"Redeploying containers on {host} due to host vars update")
      task = deploy(host=host)
      if task:
        deployed.append(host)
      else:
        failed.append(host)


  if len(failed) <= 0 and len(deployed) > 0:
    print("\n---------------------")
    print(" Deployment succeeded!")
    print(f" All tasks: {", ".join(deployed)}")
    print("---------------------\n")
    sys.exit(0)
  elif len(failed) > 0:
    print("\n---------------------")
    print(" Deployment failed!")
    print(f" Failed tasks: {", ".join(failed)}")
    print(f" All tasks: {", ".join(deployed)}")
    print("---------------------\n")
    sys.exit(1)
  elif len(deployed) <= 0:
    print("Successfully executed, no tasks required execution")
    sys.exit(0)

if __name__ == "__main__":
  main()