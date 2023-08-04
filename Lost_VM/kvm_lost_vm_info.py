#Script lloks for VMs that do not resolve into DNS


import logging, dns.resolver
import ovirtsdk4 as sdk
import ovirtsdk4.types as types
import re, sys, base64, requests, getopt, socket, csv, os, paramiko, warnings
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
    #virt_name = VIRT_NAME
    vm_name = vm.name

    #Search for cluster name by its id 
    clusters_service = connection.system_service().clusters_service()
    clusters = clusters_service.list()
    for cluster in clusters:
        if cluster.id == vm_cluster_id:
            vm_cluster_name = cluster.name

    #VM creation date
    vm_creation_date = get_vm_time(vm_name)
    vm_creation_date = vm_creation_date[:16]

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
    # print ("Summary disk size   : {} GB" . format(vm_disk_summ))

   
    vm_param_array = [[vm_cluster_name, vm_name, vm_creation_date, vm_disk_summ]]
    return vm_param_array

#Function to resolve in DNS by VM name
def DNSresolve(vm_name):
    vm_name = vm_name
    try:
        socket.gethostbyname(vm_name)
    except socket.gaierror:
        dns_resolv_status = "error"
        dns_resolv_status = str(dns_resolv_status)
    else:
        dns_resolv_status = "ok"
    return dns_resolv_status

#Function to extract VM creation time form PostgreSQL database on ovirt-engine host
def get_vm_time(vm_name):
    host = 'ovirt-engine' #Enter yout oVirt engine name here
    user = 'ovirt-user' #username used to connect to postgreSQL DB on ovirt-engine
    pubkey = '/home/ovirt-user/.ssh/ovirt-user'
    #command to execute on ovirt-engine host
    command = f'sudo su postgres -c "psql -d engine -c \\"select _create_date from vm_static where vm_name=\'{vm_name}\'\\" " 2>/dev/null | sed -n 3p'
    try: #Trying to connect via ssh to ovirt-engine
        sshcon = paramiko.SSHClient()  # will create the object
        sshcon.set_missing_host_key_policy(paramiko.AutoAddPolicy())# no known_hosts error
        sshcon.connect(hostname=host, username=user, key_filename=pubkey, timeout=10) # no passwd needed
        #Extract VM creation time from DB
        stdin, stdout, stderr = sshcon.exec_command(command)
        vm_time = stdout.read().decode('utf-8').strip()
    except BlockingIOError:
        vm_time = "NO_DATA"
    except paramiko.ssh_exception.NoValidConnectionsError:
        vm_time = "NO_DATA"
    except paramiko.ssh_exception.socket.error:
        vm_time = "NO_DATA"
    except paramiko.ssh_exception.AuthenticationException:
        vm_time = "NO_DATA"
    except paramiko.ssh_exception.SSHException:
        vm_time = "NO_DATA"

    #print(vm_time)
    return vm_time

def main():
    # Store csv file with VM data inside /tmp directory
    cloneinfodir = "/tmp/data_vm_backup/"
    cloneinfocsv = cloneinfodir + "cloneinfokvm.csv"
    #Create /tmp/data_vm_backup if does not exist
    if not os.path.exists(cloneinfodir):
        os.mkdir(cloneinfodir)

    if os.path.exists(cloneinfocsv):
        # clean old csv file
        clearCSV(cloneinfocsv)

    # Store your CA cert inside ca directory
    CA_PATH = "../ca"
   
    for OLVM_URL in OLVM_URLs: #Loop through all oVirt/OLVM engines
        OLVM_NAME = OLVM_URL[+8:-17] #strip first 8 and last 17 symbols
        OVIRT_CA=CA_PATH + "ckca.cer"
        #print(OLVM_NAME)
        check_ca = getStatusCA(OVIRT_CA)
        check_ca = str(check_ca)
        #Setup global connection to oVirt engine
        if check_ca == "True":
            connection = olvm_connect(OLVM_URL, OVIRT_CA)
            vms_service = connection.system_service().vms_service()
            vms = vms_service.list()
            for vm in vms:
                vm_name = vm.name
                vm_status = vm.status
                vm_status = str(vm_status)
                if vm_status == "down":
                    dns_resolv_state = DNSresolve(vm_name)
                    if dns_resolv_state == "error":
                        vm_param_array = VmInfo(vm,connection)
                        appendCSV(vm_param_array, cloneinfocsv)  
                #clone_info(vms_service, dcs_service)
        
    connection.close()
   

if __name__ == '__main__':
    main()
