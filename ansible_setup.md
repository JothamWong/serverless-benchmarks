# Using ansible approach to deploy Openwhisk.

First, clone openwhisk somewhere.

cd into openwhisk/ansible.

We will be using elasticsearch as the activation store. This has better performance for storing the activations.

By default, the scheduler has already been set up/enabled.

Make sure ansible python is set up.

```bash
echo -e "\nansible_python_interpreter: `which python`\n" >> ./environments/local/group_vars/all
```

```bash
# First time set up
export ENVIRONMENT=local
ansible-playbook -i environments/$ENVIRONMENT prereq.yml

cd <openwhisk_home>
./gradlew distDocker
cd ansible
# couchdb is still needed to store subjects and actions
ansible-playbook -i environments/$ENVIRONMENT couchdb.yml
ansible-playbook -i environments/$ENVIRONMENT initdb.yml
ansible-playbook -i environments/$ENVIRONMENT wipe.yml
# this will deploy a simple ES cluster, you can skip this to use external ES cluster
ansible-playbook -i environments/$ENVIRONMENT elasticsearch.yml
ansible-playbook -i environments/local  -e limit_invocations_per_minute=999999 -e limit_invocations_concurrent=999999 -e db_activation_backend=ElasticSearch openwhisk.yml

# installs a catalog of public packages and actions
ansible-playbook -i environments/$ENVIRONMENT postdeploy.yml

# to use the API gateway
ansible-playbook -i environments/$ENVIRONMENT apigateway.yml
ansible-playbook -i environments/$ENVIRONMENT routemgmt.yml
```