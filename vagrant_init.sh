#!/bin/bash

# This script will be run by Vagrant to
# set up everything necessary to use backtrader

# Because this is intended be a disposable dev VM setup,
# no effort is made to use virtualenv/virtualenvwrapper

# It is assumed that you have "vagrant up"
# from the root of the zipline github checkout.
# This will put the zipline code in the
# /vagrant folder in the system.

VAGRANT_LOG="/home/vagrant/vagrant.log"

# Need to "hold" grub-pc so that it doesn't break
# the rest of the package installs (in case of a "apt-get upgrade")
# (grub-pc will complain that your boot device changed, probably
#  due to something that vagrant did, and break your console)

echo "Obstructing updates to grub-pc..."
apt-mark hold grub-pc 2>&1 >> "$VAGRANT_LOG"

# Run a full apt-get update first.
echo "Updating apt-get caches..."
apt-get -y update 2>&1 >> "$VAGRANT_LOG"

# Install required packages
echo "Installing required packages..."
echo "Installing python-pip ..."
apt-get -y install python-pip python-dev 2>&1 >> "$VAGRANT_LOG"
echo "Installing lib for scipy..."
apt-get -y install libblas-dev liblapack-dev libatlas-base-dev gfortran  2>&1 >> "$VAGRANT_LOG" # for scipy
echo "Installing lib for matplotlib..."
apt-get -y install libfreetype6-dev libpng-dev tk tk-dev python-tk 2>&1 >> "$VAGRANT_LOG" # for matplotlib

# do pip install
echo "Installing pip packages: setuptools ..."
pip install -U setuptools distribute 2>&1 >> "$VAGRANT_LOG" 
echo "Installing pip packages: scipy/numpy ..."
pip install scipy statsmodels numpy 2>&1 >> "$VAGRANT_LOG" 
echo "Installing pip packages: pytz ..."
pip install python-dateutil pytz ipython 2>&1 >> "$VAGRANT_LOG"
echo "Installing pip packages: matplotlib ..."
pip install matplotlib 2>&1 >> "$VAGRANT_LOG" 
#pip install scipy statsmodels 2>&1 >> "$VAGRANT_LOG" 
#pip install numpy 2>&1 >> "$VAGRANT_LOG" 

# vim install
echo "Installing vim and git..."
apt-get -y install ctags vim git
git clone https://github.com/amix/vimrc.git ~/.vim_runtime
sh ~/.vim_runtime/install_awesome_vimrc.sh

cd /vagrant
echo "installing local backtrader ..."
pip install -e . 2>&1 >> "$VAGRANT_LOG"

echo "Finished!"
