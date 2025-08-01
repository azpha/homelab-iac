import re
import sys
import subprocess

bracket_regex = r'\[([^\]]*)\]'
quote_regex = r'"([^"]*)"'

def git_diff():
  args = sys.argv
  res = subprocess.run(f"git diff --name-only {args[1]} {args[2]}", capture_output=True, shell=True, text=True)
  return res.stdout.strip().split("\n")

def construct_ansible_command(server_name = None, tag = None):
  command = "ANSIBLE_CONFIG=ansible.cfg /usr/bin/ansible-playbook main.yml --vault-password-file ~/.vault_pass.txt"

  if server_name:
    command += f" -l {server_name}"
  if tag:
    command += f" --tags {tag}"

  return command

def run_deployment(server_name = None, tag = None):
  if tag:
    print(f"Deploying task '{tag}'..")
    command = construct_ansible_command(tag=tag)
  elif server_name:
    print(f"Deploying caddy on server '{server_name}'..")
    command = construct_ansible_command(server_name, "caddy_server")

  res = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  lines = res.stdout.decode(encoding='utf-8').split("\n")
  for ind, line in enumerate(lines):
    if "fatal:" in line:
      host = re.findall(bracket_regex, line)[0]
      task_failed = re.findall(bracket_regex, lines[ind - 1])[0]
      reason_failed = re.findall(quote_regex, line)

      print("\n---------------------")
      print(" Deployment failed!")
      print(f" Task: {task_failed}")
      print(f" Host: {host}")
      print(f" Reason: {reason_failed[2].split(":")[1].strip()}")
      print("---------------------\n")

def main():
  diff = git_diff()

  for file in diff:
    if "host_vars" in file:
        server_name = file.split("/")[1].split(".")[0]
        run_deployment(server_name=server_name)
    if "tasks" in file:
        task_name = file.split("/")[1].split(".")[0] + "_deploy"
        run_deployment(tag=task_name)

if __name__ == "__main__":
  main()