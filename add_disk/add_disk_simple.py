##############################################################################################################################################
# Скрипт для массового добавления дисков к выбранной включенной ВМ и в выбранный домен хранения
# Запускается из командной строки без аргументов.
# Работает в интерактивном режиме
# !!!Внимание!!!
# Перед использованием скрипта задайте свои значения переменных:
# OVIRT_USER -  пользователь ovirt с админскими правами (на создание ВМ)
# OVIRT_PASS - пароль пользователя
# OVIRT_URL -  адрес API ovirt-engine в виде "https://<hosted-engine>/ovirt-engine/api" где <hosted-engine> - FQDN менеджера виртуализации



#import logging
import ovirtsdk4 as sdk
import ovirtsdk4.types as types
#import re, sys, base64, getopt, socket, csv, os, 
import time, requests
#from colorama import Fore, Back, Style, init
#from os.path import exists
from datetime import datetime


# Задаем параметры подключения

OVIRT_USER = "evgeny@internal" #admin
OVIRT_PASS = ""
OVIRT_URL = "https://engine.redvirt.tst/ovirt-engine/api"

#Выключаем варнинги при проверке url без серта
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


# Функция соединения с Ovirt
def ovirt_connect(OVIRT_URL):
    connection = sdk.Connection(
        url=OVIRT_URL,
        username=OVIRT_USER,
        password=OVIRT_PASS,
        #ca_file=OVIRT_CA,
        # debug=True,
        # log=logging.getLogger(),
        insecure=True,
    )
    return connection


#Функция выбора ВМ
def SelectVM(connection):
    vms_service = connection.system_service().vms_service()
    vms = vms_service.list()

    vm_arr = []
    vm_num = 0
    while True:
        for vm in vms:
            vm_status = vm.status
            vm_status = str(vm_status)
            if vm_status == "up":
                vm_num += 1
                vm_arr.append(vm.name)
                print(f"{vm_num}: {vm.name}") 
        vm_index = input(f"Введите номер ВМ (все ВМ запущены) > ")
        try:
            vm_index = int(vm_index) - 1
        except ValueError:
            print(f"Введен неправильный номер ВМ, повторите снова")
            vm_num = 0
        try:
            VM_NAME = vm_arr[vm_index]
            print(VM_NAME)
            return VM_NAME
            break
        except IndexError:
            print(f"Введен неправильный номер ,ВМ повторите снова")
            vm_num = 0
        except TypeError:
            print(f"Введен неправильный номер ВМ, повторите снова")
            vm_num = 0

#Функция выбора сторадж домена
def SelectDomain(connection):
    sds_service = connection.system_service().storage_domains_service()
    sds = sds_service.list()

    sd_arr = []
    sd_num = 0
    while True:
        for sd in sds:
            sd_type = sd.type
            sd_type = str(sd_type)
            if sd_type  == "data":
                sd_num += 1
                sd_arr.append(sd.name)
                size_avail = round(sd.available / 1024 /1024 /1024)
                size_full = round((sd.committed + sd.available)  / 1024 /1024 /1024)
                print(f"{sd_num}: {sd.name}, полный объем домена {size_full} ГБ, доступный объем {size_avail} ГБ")
        sd_index = input(f"Введите номер домена > ")
        try:
            sd_index = int(sd_index) - 1
        except ValueError:
            print(f"Введен неправильный номер домена, повторите снова")
            sd_num = 0
        try:
            SD_NAME = sd_arr[sd_index]
            print(SD_NAME)
            return SD_NAME
            break
        except IndexError:
            print(f"Введен неправильный номер домена, повторите снова")
            sd_num = 0
        except TypeError:
            print(f"Введен неправильный номер домена, повторите снова")
            sd_num = 0

#Функция добавления диска к ВМ
def AddDisk(connection, VM_NAME, DISK_NAME, DISK_DESCRIPTION, DISK_SIZE, SD_NAME):
    vms_service = connection.system_service().vms_service()
    vms = vms_service.list()

    for vm in vms:
        if vm.name == VM_NAME:
            disk_attachments_service = vms_service.vm_service(vm.id).disk_attachments_service()

            disk_attachment = disk_attachments_service.add(
                types.DiskAttachment(
                    disk=types.Disk(
                        name=DISK_NAME,
                        description=DISK_DESCRIPTION,
                        format=types.DiskFormat.COW,
                        provisioned_size=DISK_SIZE,
                        storage_domains=[
                            types.StorageDomain(
                                name=SD_NAME,
                            ),
                        ],
                    ),
                    interface=types.DiskInterface.VIRTIO,
                    bootable=False,
                    active=True,
                ),
            )
            # Ждем пока диск разлочится:
            print (f"INFO: Ждем создания диска ВМ {DISK_NAME}")
            disks_service = connection.system_service().disks_service()
            disk_service = disks_service.disk_service(disk_attachment.disk.id)
            while True:
                time.sleep(5)
                disk = disk_service.get()
                if disk.status == types.DiskStatus.OK:
                    break

def main():

    #CA_PATH = "ca/" #Ресурс-файл со всеми активными хостами на локальном компе
    #MEMORY_VM = 1 * 1024 *1024 *1024
    #VCPU_VM = 1 
   
    #OVIRT_SERVICE_NAME = OVIRT_URL[+8:-17] #удаляем первые 8 символов и последние 17
    #OVIRT_CA = CA_PATH + "ca.cer"
    #check_ca = getStatusCA(OVIRT_CA)
    #check_ca = str(check_ca)
    #global connection
    #if check_ca == "True":
    connection = ovirt_connect(OVIRT_URL)
    VM_NAME = SelectVM(connection)
    SD_NAME = SelectDomain(connection)
    today = datetime.today().date()
    while True:
        DISK_SIZE = input(f"Введите требуемый размер диска (ГБ) >")
        try:
            DISK_SIZE = int(DISK_SIZE) * 2**30
        except ValueError:
            print(f"Введите требуемый размер диска еще раз")
        else:
            break
    #print(DISK_SIZE)
    while True:
        DISK_NUM = input(f"Введите требуемое количество дисков >")
        try:
            DISK_NUM = int(DISK_NUM) + 1
        except ValueError:
            print(f"Введите требуемое количество дисков еще раз")
        else:
            break
    for i in range(1, DISK_NUM):
        DISK_NAME = VM_NAME + '-disk-' + str(i)
        DISK_DESCRIPTION = DISK_NAME + '_' + str(today)
        #print(DISK_NAME)
        AddDisk(connection, VM_NAME, DISK_NAME, DISK_DESCRIPTION, DISK_SIZE, SD_NAME)

    connection.close()
   

if __name__ == '__main__':
    main()