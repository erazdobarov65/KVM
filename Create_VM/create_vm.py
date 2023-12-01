##############################################################################################################################################
# Скрипт для массового добавления Виртуальных машин в выбранный кластер
# Запускается из командной строки без аргументов.
# Работает в интерактивном режиме
# !!!Внимание!!!
# Перед использованием скрипта задайте свои значения переменных:
# OVIRT_USER -  пользователь ovirt с админскими правами (на создание ВМ)
# OVIRT_PASS - пароль пользователя
# OVIRT_URL -  адрес API ovirt-engine в виде "https://<hosted-engine>/ovirt-engine/api" где <hosted-engine> - FQDN менеджера виртуализации
# MEMORY_VM - Объем памяти ВМ в виде "<ГБ> * 1024 *1024 *1024". Геде ГБ - объем в ГБ
# VCPU_VM - Количество виртуальных CPU


#import logging
import ovirtsdk4 as sdk
import ovirtsdk4.types as types
#import re, sys, base64, getopt, socket, csv, os, 
import time, requests
from colorama import Fore, Back, Style, init
#from os.path import exists


# Задаем параметры подключения

OVIRT_USER = "evgeny@internal" #admin
OVIRT_PASS = "@ASDqwe123"
OVIRT_URL = "https://engine.redvirt.tst/ovirt-engine/api"

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


#Функция выбора кластера, в котором будет создана ВМ
def SelectCluster(connection):
    clusters_service = connection.system_service().clusters_service()
    clusters = clusters_service.list()

    cluster_arr = []
    cluster_num = 0
    while True:
        for cluster in clusters:
            cluster_num += 1
            cluster_arr.append(cluster.id)
            print(f"{cluster_num}: {cluster.name}") 
        cluster_index = input(f"Введите номер кластера > ")
        try:
            cluster_index = int(cluster_index) - 1
        except ValueError:
            print(f"Введен неправильный номер кластера, повторите снова")
            cluster_num = 0
        try:
            CLUSTER_ID = cluster_arr[cluster_index]
            print(CLUSTER_ID)
            return CLUSTER_ID
            break
        except IndexError:
            print(f"Введен неправильный номер кластера, повторите снова")
            cluster_num = 0
        except TypeError:
            print(f"Введен неправильный номер кластера, повторите снова")
            cluster_num = 0


#Функция выбора шаблона на базе которого будет создана ВМ
def SelectTemplate(connection, CLUSTER_ID):
    templates_service = connection.system_service().templates_service()
    tms = templates_service.list()
    
    tms_arr = []
    tms_num = 0
    while True:
        for tm in tms:
            try:
                if tm.cluster.id == CLUSTER_ID:
                    tms_num += 1
                    tms_arr.append(tm.id)
                    print(f"{tms_num}: {tm.name}")
            except AttributeError:
                pass
        tmpl_index = input(f"Введите номер шаблона > ")
        try:
            tmpl_index = int(tmpl_index) - 1
        except ValueError:
            print(f"Введен неправильный номер шаблона, повторите снова")
            tms_num = 0
        try:
            TMPL_ID = tms_arr[tmpl_index]
            print(TMPL_ID)
            return TMPL_ID
            break
        except IndexError:
            print(f"Введен неправильный номер шаблона, повторите снова")
            tms_num = 0
        except TypeError:
            print(f"Введен неправильный номер шаблона, повторите снова")
            tms_num = 0

#Функция создания новой ВМ
def CreateVM(connection,NEW_VM_NAME,MEMORY_VM,CLUSTER_ID,TMPL_ID,VCPU_VM):
    vms_service = connection.system_service().vms_service()
    vms = vms_service.list()
    print (Fore.CYAN + "INFO: " + Style.RESET_ALL + "Создается новая ВМ: " + Fore.CYAN + "{}". format(NEW_VM_NAME) + Style.RESET_ALL)
    vms_service.add(
        types.Vm(
            name=NEW_VM_NAME,
            memory=MEMORY_VM,
            cluster=types.Cluster(id=CLUSTER_ID),
            template=types.Template(id=TMPL_ID),
            memory_policy=types.MemoryPolicy(
                guaranteed=MEMORY_VM,
                max=MEMORY_VM,
            ),
            cpu=types.Cpu(
                topology=types.CpuTopology(
                    sockets=1,
                    cores=VCPU_VM,
                    threads=1
                )
            ),
            os=types.OperatingSystem(
                boot=types.Boot(
                    devices=[types.BootDevice.HD]
                )
            )
        ),
        clone=False #диски тонкие.
    )


#Функция для проверки создалаось ли ВМ
def CheckVMAvailable(connection, NEW_VM_NAME):
    check_vm = 0 # Проверка есть ли уже ВМ с таким именем
    vms_service = connection.system_service().vms_service()
    vms = vms_service.list()
    for vm in vms:
        vm_name = vm.name
        if vm_name == NEW_VM_NAME:
            check_vm = 1
        
    if check_vm == 1:
        print (Fore.GREEN + "SUCCESS: " + Style.RESET_ALL + "Виртуальная машина " + Fore.CYAN + "{}". format(NEW_VM_NAME) + Style.RESET_ALL + " создана")
    else:
        print (Fore.RED + "ERROR: " + Style.RESET_ALL + "Виртуальная машина " + Fore.CYAN + "{}". format(NEW_VM_NAME) + Style.RESET_ALL + " НЕ создана.")
        print ("Что-то пошло не так. Проверьте состояние ВМ в консоле.")
        print ("")
        sys.exit(2)


# Функция для проверки статуса вДиска
def CheckVMdisk(connection,NEW_VM_NAME):
    vms_service = connection.system_service().vms_service()
    vms = vms_service.list()
    for vm in vms:
        vm_name = vm.name
        if vm_name == NEW_VM_NAME:

            #Определяем id вДисков, подключенных к ВМ
            disk_attachments_service = vms_service.vm_service(vm.id).disk_attachments_service()
            disk_attachments = disk_attachments_service.list()
            for disk_attachment in disk_attachments:
                disks_service = connection.system_service().disks_service()
                disk_service = disks_service.disk_service(disk_attachment.disk.id)
                while True:
                    time.sleep(1)
                    disk = disk_service.get()
                    if disk.status == types.DiskStatus.OK:
                        break 


#Функция включения ВМ
def StartVM(connection,NEW_VM_NAME):
    vms_service = connection.system_service().vms_service()
    vm = vms_service.list(search='name=' + NEW_VM_NAME)[0]
    vm_service = vms_service.vm_service(vm.id)
    vm_service.start()


#Функция проверяет запустилась ли ВМ
def CheckVM(connection,NEW_VM_NAME):
    vms_service = connection.system_service().vms_service()
    vm = vms_service.list(search='name=' + NEW_VM_NAME)[0]
    vm_service = vms_service.vm_service(vm.id)
    while True:
        time.sleep(1)
        vm = vm_service.get()
        if vm.status == types.VmStatus.UP:
            break


def RenameDisks(connection,NEW_VM_NAME):
    vms_service = connection.system_service().vms_service()
    vms = vms_service.list()
    for vm in vms:
        vm_name = vm.name
        if vm_name == NEW_VM_NAME:
            disk_attachments_service = vms_service.vm_service(vm.id).disk_attachments_service()

            #Переименовываем диски
            disk_id = 1
            disk_attachments = disk_attachments_service.list()
            for disk_attachment in disk_attachments:
                #disk = connection.follow_link(disk_attachment.disk)
                #vm_disk_by = disk.provisioned_size
                #vm_disk_gb = vm_disk_by / 1024 / 1024 /1024
                #vm_disk_gb_round = (round (vm_disk_gb))
                #vm_alias = disk.alias
                
                #Переименовываем системный диск
                disk_attachment_service = disk_attachments_service.attachment_service(disk_attachment.id)
                disk_attachment_service.update(
                    types.DiskAttachment(
                        disk=types.Disk(
                            name=NEW_VM_NAME + '_' + str(disk_id),
                        ),
                    ),
                )
                disk_id += 1


def main():

    #CA_PATH = "ca/" #Ресурс-файл со всеми активными хостами на локальном компе
    MEMORY_VM = 1 * 1024 *1024 *1024
    VCPU_VM = 1 
   
    #OVIRT_SERVICE_NAME = OVIRT_URL[+8:-17] #удаляем первые 8 символов и последние 17
    #OVIRT_CA = CA_PATH + "ca.cer"
    #check_ca = getStatusCA(OVIRT_CA)
    #check_ca = str(check_ca)
    #global connection
    #if check_ca == "True":
    connection = ovirt_connect(OVIRT_URL)
    CLUSTER_ID = SelectCluster(connection)
    TMPL_ID = SelectTemplate(connection, CLUSTER_ID)
    while True:
        VM_NUM = input(f"Введите требуемое количество ВМ >")
        try:
            VM_NUM = int(VM_NUM) + 1
        except ValueError:
            print(f"Введите требуемое количество ВМ еще раз")
        else:
            break
    for i in range(1, VM_NUM):
        NEW_VM_NAME = 'test-vm-'+str(i)
        #print(NEW_VM_NAME)
        
        # Создаем новую ВМ
        CreateVM(connection,NEW_VM_NAME,MEMORY_VM,CLUSTER_ID,TMPL_ID,VCPU_VM)
        time.sleep(2) # Sleep for 2 seconds

        #Проверяем создалась ли ВМ
        CheckVMAvailable(connection,NEW_VM_NAME)

        # Проверяем создались ли вДиски
        print (Fore.CYAN + "INFO: " + Style.RESET_ALL + "Ждем создания диска ВМ " + Fore.CYAN + "{}". format(NEW_VM_NAME) + Style.RESET_ALL)
        CheckVMdisk(connection, NEW_VM_NAME)
        
        #Переименовываем вДиски
        RenameDisks(connection, NEW_VM_NAME)

        

    START_VM = input(f"Запустить созданные ВМ? (y/n) >")
    if START_VM == 'y':
        #Включаем ВМ
        for i in range(1, VM_NUM):
            NEW_VM_NAME = 'test-vm-'+str(i)
            # Проверяем состояние вДиска
            print (Fore.CYAN + "INFO: " + Style.RESET_ALL + "Ждем разблокирования диска ВМ " + Fore.CYAN + "{}". format(NEW_VM_NAME))
            CheckVMdisk(connection, NEW_VM_NAME)
            StartVM(connection,NEW_VM_NAME)
            print (Fore.CYAN + "INFO: " + Style.RESET_ALL + "Ждем запуска ВМ " + Fore.CYAN + "{}". format(NEW_VM_NAME))
            #Ждем когда ВМ запустится
            CheckVM(connection,NEW_VM_NAME)
            time.sleep(5)
    elif START_VM == 'n':
        print(f"Созданные ВМ не будут запущены")
    else:
        exit()

    
    connection.close()
   

if __name__ == '__main__':
    main()