ansible-playbook install-dependencies.yml &&
ansible-playbook configure-postgres.yml &&
ansible-playbook install-app.yml &&
ansible-playbook install-nginx.yml &&
ansible-playbook install-ssl.yml

# Additional steps that arent very well automated:
# 1 - Create superuser (python manage.py createsuperuser, input credentials)
# 2 - Answer certbot prompts when installing ssl
# 3 - Copy classifiers/flood_depth/weights.hdf5 to machine (file to big for source control)
# 4 - Make docs: cd docs && make html
# 5 - Create components by 'python manage.py shell' and importing main from context/create_existing_plugins.py
# Note: If /media files aren't showing, the problem is probably with permissions.
# To confirm this, check the nginx error logs: tail -10 /var/log/nginx/error.log
# If says something like "Permission denied", it confirms.
# The user may have permissions for the folder /media, but may not have for the folders above
# To solve, check the internet. In extreme case, give permissions to all (chmod 777) to the folders above /media


# Problems related with Oracle and port opening:
# https://stackoverflow.com/questions/62326988/cant-access-oracle-cloud-always-free-compute-http-port
# These 3 commands are very important to make it work:
# sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT (for HTTP)
# sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT (for HTTPS)
# sudo netfilter-persistent save (to save)