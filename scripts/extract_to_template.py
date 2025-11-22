import os
import subprocess

host_vars_path = os.path.abspath('host_vars')
file_contents = ""

if os.path.exists(host_vars_path):
  if os.path.exists(os.path.join(host_vars_path, 'all.template.yml')):
    os.remove(os.path.join(host_vars_path, 'all.template.yml'))
    
  vaults = os.listdir(host_vars_path)

  # 1st run - extract ungrouped, global variables
  for vault in vaults:
    vault_path = os.path.join(host_vars_path, vault)
    vault_contents = subprocess.run(f'ansible-vault decrypt "{vault_path}" --vault-password-file ~/.vault_pass.txt --output -', shell=True, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    stdout = vault_contents.stdout.strip().splitlines()

    for line in stdout:
      if line.startswith("#"):
        break
      elif line.split(":")[0] not in file_contents:
        file_contents += f"{line.split(":")[0]}:\n"
        
  # 2nd run - extract service-specific variables
  for vault in vaults:
    vault_path = os.path.join(host_vars_path, vault)
    vault_contents = subprocess.run(f'ansible-vault decrypt "{vault_path}" --vault-password-file ~/.vault_pass.txt --output -', shell=True, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    stdout = vault_contents.stdout.strip().splitlines()

    has_found_start = False
    for line in stdout:
      if has_found_start or line.startswith("#"):
        if not has_found_start:
          has_found_start = True
        
        if line.startswith("#") and line not in file_contents:
          file_contents += f"\n{line}\n"

        if ":" in line:
          if line.split(":")[0] not in file_contents:
            file_contents += f'{line.split(":")[0]}:\n'

  with open(os.path.join(host_vars_path, 'all.template.yml'), 'w', encoding="utf8") as template_file:
    template_file.write(file_contents)
    template_file.close()

    print("Written to disk!")