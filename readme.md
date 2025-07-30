# Homelab IaC

This repository hosts my homelab infrastructure setup, built using Ansible & Gitea Workflows.

## Getting started

You'll need to install Ansible Playbook, either through APT or another avenue.

```
sudo apt install ansible-core
```

Then, configure your vaults using the variable templates provided & update the hosts file to match your hosts. After you've done so, you can simply run `ansible-playbook main.yml` & it will deploy all containers.
