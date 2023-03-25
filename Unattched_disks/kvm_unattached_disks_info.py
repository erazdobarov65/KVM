
# Script to find unattched disks in KVM 

from curses.ascii import DC3
import logging, dns.resolver
import ovirtsdk4 as sdk
import ovirtsdk4.types as types
import re, sys, base64, requests, getopt, socket, csv, os
from os.path import exists


# Задаем параметры подключения
OLVM_USER = "roadmin@internal" #Read-only admin
OLVM_PASS = "OL2021&^vmpaSS-4"
OLVM_URLs = ["https://bs-olvm.ftc.ru/ovirt-engine/api"]

#Выключаем варнинги при проверке url без серта
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

#Проверяем доступность oVirt
def getStatuscode(url,user,passw):
    try:
        r = requests.head(url,verify=False,timeout=5,auth = (user, passw))
        return (r.status_code)
    except:
        return -1

# Функция соединения с OLVM
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

    #Проверяем еть ли такой серт
def getStatusCA(ca_file):
    file_exists = exists(ca_file)
    return file_exists


#Очищаем csv
def clearCSV(cloneinfo):
    filename = cloneinfo
    f = open(filename, "w+")
    f.close()


#Добавляем записи в csv
def appendCSV(title, cloneinfo):
    with open(cloneinfo, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerows(title)


def attachedDisks(connection):
    # Get all disks in datacenter
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

def templateDisks(connection):
    # Get all disks in datacenter
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

def findUnattachedDisks(attached_disks, all_disks, template_disks, iso_disks, OLVM_SERVICE_NAME, connection, diskinfo):
    unattached_disks = []
    olvm_service = OLVM_SERVICE_NAME
    for disk in all_disks:
        if disk not in attached_disks and disk != 'OVF_STORE':
            unattached_disks.append(disk)
    #print(unattached_disks)
    for disk in iso_disks:
        unattached_disks.remove(disk)
    #print(unattached_disks)
    for disk in unattached_disks:
        if disk in template_disks:
            unattached_disks.remove(disk)

    disk_service = connection.system_service().disks_service()
    disks = disk_service.list()

    # Формируем массив из неприатаченных дисков
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
    
def findIsoDisks(iso_disks, OLVM_SERVICE_NAME, connection, diskiso):

    disk_service = connection.system_service().disks_service()
    disks = disk_service.list()
    olvm_service = OLVM_SERVICE_NAME

    # Формируем массив из неприатаченных дисков
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
    #cloneinfo = "/var/lib/rundeck/projects/Hostinfo/etc/data_vm_olvm/cloneinfo.csv"
    diskinfo = "/u/ckdba/unix_service/Infotask/check_unattached_vm_disk/csv/diskinfo_olvm.csv"
    diskiso = "/u/ckdba/unix_service/Infotask/check_unattached_vm_disk/csv/diskiso_olvm.csv"
    #Очищаем CSV
    clearCSV(diskinfo)
    clearCSV(diskiso)
    #arg_olvm = checkOpts(sys.argv[1:]) # Проверяем заданы ли  аргумент OLVM при запуске скрипта
    #CA_PATH = "../ca/" #Ресурс-файл со всеми активными хостами на локальном компе
    CA_PATH = "/u/ckdba/vm_infra/OLVM/ca/" #Ресурс-файл со всеми активными хостами в Rundeck
    #VIRT_NAME = 'kvm'

   
    for OLVM_URL in OLVM_URLs: #Перебираем адреса OLVM из массива
        OLVM_SERVICE_NAME = OLVM_URL[+8:-17] #удаляем первые 8 символов и последние 17
        OVIRT_CA=CA_PATH + "ca-" + OLVM_SERVICE_NAME + ".pem"
        #print(OLVM_NAME)
        check_ca = getStatusCA(OVIRT_CA)
        check_ca = str(check_ca)
        #global connection
        if check_ca == "True":
            connection = olvm_connect(OLVM_URL, OVIRT_CA)
            #datacenter_service = connection.system_service().data_centers_service()
            #dcs = datacenter_service.list()
            #sds_service = connection.system_service().storage_domains_service()
            #sds = sds_service.list()
            #vms_service = connection.system_service().vms_service()
            #vms = vms_service.list()
            #for sd in sds:
            #   sd_service = sds_service.sd_service(sd.id)
            #   diskInfo(connection, sd_service)
            attached_disks = attachedDisks(connection)
            template_disks = templateDisks(connection)
            all_disks = allDisks(connection)
            iso_disks = isoDisks(connection)
            findIsoDisks(iso_disks, OLVM_SERVICE_NAME, connection, diskiso)
            findUnattachedDisks(attached_disks, all_disks, template_disks, iso_disks, OLVM_SERVICE_NAME, connection, diskinfo)
            #appendCSV(disk_param_array, diskinfo) 
                
        
    connection.close()
   

if __name__ == '__main__':
    main()
