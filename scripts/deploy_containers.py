import re
import sys
import os
import subprocess

bracket_regex = r'\[([^\]]*)\]'
quote_regex = r'"([^"]*)"'

def git_diff():
  args = sys.argv
  print(args[1], args[2])
  res = subprocess.run(f"git diff --name-only {args[1]} {args[2]}", capture_output=True, shell=True, text=True)
  return res.stdout.strip().split("\n")

def construct_ansible_command(tag = None):
  command = "ANSIBLE_CONFIG=ansible.cfg /usr/bin/ansible-playbook main.yml --vault-password-file ~/.vault_pass.txt"

  if tag:
    command += f" --tags {tag}"

  return command

def run_deployment(tag = None):
  if tag:
    command = construct_ansible_command(tag=tag)

  print(f"Running deployment for {tag}..")
  res = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  lines = res.stdout.decode(encoding='utf-8').split("\n")
  
  success = True
  for ind, line in enumerate(lines):
    if "fatal:" in line:
      success = False
      host = re.findall(bracket_regex, line)[0]
      task_failed = re.findall(bracket_regex, lines[ind - 1])[0]
      reason_failed = re.findall(quote_regex, line)

      print(f"\n{tag} failed deployment!\n{host}\n{reason_failed}\n{task_failed}\n")
      break

  return success

def main():
  tasks_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../tasks")
  diff = git_diff()
  vpn_containers = [
    "tasks/qbittorrent.yml",
    "tasks/jackett.yml"
  ]

  success = True
  deployed = 0

  # auto-heal any vpn-dependent containers
  if "tasks/gluetun.yml" in diff:
    for container in vpn_containers:
      if container not in diff:
        print(f"Adding {container} to restart list as Gluetun is present..")
        diff.append(container)

  for file in diff:
    if "tasks" in file:
        print(os.path.dirname(os.path.abspath(__file__)))
        if not os.path.exists(os.path.join(tasks_path, file.split("/")[1])):
          container_name = file.split("/")[1].replace(".yml", "").replace(".yaml", "")
          print(f"file does not exist! attempting to remove docker container \"{container_name}\"..")

          res = subprocess.run(f"/usr/bin/docker container stop {container_name}")
          if res.returncode == 0:
            subprocess.run(f"/usr/bin/docker container rm {container_name}")
            subprocess.run(f"/usr/bin/docker image prune -f")
            subprocess.run(f"/usr/bin/docker container prune -f")

            print(f"successfully removed container \"{container_name}\"")
          else:
            print(f"non-0 error code returned for stop command on container \"{container_name}\"")
        else:
          task_name = file.split("/")[1].split(".")[0] + "_deploy"
          state = run_deployment(tag=task_name)

          if not state:
            success = False
            break
          else:
            deployed += 1

  if success and deployed > 0:
    print("\n---------------------")
    print(" Deployment succeeded!")
    print(f" Tasks: {", ".join(diff)}")
    print("---------------------\n")
  elif deployed == 0:
    print("Successful, no containers required deployment")

if __name__ == "__main__":
  main()