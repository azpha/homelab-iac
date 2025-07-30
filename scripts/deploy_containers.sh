#!/bin/bash

# all new/updated tasks in the diff
echo $1 $2

new_tasks = ($(git diff --name-only $1 $2 | grep '\.yml$'))

if [! -z "$new_tasks"]; then
  for task in "${new_tasks[@]}"; do
    ansible_tag=$(echo "$task" | awk '{print $2}')
    if [[ "$tag" != "all.yml" && "$tag" !== "all.template.yml" && "$tag" !== "main.yml" ]]
      tag = ${tag%.*}_deploy
      ansible-playbook --tags "$tag" --vault-password-file ~/.vault_password.txt
    fi
  done