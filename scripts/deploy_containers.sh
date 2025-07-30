#!/bin/bash

# all new/updated tasks in the diff
new_tasks=($(git diff --name-only $1 $2 | grep '\.yml$'))
echo $new_tasks
echo $1 $2

if [ ! -z "$new_tasks" ]; then
  for task in "${new_tasks[@]}"; do
    ansible_tag=$(echo "$task" | awk -F/ '{print $2}')
    if [[ "$tag" != "all.yml" && "$tag" != "all.template.yml" && "$tag" != "main.yml" ]] ; then
      tag=${ansible_tag%.*}_deploy
      echo $tag
      ansible-playbook main.yml --tags "$tag" --vault-password-file ~/.vault_pass.txt
    fi
  done
fi