
# Script to find unattched disks in KVM 

from curses.ascii import DC3
import logging, dns.resolver
import ovirtsdk4 as sdk
import ovirtsdk4.types as types
import re, sys, base64, requests, getopt, socket, csv, os
from os.path import exists

#Enter connection details
OLVM_USER = "roadmin@internal" #Read-only admin
OLVM_PASS = "yourpassword"
OLVM_URLs = ["https://kvm-address/ovirt-engine/api"]

#Turn off warnings when connecting without certs
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

#Check if ovirt service is reachable
def getStatuscode(url,user,passw):
    try:
        r = requests.head(url,verify=False,timeout=5,auth = (user, passw))
        return (r.status_code)
    except:
        return -1

#Function to establish connection with KVM
def olvm_connect(OLVM_URL, OVIRT_CA):
    connection = sdk.Connection(
        url=OLVM_URL,
        username=OLVM_USER,
        password=OLVM_PASS,
        ca_file=OVIRT_CA,
        # debug=True,
        # log=logging.getLogger(),
        insecure=True,
    )
    return connection

#Check certificate availability
def getStatusCA(ca_file):
    file_exists = exists(ca_file)
    return file_exists


#Function to clean up csv file
def clearCSV(cloneinfo):
    filename = cloneinfo
    f = open(filename, "w+")
    f.close()


#Fuction to add entries into csv file
def appendCSV(title, cloneinfo):
    with open(cloneinfo, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerows(title)

#Function to make an array of udisks attached to VMs (they should be excluded)
def attachedDisks(connection):
    vms_service = connection.system_service().vms_service()
    vms = vms_service.list()
    attached_disks = []
    for vm in vms:
        vm_service = vms_service.vm_service(vm.id)
        disk_attachments_service = vm_service.disk_attachments_service()
        #vm_disk_summ = 0
        disk_attachments = disk_attachments_service.list()
        for disk_attachment in disk_attachments:
            disk = connection.follow_link(disk_attachment.disk)
            vm_disk_name = disk.name
            attached_disks.append(vm_disk_name)
    #print(attached_disks)
    return attached_disks


#Function to make an array of disks attached to templates (they should be excluded)
def templateDisks(connection):
    templates_service = connection.system_service().templates_service()
    tms = templates_service.list()
    template_disks = []
    for tm in tms:
        template_service = templates_service.template_service(tm.id)
        disk_attachments_service = template_service.disk_attachments_service()
        #vm_disk_summ = 0
        disk_attachments = disk_attachments_service.list()
        for disk_attachment in disk_attachments:
            disk = connection.follow_link(disk_attachment.disk)
            vm_disk_name = disk.name
            template_disks.append(vm_disk_name)
    #print(template_disks)
    return template_disks


#Function to make an array of disks using disk service. i.e. all disks that can be found on storage
def allDisks(connection):
    # Get all disks in datacenter
    disk_service = connection.system_service().disks_service()
    disks = disk_service.list()

    # Filter disks that are not connected to any VM
    all_disks = []
    for disk in disks:
        disk_name = disk.name
        all_disks.append(disk_name)
    
    #print(unattached_disks)
    return all_disks

#Function to make an array of ISO disks (saved into own csv file)
def isoDisks(connection):
    # Get all disks in datacenter
    disk_service = connection.system_service().disks_service()
    disks = disk_service.list()

    # Filter disks that are not connected to any VM
    iso_disks = []
    for disk in disks:
        disk_iso = str(disk.content_type)
        disk_name = disk.name
        if disk_iso == 'iso':
            iso_disks.append(disk_name)
    
    #print(iso_disks)
    return iso_disks

# Function to create csv with unattached disks. 
def findUnattachedDisks(attached_disks, all_disks, template_disks, iso_disks, OLVM_SERVICE_NAME, connection, diskinfo):
    unattached_disks = []
    olvm_service = OLVM_SERVICE_NAME
    for disk in all_disks:
        if disk not in attached_disks and disk != 'OVF_STORE': #Exclude disks attached to VM and system dusks with name 'OVF_STORE'
            unattached_disks.append(disk)
    #print(unattached_disks)
    for disk in iso_disks: #Exclude ISO disks
        unattached_disks.remove(disk)
    #print(unattached_disks) #Exclude template disks
    for disk in unattached_disks:
        if disk in template_disks:
            unattached_disks.remove(disk)

    disk_service = connection.system_service().disks_service()
    disks = disk_service.list()

    #make an array of unattched disks and save it into csv
    for disk in disks:
        disk_name = disk.name
        if disk.name in unattached_disks:
            disk_size = disk.provisioned_size / 1024 / 1024 /1024
            disk_size_gb = round(disk_size)
            sd_id = disk.storage_domains[0].id
            sds_service = connection.system_service().storage_domains_service()
            storage_domain = sds_service.storage_domain_service(sd_id).get()
            sd_name = storage_domain.name
            disk_param_array = [[olvm_service, sd_name, disk_name, disk_size_gb]]
            appendCSV(disk_param_array, diskinfo)

    return disk_param_array
    #print(unattached_disks)

#Function to create csv of ISO disks
def findIsoDisks(iso_disks, OLVM_SERVICE_NAME, connection, diskiso):
    disk_service = connection.system_service().disks_service()
    disks = disk_service.list()
    olvm_service = OLVM_SERVICE_NAME
    
    #make an array of ISO disks and save it into csv
    for disk in disks:
        disk_name = disk.name
        if disk.name in iso_disks:
            disk_size = disk.provisioned_size / 1024 / 1024 /1024
            disk_size_gb = round(disk_size)
            sd_id = disk.storage_domains[0].id
            sds_service = connection.system_service().storage_domains_service()
            storage_domain = sds_service.storage_domain_service(sd_id).get()
            sd_name = storage_domain.name
            disk_iso_array = [[olvm_service, sd_name, disk_name, disk_size_gb]]
            appendCSV(disk_iso_array, diskiso)
            
    return disk_iso_array
    #print(unattached_disks)

def main():
    diskinfo = "../csv/diskinfo_olvm.csv" # place csv file with unattched disks into 'csv' folder
    diskiso = "../csv/diskiso_olvm.csv" # place csv file with ISO disks into 'csv' folder
    
    #Clean up csv files
    clearCSV(diskinfo)
    clearCSV(diskiso)
    CA_PATH = "../ca/" #File with KVM cert in 'ca' folder

    for OLVM_URL in OLVM_URLs: #Loop throuth KVM URLs array
        OLVM_SERVICE_NAME = OLVM_URL[+8:-17] #remove first 8 and last 17 symbols from KVM URL
        OVIRT_CA=CA_PATH + "ca-" + OLVM_SERVICE_NAME + ".pem"
        #print(OLVM_NAME)
        check_ca = getStatusCA(OVIRT_CA)
        check_ca = str(check_ca)
        if check_ca == "True":
            connection = olvm_connect(OLVM_URL, OVIRT_CA)
            attached_disks = attachedDisks(connection)
            template_disks = templateDisks(connection)
            all_disks = allDisks(connection)
            iso_disks = isoDisks(connection)
            findIsoDisks(iso_disks, OLVM_SERVICE_NAME, connection, diskiso)
            findUnattachedDisks(attached_disks, all_disks, template_disks, iso_disks, OLVM_SERVICE_NAME, connection, diskinfo)
    connection.close()
   

if __name__ == '__main__':
    main()
