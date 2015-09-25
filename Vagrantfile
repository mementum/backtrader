# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  #config.ssh.forward_agent = true
  config.ssh.forward_x11 = true
  config.vm.box = "ARTACK/debian-jessie"
  config.vm.box_url = "https://atlas.hashicorp.com/ARTACK/boxes/debian-jessie"
  #config.vm.box = "remram/debian-8-amd64"
  #config.vm.box_url = "https://atlas.hashicorp.com/remram/boxes/debian-8-amd64"
  config.vm.define "bktraderhost"
  config.vm.provider :virtualbox do |vb|
    vb.customize ["modifyvm", :id, "--memory", 1024, "--cpus", 1]
    vb.customize ["modifyvm", :id, "--audio", "none"]
    vb.customize ["modifyvm", :id, "--usb", "on"]
    vb.customize ["modifyvm", :id, "--usbehci", "off"]
  end
  config.vm.provision "shell", path: "vagrant_init.sh"
end
