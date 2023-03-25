# KVM
Scripts to support KVM virtual infrastructure

--

## Lost_VM

Script looks into specified OLVM/oVirt URL and searches for VMs that do not resolve in DNS. This may indicate a stray VM, test VM or a VM clone. VM data (cluster name, VM name, creation date, disk summ size) is saved into csv. This may be used to make an inventory of unused VMs to keep KVM infrastructure clean.

Script may be run from command line or used in automation tools like rundeck.

tested with OLVM v4.3, v4.4, oVirt v4.4

---------------------------------------

## Unattached_disks

Script looks into specified OLVM/oVirt URL and searches for unattached disks, i.e. disks that are not connected to VM. Information about disks (service name, storage name, disk name, disk size) is saved into csv file. ISO disks are also found and they are saved into second scv. The script may be used to keep track of unattached disks and optimize storage capacity by removing forgotten disks. 

Script may be run from command line or used in automation tools like rundeck.

tested with OLVM v4.3, v4.4, oVirt v4.4

