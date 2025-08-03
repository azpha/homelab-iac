import re
import sys
import subprocess

bracket_regex = r'\[([^\]]*)\]'
quote_regex = r'"([^"]*)"'

def git_diff():
  args = sys.argv
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
      host = re.findall(bracket_regex, line)[0]
      task_failed = re.findall(bracket_regex, lines[ind - 1])[0]
      reason_failed = re.findall(quote_regex, line)

      print("\n---------------------")
      print(" Deployment failed!")
      print(f" Task: {task_failed}")
      print(f" Host: {host}")
      print(f" Reason: {reason_failed}")
      print(line)
      print("---------------------\n")

      sys.exit(1)

  return success

def main():
  diff = git_diff()
  vpn_containers = [
    "tasks/qbittorrent.yml"
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