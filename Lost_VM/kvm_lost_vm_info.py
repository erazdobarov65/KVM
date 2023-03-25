#Script lloks for VMs that do not resolve into DNS


import logging, dns.resolver
import ovirtsdk4 as sdk
import ovirtsdk4.types as types
import re, sys, base64, requests, getopt, socket, csv, os
from os.path import exists


#Enter connection details
OLVM_USER = "roadmin@internal" #Read-only admin
OLVM_PASS = "yourpassword"
OLVM_URLs = ["https://kvm-address/ovirt-engine/api"] #array with  kvm URL. In this example there is just single address

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


#Function to get info about VM
def VmInfo(vm,connection):
    vms_service = connection.system_service().vms_service()
    vm_service = vms_service.vm_service(vm.id)

    # VM_name
    vm_cluster_id = vm.cluster.id
    vm_name = vm.name

    #Search for cluster name by its id
    clusters_service = connection.system_service().clusters_service()
    clusters = clusters_service.list()
    for cluster in clusters:
        if cluster.id == vm_cluster_id:
            vm_cluster_name = cluster.name

    #VM creation date
    vm_creation_date = vm_service.get().creation_time.strftime("%Y-%m-%d %H:%M")

    #VM_summ_disks_size
    disk_attachments_service = vm_service.disk_attachments_service()
    vm_disk_summ = 0
    disk_attachments = disk_attachments_service.list()
    for disk_attachment in disk_attachments:
        disk = connection.follow_link(disk_attachment.disk)
        vm_disk_by = disk.provisioned_size
        vm_disk_gb = vm_disk_by / 1024 / 1024 /1024
        vm_disk_gb_round = (round (vm_disk_gb))
        vm_disk_summ = vm_disk_summ + vm_disk_gb_round
    #make an array with VM information
    vm_param_array = [[vm_cluster_name, vm_name, vm_creation_date, vm_disk_summ]]
    return vm_param_array

#Function to resolve VM into DNS by its name
def DNSresolve(vm_name):
    vm_name = vm_name
    resolver = dns.resolver.Resolver()
    resolver.nameservers = ['192.168.92.20']
    try:
        resolver.query(vm_name, "A")
    except dns.exception.DNSException:
        dns_resolv_status = "error"
        dns_resolv_status = str(dns_resolv_status)
                    #print(dns_resolv_status)
    else:
        dns_resolv_status = "ok"
    return dns_resolv_status

def main():
    csvinfo = "../csv/csvinfokvm.csv" # place csv file into csv folder
    #clean up csv file
    clearCSV(csvinfo)
    CA_PATH = "../ca/" #File with KVM cert
   
    for OLVM_URL in OLVM_URLs: #Loop throuth KVM URLs array
        OLVM_NAME = OLVM_URL[+8:-17] #remove first 8 and last 17 symbols from KVM URL
        OVIRT_CA=CA_PATH + "ca-" + OLVM_NAME + ".pem"
        #print(OLVM_NAME)
        check_ca = getStatusCA(OVIRT_CA)
        check_ca = str(check_ca)
        #make global connection to KVM
        if check_ca == "True":
            connection = olvm_connect(OLVM_URL, OVIRT_CA)
            vms_service = connection.system_service().vms_service()
            vms = vms_service.list()
            for vm in vms:
                vm_name = vm.name
                #resole VM in DNS
                dns_resolv_state = DNSresolve(vm_name)
                #if VM is not resolved, collect its data and save into csv
                if dns_resolv_state == "error":
                    vm_param_array = VmInfo(vm,connection)
                    appendCSV(vm_param_array, csvinfo)  
        
    connection.close()
   

if __name__ == '__main__':
    main()
