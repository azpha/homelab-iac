#!/bin/bash
# all new/updated tasks in the diff
new_tasks=($(git diff --name-only $1 $2 | grep '\.yml$'))
echo $new_tasks
echo $1 $2

if [ ! -z "$new_tasks" ]; then
  echo "Redeploying Caddy.."
  ansible-playbook main.yml --tags "caddy_deploy" --vault-password-file ~/.vault_pass.txt

  for task in "${new_tasks[@]}"; do
    ansible_tag=$(echo "$task" | awk -F/ '{print $2}')
    if [[ "$ansible_tag" != "all.yml" && "$ansible_tag" != "all.template.yml" && "$ansible_tag" != "main.yml" ]] ; then
      tag=${ansible_tag%.*}_deploy
      if [[ "$tag" != "_deploy" ]] ; then 
        ansible-playbook main.yml --tags "$tag" --vault-password-file ~/.vault_pass.txt
      fi
    fi
  done
fi