import random
import logging
import string
import os
import inspect
from shutit_module import ShutItModule

class shutit_faas(ShutItModule):


	def build(self, shutit):
		vagrant_image = shutit.cfg[self.module_id]['vagrant_image']
		vagrant_provider = shutit.cfg[self.module_id]['vagrant_provider']
		gui = shutit.cfg[self.module_id]['gui']
		memory = shutit.cfg[self.module_id]['memory']
		shutit.cfg[self.module_id]['vagrant_run_dir'] = os.path.dirname(os.path.abspath(inspect.getsourcefile(lambda:0))) + '/vagrant_run'
		run_dir = shutit.cfg[self.module_id]['vagrant_run_dir']
		module_name = 'shutit_faas_' + ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))
		this_vagrant_run_dir = run_dir + '/' + module_name
		shutit.cfg[self.module_id]['this_vagrant_run_dir'] = this_vagrant_run_dir
		shutit.send(' command rm -rf ' + this_vagrant_run_dir + ' && command mkdir -p ' + this_vagrant_run_dir + ' && command cd ' + this_vagrant_run_dir)
		shutit.send('command rm -rf ' + this_vagrant_run_dir + ' && command mkdir -p ' + this_vagrant_run_dir + ' && command cd ' + this_vagrant_run_dir)
		if shutit.send_and_get_output('vagrant plugin list | grep landrush') == '':
			shutit.send('vagrant plugin install landrush')
		shutit.send('vagrant init ' + vagrant_image)
		shutit.send_file(this_vagrant_run_dir + '/Vagrantfile','''Vagrant.configure("2") do |config|
  config.landrush.enabled = true
  config.vm.provider "virtualbox" do |vb|
    vb.gui = ''' + gui + '''
    vb.memory = "''' + memory + '''"
  end

  config.vm.define "faas1" do |faas1|
    faas1.vm.box = ''' + '"' + vagrant_image + '"' + '''
    faas1.vm.hostname = "faas1.vagrant.test"
  config.vm.provider :virtualbox do |vb|
    vb.name = "shutit_faas_1"
  end
  end
  config.vm.define "faas2" do |faas2|
    faas2.vm.box = ''' + '"' + vagrant_image + '"' + '''
    faas2.vm.hostname = "faas2.vagrant.test"
  config.vm.provider :virtualbox do |vb|
    vb.name = "shutit_faas_2"
  end
  end
  config.vm.define "faas3" do |faas3|
    faas3.vm.box = ''' + '"' + vagrant_image + '"' + '''
    faas3.vm.hostname = "faas3.vagrant.test"
  config.vm.provider :virtualbox do |vb|
    vb.name = "shutit_faas_3"
  end
  end
end''')
		pw = shutit.get_env_pass()
		try:
			shutit.multisend('vagrant up --provider ' + shutit.cfg['shutit-library.virtualization.virtualization.virtualization']['virt_method'] + " faas1",{'assword for':pw,'assword:':pw},timeout=99999)
		except NameError:
			shutit.multisend('vagrant up faas1',{'assword for':pw,'assword:':pw},timeout=99999)
		if shutit.send_and_get_output("""vagrant status | grep -w ^faas1 | awk '{print $2}'""") != 'running':
			shutit.pause_point("machine: faas1 appears not to have come up cleanly")
		try:
			shutit.multisend('vagrant up --provider ' + shutit.cfg['shutit-library.virtualization.virtualization.virtualization']['virt_method'] + " faas2",{'assword for':pw,'assword:':pw},timeout=99999)
		except NameError:
			shutit.multisend('vagrant up faas2',{'assword for':pw,'assword:':pw},timeout=99999)
		if shutit.send_and_get_output("""vagrant status | grep -w ^faas2 | awk '{print $2}'""") != 'running':
			shutit.pause_point("machine: faas2 appears not to have come up cleanly")
		try:
			shutit.multisend('vagrant up --provider ' + shutit.cfg['shutit-library.virtualization.virtualization.virtualization']['virt_method'] + " faas3",{'assword for':pw,'assword:':pw},timeout=99999)
		except NameError:
			shutit.multisend('vagrant up faas3',{'assword for':pw,'assword:':pw},timeout=99999)
		if shutit.send_and_get_output("""vagrant status | grep -w ^faas3 | awk '{print $2}'""") != 'running':
			shutit.pause_point("machine: faas3 appears not to have come up cleanly")


		# machines is a dict of dicts containing information about each machine for you to use.
		machines = {}
		machines.update({'faas1':{'fqdn':'faas1.vagrant.test'}})
		ip = shutit.send_and_get_output('''vagrant landrush ls | grep -w ^''' + machines['faas1']['fqdn'] + ''' | awk '{print $2}' ''')
		machines.get('faas1').update({'ip':ip})
		machines.update({'faas2':{'fqdn':'faas2.vagrant.test'}})
		ip = shutit.send_and_get_output('''vagrant landrush ls | grep -w ^''' + machines['faas2']['fqdn'] + ''' | awk '{print $2}' ''')
		machines.get('faas2').update({'ip':ip})
		machines.update({'faas3':{'fqdn':'faas3.vagrant.test'}})
		ip = shutit.send_and_get_output('''vagrant landrush ls | grep -w ^''' + machines['faas3']['fqdn'] + ''' | awk '{print $2}' ''')
		machines.get('faas3').update({'ip':ip})

		for machine in sorted(machines.keys()):
			shutit.login(command='vagrant ssh ' + machine)
			shutit.login(command='sudo su -',password='vagrant')
			root_password = 'root'
			shutit.install('net-tools') # netstat needed
			if not shutit.command_available('host'):
				shutit.install('bind-utils') # host needed
			# Workaround for docker networking issues + landrush.
			shutit.send("""echo "$(host -t A index.docker.io | grep has.address | head -1 | awk '{print $NF}') index.docker.io" >> /etc/hosts""")
			shutit.send("""echo "$(host -t A registry-1.docker.io | grep has.address | head -1 | awk '{print $NF}') registry-1.docker.io" >> /etc/hosts""")
			shutit.send("""echo "$(host -t A auth.docker.io | grep has.address | head -1 | awk '{print $NF}') auth.docker.io" >> /etc/hosts""")
			shutit.send('mkdir -p /etc/docker',note='Create the docker config folder')
			shutit.send_file('/etc/docker/daemon.json',"""{
  "dns": ["8.8.8.8"]
}""",note='Use the google dns server rather than the vagrant one. Change to the value you want if this does not work, eg if google dns is blocked.')
			shutit.multisend('passwd',{'assword:':root_password})
			shutit.send("""sed -i 's/.*PermitRootLogin.*/PermitRootLogin yes/g' /etc/ssh/sshd_config""")
			shutit.send("""sed -i 's/.*PasswordAuthentication.*/PasswordAuthentication yes/g' /etc/ssh/sshd_config""")
			shutit.send('service ssh restart || systemctl restart sshd')
			shutit.multisend('ssh-keygen',{'Enter':'','verwrite':'n'})
			shutit.logout()
			shutit.logout()
		for machine in sorted(machines.keys()):
			shutit.login(command='vagrant ssh ' + machine)
			shutit.login(command='sudo su -',password='vagrant')
			for copy_to_machine in machines:
				for item in ('fqdn','ip'):
					shutit.multisend('ssh-copy-id root@' + machines[copy_to_machine][item],{'assword:':root_password,'ontinue conn':'yes'})
			shutit.logout()
			shutit.logout()
		shutit.login(command='vagrant ssh ' + sorted(machines.keys())[0])
		shutit.login(command='sudo su -',password='vagrant')
		shutit.send('yum update -y')
		shutit.send('curl -fsSL https://test.docker.com/ | sh || curl -fsSL https://test.docker.com/ | sh')
		shutit.send('systemctl enable docker.service')
		# Workaround required for dns/landrush/docker issues: https://github.com/docker/docker/issues/18842
		shutit.insert_text('Environment=GODEBUG=netdns=cgo','/usr/lib/systemd/system/docker.service',pattern='.Service.')
		shutit.send('systemctl daemon-reload')
		shutit.send('systemctl restart docker')
		shutit.install ('git')
		shutit.send('curl -L https://github.com/docker/machine/releases/download/v0.8.2/docker-machine-`uname -s`-`uname -m` >/usr/local/bin/docker-machine && chmod +x /usr/local/bin/docker-machine')
		shutit.send('docker-machine create --engine-install-url "https://test.docker.com" -d generic --generic-ip-address ' + machines['faas1']['ip'] + ' --engine-env GODEBUG=netdns=cgo faas1')
		shutit.send('docker-machine create --engine-install-url "https://test.docker.com" -d generic --generic-ip-address ' + machines['faas2']['ip'] + ' --engine-env GODEBUG=netdns=cgo faas2')
		shutit.send('docker-machine create --engine-install-url "https://test.docker.com" -d generic --generic-ip-address ' + machines['faas3']['ip'] + ' --engine-env GODEBUG=netdns=cgo faas3')
		shutit.send('eval $(docker-machine env faas1)')
		shutit.send('docker swarm init --advertise-addr ' + machines['faas1']['ip'])
		join_cmd = shutit.send_and_get_output('docker swarm join-token worker | grep -v ^To')
		shutit.send('eval $(docker-machine env faas2)')
		shutit.send(join_cmd)
		shutit.send('eval $(docker-machine env faas3)')
		shutit.send(join_cmd)
		shutit.send('eval $(docker-machine env faas1)')
		shutit.send('docker node ls')
		shutit.send('git clone https://github.com/alexellis/faas')
		shutit.send('cd faas')
		shutit.send('./deploy_stack.sh')
		shutit.send_until('docker service ls','.*0/1.*',not_there=True)
		shutit.send('curl -X POST http://10.0.2.15:8080/function/func_hubstats -d "alexellis2"')
		shutit.pause_point('')

		shutit.logout()
		shutit.logout()
		shutit.log('''Vagrantfile created in: ''' + shutit.cfg[self.module_id]['vagrant_run_dir'] + '/' + module_name,add_final_message=True,level=logging.DEBUG)
		shutit.log('''Run:

	cd ''' + shutit.cfg[self.module_id]['vagrant_run_dir'] + '/' + module_name + ''' && vagrant status && vagrant landrush ls

To get a picture of what has been set up.''',add_final_message=True,level=logging.DEBUG)
		return True


	def get_config(self, shutit):
		shutit.get_config(self.module_id,'vagrant_image',default='centos/7')
		shutit.get_config(self.module_id,'vagrant_provider',default='virtualbox')
		shutit.get_config(self.module_id,'gui',default='false')
		shutit.get_config(self.module_id,'memory',default='1024')
		shutit.get_config(self.module_id,'vagrant_run_dir',default='/tmp')
		shutit.get_config(self.module_id,'this_vagrant_run_dir',default='/tmp')
		return True

	def test(self, shutit):
		return True

	def finalize(self, shutit):
		return True

	def is_installed(self, shutit):
		# Destroy pre-existing, leftover vagrant images.
		shutit.run_script('''#!/bin/bash
MODULE_NAME=shutit_faas
rm -rf $( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/vagrant_run/*
if [[ $(command -v VBoxManage) != '' ]]
then
	while true
	do
		VBoxManage list runningvms | grep ${MODULE_NAME} | awk '{print $1}' | xargs -IXXX VBoxManage controlvm 'XXX' poweroff && VBoxManage list vms | grep shutit_faas | awk '{print $1}'  | xargs -IXXX VBoxManage unregistervm 'XXX' --delete
		# The xargs removes whitespace
		if [[ $(VBoxManage list vms | grep ${MODULE_NAME} | wc -l | xargs) -eq '0' ]]
		then
			break
		else
			ps -ef | grep virtualbox | grep ${MODULE_NAME} | awk '{print $2}' | xargs kill
			sleep 10
		fi
	done
fi
if [[ $(command -v virsh) ]] && [[ $(kvm-ok 2>&1 | command grep 'can be used') != '' ]]
then
	virsh list | grep ${MODULE_NAME} | awk '{print $1}' | xargs -n1 virsh destroy
fi
''')
		return False

	def start(self, shutit):
		return True

	def stop(self, shutit):
		return True

def module():
	return shutit_faas(
		'swarm.shutit_faas.shutit_faas', 1979150550.0001,
		description='',
		maintainer='',
		delivery_methods=['bash'],
		depends=['shutit.tk.setup','shutit-library.virtualization.virtualization.virtualization','tk.shutit.vagrant.vagrant.vagrant']
	)
