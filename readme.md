# Homelab IaC

This repository hosts my homelab infrastructure setup, built using Ansible & Gitea Workflows.

## Getting started

You'll need to install Ansible Playbook, either through APT or another avenue.

```
sudo apt install ansible-core
```

Once you've done so, configure the [hosts](./hosts) file to direct to your server(s). You'll need to deal with the SSH setup, alongside setting up the host variables for each service you want to use.

## Project setup

I have this project set up like so;

- **tasks/** - All of the playbooks for the services I deploy
- **roles/** - More comprehensive tasks, like FiveM which requires multiple JNinja templates
- **scripts/** - Any utility scripts, like the one used for deployment
- **host_vars/** - All host variables, containings variables for each service
- **main.yml** - Playbook that contains all the setup for the automated deployment

## Deployment

In my lab, I have a Git runner sitting on my local network. I use this to deploy changes to this repository across all of my machines.

The business logic for how this is done is in the `scripts/deploy_containers.py` script, which handles

- Deploying new containers
- Redeploying changed containers based on the Git diff
- Redeploying VPN-based containers that need to restart when Gluetun does
- Redeploying containers when secrets update
- Cleaning up containers/images when tasks are removed

This uses `tags` in [main.yml](./main.yml), structured as `{container}_deploy` - so if I update Immich, it will run ansible-playbook with the argument `--tags immich_deploy`.

When secrets for a specific host are detected as updated, it will run the deploy tasks for all containers that host has (`-l {host}`) to refresh environment variables.
