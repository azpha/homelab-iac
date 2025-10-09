import sys
import os
import subprocess

def git_diff():
  args = sys.argv
  res = subprocess.run(f"git diff --name-only {args[1]} {args[2]}", capture_output=True, shell=True, text=True)
  return [x for x in res.stdout.strip().split("\n") if "tasks/" in x and "roles/" not in x]

def construct_command(tag = None):
  command = f"ANSIBLE_CONFIG=ansible.cfg /usr/bin/ansible-playbook main.yml --vault-password-file ~/.vault_pass.txt --tags {tag}_deploy"
  return command

def deploy(tag = None):
  if tag:
    command = construct_command(tag)
  
  print(f"Deploying {tag}...\n")
  res = subprocess.run(command, shell=True)

  return res.returncode == 0

def main():
  tasks_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../tasks")
  diff = git_diff()
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

  failed = []
  deployed = 0
  for file in diff:
    if "tasks/" in file: 
      # separating these for now because roles will typically
      # have a bunch of other things tied to them
      if "roles/" not in file:
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

      # deploy the task, regardless of its status
      task = deploy(task_name)
      if not task:
        failed.append(task_name)
      else:
        deployed += 1

  if len(failed) <= 0 and deployed > 0:
    print("\n---------------------")
    print(" Deployment succeeded!")
    print(f" All tasks: {", ".join(diff)}")
    print("---------------------\n")
  elif len(failed) > 0:
    print("\n---------------------")
    print(" Deployment failed!")
    print(f" Failed tasks: {", ".join(failed)}")
    print(f" All tasks: {", ".join(diff)}")
    print("---------------------\n")
  elif deployed <= 0:
    print("Successfully executed, no tasks required execution")

if __name__ == "__main__":
  main()