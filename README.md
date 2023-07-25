# KVM
Scripts to support KVM virtual infrastructure

---

## Lost_VM

Script looks into specified OLVM/oVirt URL and searches for VMs that do not resolve in DNS. This may indicate a stray VM, test VM or a VM clone. VM data (cluster name, VM name, creation date, disk summ size) is saved into csv. This may be used to make an inventory of unused VMs to keep KVM infrastructure clean.

Script may be run from command line or used in automation tools like rundeck.

tested with OLVM v4.3, v4.4, oVirt v4.4

---

## Unattached_disks

Script looks into specified OLVM/oVirt URL and searches for unattached disks, i.e. disks that are not connected to VM. Information about disks (service name, storage name, disk name, disk size) is saved into csv file. ISO disks are also found and they are saved into second scv. The script may be used to keep track of unattached disks and optimize storage capacity by removing forgotten disks. 

Script may be run from command line or used in automation tools like rundeck.

tested with OLVM v4.3, v4.4, oVirt v4.4

---

## Add_vlan

This is an interactive script that adds VLANs from csv file to the specified datacenter of KVM server/

Script is to be run from the command line.

tested with OLVM v4.3, v4.4, oVirt v4.

---

## Move disks between KVM data domains

This is an interactive script that moves VM disks between storage data domains. Disk names are accepted as command line parameters, seprated by space. Before running this script make sure to prepare csv file with disk names that need to be moved and their target storage domain ids.

Usage example:
<pre>
#python3 move_disks.py server1_backups server1_system
</pre>
