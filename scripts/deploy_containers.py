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

  print("Reloading Caddyfile..")
  subprocess.run(construct_ansible_command(tag="caddyfile_deploy"), shell=True)
  subprocess.run("docker exec -w /etc/caddy caddy caddy reload", shell=True)

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
      print(f" Reason: {reason_failed[2].split(":")[1].strip()}")
      print("---------------------\n")

      success = False
      break

  return success

def main():
  diff = git_diff()

  success = True
  for file in diff:
    if "tasks" in file:
        task_name = file.split("/")[1].split(".")[0] + "_deploy"
        state = run_deployment(tag=task_name)

        if not state:
          success = False
          break

  if success:
    print("\n---------------------")
    print(" Deployment succeeded!")
    print(f" Tasks: {", ".join(diff)}")
    print("---------------------\n")

if __name__ == "__main__":
  main()