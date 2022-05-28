ansible-playbook install-dependencies.yml &&
ansible-playbook configure-postgres.yml &&
ansible-playbook install-app.yml &&
ansible-playbook install-nginx.yml &&
ansible-playbook install-ssl.yml

# Additional steps that arent very well automated:
# 1 - Create superuser (python manage.py createsuperuser, input credentials)
# 2 - Answer certbot prompts when installing ssl
# 3 - Copy classifiers/flood_depth_weights.hdf5 to machine (file to big for source control)