import ovirtsdk4 as sdk
import ovirtsdk4.types as types
import requests, csv, time, sys
from os.path import exists


# set connection details
OLVM_USER = "admin@internal" #Local admin account
OLVM_PASS = "yourpassword"
OLVM_URLs = ["https://ovirt_url.xxx.xx/ovirt-engine/api"]

#Turn off warnings when checking URL without cert
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

#Check access to ovirt
def getStatuscode(url,user,passw):
    try:
        r = requests.head(url,verify=False,timeout=5,auth = (user, passw))
        return (r.status_code)
    except:
        return -1

#Function to connetc to ovirt server
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

#cert check
def getStatusCA(ca_file):
    file_exists = exists(ca_file)
    return file_exists

#Function to check disks domains after move
def check_disks(sd_orig_name, disk, connection):
    sd_new_id = disk.storage_domains[0].id
    sds_service = connection.system_service().storage_domains_service()
    storage_domain = sds_service.storage_domain_service(sd_new_id).get()
    sd_new_name = storage_domain.name
   
    if sd_new_name != sd_orig_name:
        print(f"Диск {disk.name} был перемещен из {sd_orig_name} в {sd_new_name}")
    else:
        print(f"Диск {disk.name} не был перемещен")


#Function for moving disks to another domain
def move_disks(disk_domain, disk, connection):

    sds_service = connection.system_service().storage_domains_service()
    sd_new_id = sds_service.storage_domain_service(disk_domain).get()
    try:
        disk_service = connection.system_service().disks_service().disk_service(disk.id)
        disk_service.move(storage_domain=sd_new_id)
        while True:
            print(f"Waiting for the {disk.name} movement to complete ...")
            time.sleep(10)
            disk = disk_service.get()
            if disk.status == types.DiskStatus.OK:
                break
    except sdk.Error: 
        print(f"Диск {disk.name} уже находится в нужном хранилище")
 
def main():
    CA_PATH = "../ca/" #path to certs
    #Create list with disk names as command-line arguments
    arg_list = []
    for idx, arg in enumerate(sys.argv[1:]):
        arg_list.append(arg)
    #print(arg_list)
  
    #Create dictionary with disk names and target disk domains 
    disks_list = {}

    #read csv file and add disk name and target domain int dictionary
    with open('disks.csv', 'r') as csv_file:
        reader = csv.reader(csv_file)
        #Loop through each line in csv file
        for row in reader:
            if row[0] in arg_list:
                disks_list[row[0]] = row[2]
    #print(disks_list)      
 
    for OLVM_URL in OLVM_URLs: #Loop through all oVirt/OLVM servers 
        OLVM_NAME = OLVM_URL[+8:-17] #remove first 8 and and last 17 symbols
        OVIRT_CA=CA_PATH + "ca-" + OLVM_NAME + ".pem"
        check_ca = getStatusCA(OVIRT_CA)
        check_ca = str(check_ca)
        #global connection
        if check_ca == "True":
            connection = olvm_connect(OLVM_URL, OVIRT_CA)
            disk_service = connection.system_service().disks_service()
            disks = disk_service.list()
            #dictionary to store disk name and original data domain
            disks_orig = {}
            #Find original data domains adn add to disks_orig dictionary
            for disk in disks:
                #print(disk.name)
                disk_name = disk.name
                if disk_name in disks_list:
                    sd_orig_id = disk.storage_domains[0].id
                    sds_service = connection.system_service().storage_domains_service()
                    storage_domain = sds_service.storage_domain_service(sd_orig_id).get()
                    sd_orig_name = storage_domain.name
                    disks_orig[disk_name] = sd_orig_name
            #check if disk is disks_list and move these disks to target domain
            for disk in disks:
                #print(disk.name)
                disk_name = disk.name
                if disk_name in disks_list:
                    for k,v in disks_list.items():
                        if k == disk_name:
                            disk_domain = v
                            move_disks(disk_domain, disk, connection)
            #close connection to oVirt server
            connection.close()
      
        if check_ca == "True":
            #create new connection to oVirt server
            connection = olvm_connect(OLVM_URL, OVIRT_CA)
            disk_service = connection.system_service().disks_service()
            disks = disk_service.list()
            #Create final report that includes disk name, original and new domains
            for disk in disks:
                disk_name = disk.name
                if disk_name in disks_list:
                    for k,v in disks_orig.items():
                        if k == disk_name:
                            sd_orig_name = v
                            check_disks(sd_orig_name, disk, connection)
    connection.close() 

   

if __name__ == '__main__':
    main()
