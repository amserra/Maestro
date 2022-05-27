ansible-playbook install-dependencies.yml &&
ansible-playbook configure-postgres.yml &&
ansible-playbook install-app.yml &&
ansible-playbook install-nginx.yml