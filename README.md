# KVM
Collection of scripts to support KVM virtual infrastructure

##Lost_VM
This script looks into specified OLVM/Ovirt URL and searches for VMs that do not resolve in DNS. This may indicate a stray VM, test VM or a VM clone. VM data (cluster name, VM name, creation date, disk summ size) is saved into csv. This may be used to make an inventory of unused VMs to keep KVM infrastructure clean.

Script may be run from command line or used in automation tools like rundeck.
