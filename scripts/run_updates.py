import requests
import subprocess
import os
import yaml

def search_for_image(image_name):
  tasks_folder = os.path.realpath(os.path.join('./', 'tasks'))
  if "library/" in image_name:
    image_name = image_name.replace("library/", "")
  
  for task in os.listdir(tasks_folder):
    with open(os.path.join(tasks_folder, task), 'r') as file:
      data = yaml.safe_load(file)

      for key in data:
        if "docker_image" in key:
          if image_name in key["docker_image"]["name"]:
            return f"{task.split(".")[0]}_deploy"

def main():
  update_list = requests.get("https://cup.fntz.net/api/v3/json")
  update_list.raise_for_status()
  update_list = update_list.json()

  deployable_tags = []
  with open("main.yml", 'r') as file:
    data = yaml.safe_load(file)
    for host in data:
      for task in host['tasks']:
        deployable_tags.append(task['tags'])

  if len(update_list["images"]) <= 0:
    print("No images to update!")
  else:
    print(f"Updating {update_list["metrics"]["updates_available"]} image(s)..\n")

    for image in update_list["images"]:
      if image['result']['has_update']:
        if "remote_digest" in image["result"]["info"]:
          image_name = image["parts"]["repository"]
          ansible_tag = search_for_image(image_name) 

          if ansible_tag and ansible_tag in deployable_tags:
            print(f"Updating '{image_name}' ({ansible_tag})..")
            subprocess.run(f'docker image pull {image_name}', shell=True)
            subprocess.run(f'ANSIBLE_CONFIG=ansible.cfg ansible-playbook main.yml --tags {ansible_tag} --vault-password-file=~/.vault_pass.txt', shell=True)

    print("\nAll images updated, refreshing Cup")
    requests.get("https://cup.fntz.net/api/v3/refresh")

if __name__ == "__main__":
  main()
