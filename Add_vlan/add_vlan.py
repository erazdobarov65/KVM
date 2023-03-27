import ovirtsdk4 as sdk
import ovirtsdk4.types as types
import base64, requests, csv
from colorama import Fore, Style, init
from os.path import exists


#Enter connection details
OVIRT_USER = "admin@internal"
OVIRT_PASS = "yourpassword"

#Warning turn of when connecting without cert
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

#Check if KVM server is reachable
def getStatuscode(url,user,passw):
    try:
        r = requests.head(url,verify=False,timeout=5,auth = (user, passw))
        return (r.status_code)
    except:
        return -1

#Function to connect with KVM
def olvm_connect(OLVM_URL, OVIRT_CA, OVIRT_USER, OVIRT_PASS):
    connection = sdk.Connection(
        url=OLVM_URL,
        username=OVIRT_USER,
        password=OVIRT_PASS,
        ca_file=OVIRT_CA,
        # debug=True,
        # log=logging.getLogger(),
        insecure=True,
    )
    return connection

#Function to check certs file availability
def getStatusCA(ca_file):
    file_exists = exists(ca_file)
    return file_exists

#Function to select KVM server
def selectOLVMurl(OVIRT_DICT):
    name_str = []
    for k,v in OVIRT_DICT.items():
        name_str.append(k)
        print(f"{Fore.CYAN}{k}) {Style.RESET_ALL}{v}")
    #Select required KVM 
    name_index = input(f"Select option {str(name_str)} > ")
    OLVM_NAME = ''
    for k,v in OVIRT_DICT.items():
        if name_index == k:
            OLVM_NAME = v
    #Return selected KVM
    return OLVM_NAME

#Funtion to select Datacenter within KVM server
def select_dc(dcs_service):
    dcs = dcs_service.list()
    dc_arr = []
    dc_num = 0
    for dc in dcs:
        dc_num += 1
        dc_arr.append(dc.name)
        print(f"{dc_num}: {dc.name}")
    dc_index = input(f"Select DC number > ")
    dc_true_index = int(dc_index) - 1
    DC_NAME = dc_arr[dc_true_index]
    #print(DC_NAME)
    return DC_NAME

#Function to add VLAN
def add_vlan(nws_service, dc_sel):
    #Open vlan.csv file to read
    with open('vlan.csv', 'r') as csv_file:
        reader = csv.reader(csv_file)
        #Loop through each line in csv file
        for row in reader:
            try:
                #if VLAN field in csv is empty
                if row[3] == 'none':
                    nws_service.add(
                        network=types.Network(
                            name=row[0],
                            description=row[2],
                            comment=row[1],
                            data_center=types.DataCenter(
                                name=dc_sel
                            ),
                            #vlan=types.Vlan(id=row[3]),
                            usages=[types.NetworkUsage.VM],
                            mtu=1500,
                        ),
                    )
                #if VLAN field in csv has a value
                else:
                    nws_service.add(
                        network=types.Network(
                            name=row[0],
                            description=row[2],
                            comment=row[1],
                            data_center=types.DataCenter(
                                name=dc_sel
                            ),
                            vlan=types.Vlan(id=row[3]),
                            usages=[types.NetworkUsage.VM],
                            mtu=1500,
                        ),
                    )
            #handle exception if VLAN already exists
            except sdk.Error:
                print(f"Network {row[0]} already exists!")
            else:
                pass
    csv_file.close
    

def main():
    #Dictionary with KVM servers. 
    OVIRT_DICT = {"1" : "kvm-name1.xxx.xx",
                  "2" : "kvm-name2.xxx.xx"
                  }
    CA_PATH = "../ca/" #File with KVM server CA cert
    #Select required KVM server
    OLVM_NAME = selectOLVMurl(OVIRT_DICT) 
    print(f"Was selected: {Fore.CYAN}{OLVM_NAME}{Style.RESET_ALL}")
    OLVM_URL = "https://" + OLVM_NAME + "/ovirt-engine/api"
    OVIRT_CA=CA_PATH + "ca-" + OLVM_NAME + ".pem" #CA file name format: 'ca-kvm-server-name.xxx.xx.pem'
    check_ca = getStatusCA(OVIRT_CA)
    check_ca = str(check_ca)
    if check_ca == "True":
        if olvm_connect(OLVM_URL,OVIRT_CA,OVIRT_USER,OVIRT_PASS).test:
            connection = olvm_connect(OLVM_URL, OVIRT_CA, OVIRT_USER, OVIRT_PASS)
    dcs_service = connection.system_service().data_centers_service()
    nws_service = connection.system_service().networks_service()
    dc_sel = select_dc(dcs_service)
    print(dc_sel)
    add_vlan(nws_service, dc_sel)

    connection.close()

   
if __name__ == '__main__':
    main()
