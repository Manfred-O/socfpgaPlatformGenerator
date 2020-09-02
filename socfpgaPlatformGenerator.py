#!/usr/bin/env python3
#
#            ########   ######     ##    ##  #######   ######  ########  #######                  
#            ##     ## ##    ##     ##  ##  ##     ## ##    ##    ##    ##     ##           
#            ##     ## ##            ####   ##     ## ##          ##    ##     ##        
#            ########   ######        ##    ##     ## ##          ##    ##     ##       
#            ##   ##         ##       ##    ##     ## ##          ##    ##     ##      
#            ##    ##  ##    ##       ##    ##     ## ##    ##    ##    ##     ##        
#            ##     ##  ######        ##     #######   ######     ##     #######         
#             ___          _   _      _     ___               _                 
#            | _ )  _  _  (_) | |  __| |   / __|  _  _   ___ | |_   ___   _ __  
#            | _ \ | || | | | | | / _` |   \__ \ | || | (_-< |  _| / -_) | '  \ 
#            |___/  \_,_| |_| |_| \__,_|   |___/  \_, | /__/  \__| \___| |_|_|_|
#                                                  |__/                              
#
#
# Robin Sebastian (https://github.com/robseb)
# Contact: git@robseb.de
# Repository: https://github.com/robseb/meta-intelfpga
#
# Python Script to automatically generate the u-boot loader 
# for Intel SoC-FPGAs 
 
# (2020-07-23) Vers.1.0 
#   first Version 
#
# (2020-09-02) Vers. 1.01
# Generation of a FPGA configuration file that can be written by the HPS 
#  
version = "1.01"

#
#
#
############################################ Const ###########################################
#
#
#

DELAY_MS = 1 # Delay after critical tasks in milliseconds 

QURTUS_DEF_FOLDER         = "intelFPGA"
QURTUS_DEF_FOLDER_LITE    = "intelFPGA_lite"
EDS_EMBSHELL_DIR          = "/embedded/embedded_command_shell.sh"
BOOTLOADER_FILE_NAME      = 'u-boot-with-spl.sfp'

YOCTO_BASE_FOLDER         = 'poky'

IMAGE_FOLDER_NAME         = 'Image_partitions'

GITNAME                   = "socfpgaPlatformGenerator"
GIT_SCRIPT_URL            = "https://github.com/robseb/socfpgaPlatformGenerator.git"
GIT_U_BOOT_SOCFPGA_URL    = "https://github.com/altera-opensource/u-boot-socfpga"
GIT_U_BOOT_SOCFPGA_BRANCH = "socfpga_v2020.04" # default: master

GIT_LINUXBOOTIMAGEGEN_URL = "https://github.com/robseb/LinuxBootImageFileGenerator.git"

#
# @brief default XML Blueprint file
#
INTELSOCFPGA_BLUEPRINT_XML_FILE ='<?xml version="1.0" encoding = "UTF-8" ?>\n'+\
    '<!-- Linux Distribution Blueprint XML file -->\n'+\
    '<!-- Used by the Python script "LinuxDistro2Image.py -->\n'+\
    '<!-- to create a custom Linux boot image file -->\n'+\
    '<!-- Description: -->\n'+\
    '<!-- item "partition" describes a partition on the final image file-->\n'+\
    '<!-- L "id"        => Partition number on the final image (1 is the lowest number) -->\n'+\
    '<!-- L "type"      => Filesystem type of partition  -->\n'+\
    '<!--   L       => ext[2-4], Linux, xfs, vfat, fat, none, raw, swap -->\n'+\
    '<!-- L "size"      => Partition size -->\n'+\
    '<!-- 	L	    => <no>: Byte, <no>K: Kilobyte, <no>M: Megabyte or <no>G: Gigabyte -->\n'+\
    '<!-- 	L	    => "*" dynamic file size => Size of the files2copy + offset  -->\n'+\
    '<!-- L "offset"    => in case a dynamic size is used the offset value is added to file size-->\n'+\
    '<!-- L "devicetree"=> compile the Linux Device (.dts) inside the partition if available (Top folder only)-->\n'+\
    '<!-- 	L 	    => Yes: Y or No: N -->\n'+\
    '<!-- L "unzip"     => Unzip a compressed file if available (Top folder only) -->\n'+\
    '<!-- 	L 	    => Yes: Y or No: N -->\n'+\
    '<LinuxDistroBlueprint>\n'+\
    '<partition id="1" type="vfat" size="*" offset="500M" devicetree="Y" unzip="N" />\n'+\
    '<partition id="2" type="ext3" size="*" offset="1M" devicetree="N" unzip="Y" />\n'+\
    '<partition id="3" type="RAW" size="*" offset="20M"  devicetree="N" unzip="N" />\n'+\
    '</LinuxDistroBlueprint>\n'

# "u-boot-socfpga" QTS file location directory 
u_boot_bsp_qts_dir_list = ['/board/altera/cyclone5-socdk/qts/', '/board/altera/arria5-socdk/qts/', \
                    '/board/altera/arria10-socdk/qts/']

# "u-boot-socfpga deconfig" file name for make (u-boot-socfpga/configs/)
u_boot_defconfig_list = ['socfpga_cyclone5_defconfig', 'socfpga_arria5_defconfig', \
                    'socfpga_arria10_defconfig']

limaro_version_list = ['gcc-linaro-7.5.0-2019.12-x86_64_arm-linux-gnueabihf']
limaro_url_list = ['https://releases.linaro.org/components/toolchain/binaries/7.5-2019.12/arm-linux-gnueabihf/gcc-linaro-7.5.0-2019.12-x86_64_arm-linux-gnueabihf.tar.xz']

gcc_toolchain_path_list= ['gcc-linaro-7.5.0-2019.12-x86_64_arm-linux-gnueabihf/bin/:$PATH']


#
#
#
############################################ Github clone function ###########################################
#
#
#
import sys

if sys.platform =='linux':
    try:
        import git
        from git import RemoteProgress
        import wget

    except ImportError as ex:
        print('Msg: '+str(ex))
        print('This Python Application requirers "git"')
        print('Use following pip command to install it:')
        print('$ pip3 install GitPython wget')
        sys.exit()
    


if sys.platform =='linux':
    # @brief to show process bar during github clone
    #
    #
    class CloneProgress(RemoteProgress):
        def update(self, op_code, cur_count, max_count=None, message=''):
            if message:
                sys.stdout.write("\033[F")
                print("    "+message)

import os
import time
import io
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from typing import NamedTuple
import math
import glob
from pathlib import Path
from datetime import datetime
from datetime import timedelta
import mmap

try:
    from LinuxBootImageFileGenerator.LinuxBootImageGenerator import Partition,BootImageCreator
except ModuleNotFoundError as ex:
    print('--> Cloning "LinuxBootImageFileGenerator" from GitHub')
    print('       please wait...')

    try:
        git.Repo.clone_from(GIT_LINUXBOOTIMAGEGEN_URL, os.getcwd()+'/LinuxBootImageFileGenerator', branch='master', progress=CloneProgress())
    except Exception as ex:
        print('ERROR: The cloning failed! Error Msg.:'+str(ex))
        sys.exit()

    if not os.path.isabs(os.getcwd()+'/LinuxBootImageFileGenerator'):
        print('ERROR: Failed to clone "LinuxBootImageFileGenerator"')
        print('       Check your network connection and try it again')
        sys.exit()
    
    from LinuxBootImageFileGenerator.LinuxBootImageGenerator import Partition,BootImageCreator

# 
#
# @brief Class for automatisation the entry bootable Linux Distribution generation 
#        for Intel SoC-FPGAs
#   
class SocfpgaPlatformGenerator:

    EDS_Folder_dir              : str # Directory of the Intel EDS folder
    Quartus_proj_top_dir        : str # Directory of the Quartus Project folder 
    
    Qpf_file_name               : str # Name of the Quartus Project ".qpf"-file
    Sof_file_name               : str # Name of the Quartus Project ".sof"-file
    Qsys_file_name              : str # Name of the Quartus Project ".qsys"-file
    Handoff_folder_name         : str # Name of the Quartus Project Hand-off folder
    Uboot_default_preBuild_dir  : str # Directory of the pre-build u-boot for the device 
    Quartus_bootloder_dir       : str # Directory of the Quartus Project "/software/bootloader"-folder
    Sof_folder                  : str # Name of the Quartus Project folder containing the ".sof"-file 
    U_boot_socfpga_dir          : str # Directory of u-boot SoC-FPGA folder 
    Uboot_default_file_dir      : str # Directory of the pre-build default u-boot file 
    unlicensed_ip_found         : bool# Quartus project contains an unlicensed IP (e.g. NIOS II Core) 

    Device_id                   : int # SocFPGA ID (0: Cyclone V; 1: Arria V;2: Arria 10)
    
    PartitionList               : Partition # Partition List for boot image generation 

    Raw_folder_dir              : str # Directory of the RAW Partition folder (u-boot)
    Vfat_folder_dir             : str # Directory of the VFAT Partition folder
    Ext_folder_dir              : str # Directory of the EXT3 Partition folder (rootfs)

    Socfpga_devices_list = ['cyclone5', 'arria5', 'arria10' ]
    Socfpga_arch_list    = ['arm',      'arm',    'arm']

    OutputZipFileName           : str  # Name of the output ".zip" compressed image file 
    ImageFileName               : str  # Name of the output ".img" image file
    Bootloader_available        : bool # Is a bootloader executable available 
    
    BootImageCreator            : BootImageCreator # The boot Image generator object

    def __init__(self):
        ######################################### Find the Intel EDS Installation Path ####################################
        
        print('--> Find the System Platform')

        EDS_Folder_def_suf_dir = os.path.join(os.path.join(os.path.expanduser('~'))) + '/'

        # 1.Step: Find the EDS installation path
        print('--> Try to find the default Intel EDS installation path')

        quartus_standard_ver = False
        # Loop to detect the case that the free Version of EDS (EDS Standard [Folder:intelFPGA]) and 
        #    the free Version of Quartus Prime (Quartus Lite [Folder:intelFPGA_lite]) are installed together 
        while(True):
            if (os.path.exists(EDS_Folder_def_suf_dir+QURTUS_DEF_FOLDER)) and (not quartus_standard_ver):
                self.EDS_Folder=EDS_Folder_def_suf_dir+QURTUS_DEF_FOLDER
                quartus_standard_ver = True
            elif(os.path.exists(EDS_Folder_def_suf_dir+QURTUS_DEF_FOLDER_LITE)):
                self.EDS_Folder=EDS_Folder_def_suf_dir+QURTUS_DEF_FOLDER_LITE
                quartus_standard_ver = False
            else:
                print('ERROR: No Intel EDS Installation Folder was found!')
                sys.exit()

            # 2.Step: Find the latest Intel EDS Version No.
            avlVer = []
            for name in os.listdir(self.EDS_Folder):
                if  os.path.abspath(name):
                    try:
                        avlVer.append(float(name))
                    except Exception:
                        pass

            if (len(avlVer)==0):
                print('ERROR: No valid Intel EDS Version was found')
                sys.exit()

            avlVer.sort(reverse = True) 

            highestVer = avlVer[0]
            self.EDS_Folder = self.EDS_Folder +'/'+ str(highestVer)   

            if (not(os.path.realpath(self.EDS_Folder))):
                print('ERROR: No valid Intel EDS Installation Folder was found!')
                sys.exit()

            if(highestVer < 19): 
                print('ERROR: This script is designed for Intel EDS Version 19+ (19.1, 20.1, ...) ')
                print('       You using Version '+str(highestVer)+' please update Intel EDS!')
                sys.exit()
            elif(highestVer > 20.1):
                print('WARNING: This script was designed for Intel EDS Version 19.1 and 20.1')
                print('         Your version is newer. Errors may occur!')

            # Check if the NIOS II Command Shell is available 
            if((not(os.path.isfile(self.EDS_Folder+EDS_EMBSHELL_DIR)) )):
                if( not quartus_standard_ver):
                    print('ERROR: Intel EDS Embedded Command Shell was not found!')
                    sys.exit()
            else:
                break

        print('        Following EDS Installation Folder was found:')
        print('        '+self.EDS_Folder)


        ############################### Check that the script runs inside the Github folder ###############################
        print('--> Check that the script runs inside the Github folder')
        self.Quartus_proj_top_dir =''
        excpath = os.getcwd()
        try:
            if(len(excpath)<len(GITNAME)):
                raise Exception()

            # Find the last slash in the execution path 
            slashpos =0
            for str_ in excpath:
                slashpos_pos=excpath.find('/',slashpos)
                if(slashpos_pos == -1):
                    break
                slashpos= slashpos_pos+len('/')

            if(not excpath[slashpos:] == GITNAME):
                    raise Exception()

            self.Quartus_proj_top_dir = excpath[:slashpos-1]

        except Exception:
            print('ERROR: The script was not executed inside the cloned Github folder')
            print('       Please clone this script from Github and execute the script')
            print('       directly inside the cloned folder!')
            print('URL: '+GIT_SCRIPT_URL)
            sys.exit()

        if not os.path.isdir(excpath+'/ubootScripts'):
            print('ERROR: The u-boot default script folder "ubootScripts" is not available')

        ############################### Check that the script runs inside the Quartus project ###############################
        print('--> Check that the script runs inside the Quartus Prime project folder')

        # Find the Quartus project (.qpf) file 
        self.Qpf_file_name = ''
        for file in os.listdir(self.Quartus_proj_top_dir):
                if ".qpf" in file:
                    self.Qpf_file_name =file
                    break

        # Find the Quartus  (.sof) (SRAM Object) file 
        self.Sof_file_name = ''
        self.Sof_folder = ''
        # Looking in the top folder for the sof file
        for file in os.listdir(self.Quartus_proj_top_dir):
                if ".sof" in file:
                    self.Sof_file_name =file
                    break
        if self.Sof_file_name == '':
            # Looking inside the "output_files" and "output" folders
            if os.path.isdir(self.Quartus_proj_top_dir+'/output_files'):
                self.Sof_folder = '/output_files'
            if os.path.isdir(self.Quartus_proj_top_dir+'/output'):
                self.Sof_folder = '/output'
            for file in os.listdir(self.Quartus_proj_top_dir+self.Sof_folder):
                if ".sof" in file:
                    self.Sof_file_name =file
                    break

        # Find the Platform Designer (.qsys) file  
        self.Qsys_file_name = ''
        for file in os.listdir(self.Quartus_proj_top_dir):
                if ".qsys" in file and not ".qsys_edit" in file:
                    self.Qsys_file_name =file
                    print(self.Qsys_file_name)
                    break

        print('    Founded files: ')
        print('      QPF: "'+self.Qpf_file_name+'"')
        print('      SOF: "'+self.Sof_file_name+'"')
        print('     QSYS: "'+self.Qsys_file_name+'"')

        # Does the SOF file contains an IP with a test licence, such as a NIOS II Core?
        self.unlicensed_ip_found=False
        if self.Sof_file_name in "_time_limited":
            print('********************************************************************************')
            print('*                   Unlicensed IP inside the project found!                    *')
            print('*                  Generation of ".rbf" file is not possible!                  *')
            print('********************************************************************************\n')
            self.unlicensed_ip_found=True


        # Find the Platform Designer folder
        if self.Qsys_file_name=='' or self.Qpf_file_name=='' or self.Sof_file_name=='':
            print('\nERROR: The script was not executed inside the cloned Github- and Quartus Prime project folder!')
            print('         Please clone this script with its folder from Github,')
            print('         copy it to the top folder of your Quartus project and execute the script')
            print('         directly inside the cloned folder!')
            print(' NOTE:   Be sure that the QPF,SOF and QSYS folder was found!')
            print('         These files must be in the top project folder')
            print('         The SOF file can also be inside a sub folder with the name "output_files" and "output"')
            print('       URL: '+GIT_SCRIPT_URL+'\n')
            print('       --- Required folder structure  ---')
            print('          YOUR_QURTUS_PROJECT_FOLDER ')
            print('       |     L-- PLATFORM_DESIGNER_FOLDER')
            print('       |     L-- platform_designer.qsys')
            print('       |     L-- _handoff')
            print('       |     L-- quartus_project.qpf')
            print('       |     L-- socfpgaPlatformGenerator <<<----')
            print('       |         L-- socfpgaPlatformGenerator.py')
            print('       Note: File names can be chosen freely\n')
            print('NOTE: It is necessary to build the Prime Quartus Project for the bootloader generation!')
            sys.exit()

        # Find the handoff folder
        print('--> Find the Quartus handoff folder')
        self.Handoff_folder_name = ''
        handoff_folder_start_name =''
        for file in os.listdir(self.Quartus_proj_top_dir):
                if "_handoff" in file:
                    handoff_folder_start_name =file
                    break
        folder_found = False
        for folder in os.listdir(self.Quartus_proj_top_dir+'/'+handoff_folder_start_name):
            if os.path.isdir(self.Quartus_proj_top_dir+'/'+handoff_folder_start_name+'/'+folder):
                self.Handoff_folder_name = folder
                if folder_found:
                    print('ERROR: More than one folder inside the Quartus handoff folder "'+self.Handoff_folder_name+'" found! Please delete one!')
                    print('NOTE: It is necessary to build the Prime Quartus Project for the bootloader generation!')
                    sys.exit()
                folder_found = True
        self.Handoff_folder_name = handoff_folder_start_name+'/'+self.Handoff_folder_name
        print('     Handoff folder:" '+self.Handoff_folder_name+'"')

        # Find the "hps.xml"-file inside the handoff folder
        print('--> Find the "hps.xml" file ')
        handoff_xml_found =False

        for file in os.listdir(self.Quartus_proj_top_dir+'/'+self.Handoff_folder_name):
            if "hps.xml" == file:
                handoff_xml_found =True
                break 
        if not handoff_xml_found:
            print('ERROR: The "hps.xml" file inside the handoff folder was not found!')
            print('NOTE: It is necessary to build the Prime Quartus Project for the bootloader generation!')
            sys.exit()

        # Load the "hps.xml" file to read the device name
        print('--> Read the "hps.xml"-file to decode the device name')

        try:
            tree = ET.parse(self.Quartus_proj_top_dir+'/'+self.Handoff_folder_name+'/'+'hps.xml') 
            root = tree.getroot()
        except Exception as ex:
            print(' ERROR: Failed to parse "hps.xml" file!')
            print(' Msg.: '+str(ex))
            sys.exit()

        device_name_temp =''
        for it in root.iter('config'):
            name = str(it.get('name'))
            if name == 'DEVICE_FAMILY':
                device_name_temp = str(it.get('value'))
                break
        if device_name_temp == '':
            print('ERROR: Failed to decode the device name inside "hps.xml"')

        # Convert Device name
        if device_name_temp == 'Cyclone V':
            self.Device_id = 0
            '''
            elif device_name_temp == 'Arria V':
                self.Device_id = 1
            elif device_name_temp == 'Arria 10':
                self.Device_id = 2
            '''
            ## NOTE: ADD ARRIA V/10 SUPPORT HERE 
        else:
            print('Error: Your Device ('+device_name_temp+') is not supported right now!')
            print('       I am working on it...')
            sys.exit()
        print('     Device Name:"'+device_name_temp+'"') 

        self.Uboot_default_file_dir =''
        # Find the depending default u-boot script file 
        for name in os.listdir(excpath+'/ubootScripts'):
            if  os.path.isfile(excpath+'/ubootScripts/'+name) and \
            (name.find(self.Socfpga_devices_list[self.Device_id])!=-1):
                self.Uboot_default_file_dir=excpath+'/ubootScripts/'+name
        if self.Uboot_default_file_dir =='':
            print('NOTE: No depending default u-boot script file is available for this device!')

        # Find the depending default pre-build u-boot 
        self.Uboot_default_preBuild_dir =''
        for name in os.listdir(excpath+'/ubootDefaultSFP'):
            if  os.path.isfile(excpath+'/ubootDefaultSFP/'+name) and \
            (name.find(self.Socfpga_devices_list[self.Device_id])!=-1):
                self.Uboot_default_preBuild_dir=excpath+'/ubootDefaultSFP/'+name
        if self.Uboot_default_preBuild_dir =='':
            print('NOTE: No depending default u-boot pre-build file is available for this device!')
        
    ##################################### Update "LinuxBootImageFileGenerator" ####################################################
        print('-> Pull the latest "LinuxBootImageFileGenerator" Version from GitHub!')
        g = git.cmd.Git(os.getcwd()+'/LinuxBootImageFileGenerator')
        g.pull()

    ############################### Create "software/bootloader" folder inside Quartus project  ###################################
        if not os.path.isdir(self.Quartus_proj_top_dir+'/'+'software'):
            print('-> Create the folder software')
            try:
                os.mkdir(self.Quartus_proj_top_dir+'/'+'software')      
            except Exception as ex:
                print('ERROR: Failed to create the software folder MSG:'+str(ex))

        self.Quartus_bootloder_dir = self.Quartus_proj_top_dir+'/'+'software'+'/'+'bootloader'
        self.Bootloader_available =False
        if not os.path.isdir(self.Quartus_bootloder_dir):
            print('-> Create the folder bootloader')
            try:
                os.mkdir(self.Quartus_bootloder_dir)      
            except Exception as ex:
                print('ERROR: Failed to create the bootloader folder MSG:'+str(ex))
        else:
            self.Bootloader_available = True
        self.U_boot_socfpga_dir = self.Quartus_bootloder_dir+'/'+'u-boot-socfpga'
    ###############################################   Create SD-CARD folder  ##############################################
        # Create the partition blueprint xml file 
        if os.path.exists('SocFPGABlueprint.xml'):
            # Check that the SocFPGABlueprint XML file looks valid
            print('---> The Linux Distribution blueprint XML file exists')
        else:
            print(' ---> Creating a new Linux Distribution blueprint XML file')
            with open('SocFPGABlueprint.xml',"w") as f: 
                f.write(INTELSOCFPGA_BLUEPRINT_XML_FILE)
        
    #
    #
    #
    # @brief Create the partition table for Intel SoC-FPGAs by reading the "SocFPGABlueprint" XML-file
    # @return                      success
    #
    def GeneratePartitionTable(self):
        ############################################ Read the XML Blueprint file  ###########################################
        ####################################### & Process the settings of a partition   ####################################
        print('---> Read the XML blueprint file ')
        try:
            tree = ET.parse('SocFPGABlueprint.xml') 
            root = tree.getroot()
        except Exception as ex:
            print(' ERROR: Failed to parse SocFPGABlueprint.xml file!')
            print(' Msg.: '+str(ex))
            return False
        
        # Load the partition table of XML script 
        print('---> Load the items of XML file ')
        self.PartitionList= []

        for part in root.iter('partition'):
            try:
                id = str(part.get('id'))
                type = str(part.get('type'))
                size = str(part.get('size'))
                offset = str(part.get('offset'))
                devicetree = str(part.get('devicetree'))
                unzip_str = str(part.get('unzip'))
                comp_ubootscr = str(part.get('ubootscript'))
            except Exception as ex:
                print(' ERROR: XML File decoding failed!')
                print(' Msg.: '+str(ex))
                return False

            comp_devicetree =False
            if devicetree == 'Y' or devicetree == 'y':
                comp_devicetree = True

            unzip =False
            if unzip_str == 'Y' or unzip_str == 'y':
                unzip = True

            try:
                self.PartitionList.append(Partition(True,id,type,size,offset,comp_devicetree,unzip,comp_ubootscr))
            except Exception as ex:
                print(' ERROR: Partition data import failed!')
                print(' Msg.: '+str(ex))
                return False

        ####################################### Check if the partition folders are already available  #######################################

        # Generate working folder names for every partition
        working_folder_pat = []
        for part in self.PartitionList:
            working_folder_pat.append(part.giveWorkingFolderName(True))

        create_new_folders = True

        # Check if the primary partition folder exists
        if os.path.isdir(IMAGE_FOLDER_NAME):
            if not len(os.listdir(IMAGE_FOLDER_NAME)) == 0:
                # Check that all partition folders exist
                for file in os.listdir(IMAGE_FOLDER_NAME):
                    if not file in working_folder_pat:
                        print('ERROR:  The existing "'+IMAGE_FOLDER_NAME+'" Folder is not compatible with this configuration!')
                        print('        Please delete or rename the folder "'+IMAGE_FOLDER_NAME+'" to allow the script')
                        print('        to generate a matching folder structure for your configuration')
                        return False  
                create_new_folders = False
        else: 
            try:
                os.makedirs(IMAGE_FOLDER_NAME)
            except Exception as ex:
                print(' ERROR: Failed to create the image import folder on this directory!')
                print(' Msg.: '+str(ex))
                return False
    ###################################### Create new import folders for every partition   #######################################
        if create_new_folders:
            for folder in working_folder_pat:
                try:
                    os.makedirs(IMAGE_FOLDER_NAME+'/'+folder)
                except Exception as ex:
                    print(' ERROR: Failed to create the partition import folder on this directory!')
                    print(' Msg.: '+str(ex))
                    return False

    ################################### Check that all required Partitions are available  ####################################
        self.Raw_folder_dir =''
        self.Vfat_folder_dir=''
        self.Ext_folder_dir=''
        excpath = os.getcwd()

        for part in self.PartitionList:
            if part.type_hex=='a2':
                self.Raw_folder_dir=excpath+'/'+IMAGE_FOLDER_NAME+'/'+part.giveWorkingFolderName(False)
            elif part.type_hex=='b': # FAT
                self.Vfat_folder_dir=excpath+'/'+IMAGE_FOLDER_NAME+'/'+part.giveWorkingFolderName(False)
                if not part.comp_devicetree:
                    print('NOTE:  The devicetree compilation is for the VFAT/FAT partition not enabled!')
                    print('       The script may not work properly!')
                if not part.comp_ubootscript == self.Socfpga_arch_list[self.Device_id]:
                    print('NOTE:  Compilation of the u-boot script is for the ext3/LINUX partition\n'+ \
                        '       is not enabled or the wrong architecture is selected!\n'+ \
                        '       Use: ubootscript="'+self.Socfpga_arch_list[self.Device_id]+'"')
                    print('       The script may not work properly!')

            elif part.type_hex=='83': # LINUX
                self.Ext_folder_dir=excpath+'/'+IMAGE_FOLDER_NAME+'/'+part.giveWorkingFolderName(False)
                if not part.unzip_file:
                    print('NOTE:  Unzip is for the ext3/LINUX partition not enabled!')
                    print('      The script may not work properly!')
        # All folders there ?
        if self.Raw_folder_dir =='':
            print('ERROR: The chosen partition table has now RAW/NONE-partition.')
            print('       That is necessary for the bootloader')
            return False
        if self.Vfat_folder_dir =='':
            print('ERROR: The chosen partition table has now VFAT-partition.')
            print('       That is necessary for the Kernel image')
            return False
        if self.Ext_folder_dir =='':
            print('ERROR: The chosen partition table has now EXT-partition.')
            print('       That is necessary for the rootfs')
            return False
        return True

    #
    #
    #
    # @brief Build the bootloader for the chosen Intel SoC-FPGA
    #        and copy the output files to the depending partition folders
    # @param generation_mode       0: The User can chose how the bootloader should be build
    #                              1: Allways build or re-build the entire bootloader 
    #                              2: Build the entire bootloader in case it was not done
    #                              3: Use the default pre-build bootloader for the device 
    # @return                      success
    #
    def BuildBootloader(self, generation_mode= 0):
    #################################### Setup u-boot with the Quartus Prime Settings  ################################################

        bootloader_build_required =True
        use_default_bootloader = False
        excpath = os.getcwd()

        if (self.Bootloader_available and os.path.isfile(self.Raw_folder_dir+'/'+'u-boot-with-spl.sfp')):
            bootloader_build_required = False

        if generation_mode==1:
            # Allways build or re-build the entire bootloader 
            bootloader_build_required=True
        elif generation_mode==2:
            # Use the default pre-build bootloader for the device 
            bootloader_build_required =False
            use_default_bootloader = True
        elif generation_mode==0:
            #The User can chose how the bootloader should be build
            print('\n################################################################################')
            print('#                                                                              #')
            print('#                       Bootloader Generation Settings                         #')
            print('#                                                                              #')
            if not bootloader_build_required:
                print('#                    Do you want to rebuild the bootloader?                    #')
            print('#                                                                              #')
            print('--------------------------------------------------------------------------------')
            print('#    D:              Use the pre-build default bootloader                      #')
            print('#    Y:              Build/Rebuild the bootloader                              #')
    

            if not bootloader_build_required:
                print('#    anything else:  Continue without rebuilding the bootloader                #')
            print('#    Q:              Abort                                                     #')
            print('------------------------------------------------------------------------------')
            __wait2__ = input('#              Please type ...                                               #\n')
            
            if __wait2__ =='q' or __wait2__=='Q':
                sys.exit()
            elif __wait2__ =='Y' or __wait2__=='y':
                bootloader_build_required = True
            elif __wait2__ =='D' or __wait2__=='d':
                use_default_bootloader = True
                bootloader_build_required=False
    ############################################  Use the default pre-build bootloader   ################################################
        if use_default_bootloader: 
            print('--> Use the default pre-build bootloader')
            if not os.path.isdir(excpath+'/ubootDefaultSFP'):
                print('ERROR: The u-boot default pre-build folder "ubootDefaultSFP" is not available')
                return False
            try:
                shutil.copy2(self.Uboot_default_preBuild_dir,self.Raw_folder_dir+'/u-boot-with-spl.sfp')
            except Exception as ex:
                print('ERROR: Failed to copy the pre-build file to the RAW folder MSG='+str(ex))
                return False
            
    ################################################  Install the Linaro toolchain  #####################################################
        if bootloader_build_required:
            toolchain_dir = excpath+'/toolchain'
            print('--> Check if the linaro toolchain is installed')
            if not os.path.isdir(toolchain_dir+'/'+limaro_version_list[self.Device_id]):
                if not os.path.isdir(toolchain_dir):
                    os.mkdir(toolchain_dir)
                
                if not os.path.isfile(toolchain_dir+'/'+limaro_version_list[self.Device_id]+'.tar.xz'):
                    print('--> Download the linaro toolchain "'+limaro_version_list[self.Device_id]+'"')
                    try:
                        wget.download(limaro_url_list[self.Device_id], out=toolchain_dir)
                    except Exception as ex:
                        print('\nERROR: Failed to download with wget! MSG:'+str(ex))
                        print('       Download URL: "'+limaro_url_list[self.Device_id]+'"')
                        return False
                if os.path.isfile(toolchain_dir+'/'+limaro_version_list[self.Device_id]+'.tar.xz'):
                    print('\n--> Unpackage the linaro toolchain archive file')
                    try:
                        os.system('tar xf '+toolchain_dir+'/'+ \
                                limaro_version_list[self.Device_id]+'.tar.xz -C '+toolchain_dir)
                    except subprocess.CalledProcessError:
                        print('ERROR: Failed to unpackage the linaro toolchain!')
                        return False
                    print('    == Done')
                    print('--> Remove the limaro archive file')
                    try:
                        shutil.rmtree(toolchain_dir+'/'+ \
                                limaro_version_list[self.Device_id]+'.tar.xz')
                    except Exception:
                        print('ERROR: Failed to remove the limaro archive file')
                    print('    == Done')

                if not os.path.isdir(toolchain_dir+'/'+limaro_version_list[self.Device_id]):
                    print('ERROR: The download or the unpackage of the linaro toolchain failed!')
                    print('       Download URL: "'+limaro_url_list[self.Device_id]+'"')
                    return False
            else:
                print('    The linaro toolchain in Version "'+limaro_version_list[self.Device_id]+ \
                        '" is installed')

            # Define the EXPORT value to the toolchain path
            export_path_cmd ='export PATH='+'`pwd`/toolchain/'+gcc_toolchain_path_list[self.Device_id]+'\n'

    ################################################  Build the bootloader #####################################################
            print('--> Start the Intel Embedded Command Shell')
            try:
                # Create the BSP package for the device with the Intel EDS shell
                with subprocess.Popen(self.EDS_Folder+'/'+EDS_EMBSHELL_DIR, stdin=subprocess.PIPE) as edsCmdShell:
                    time.sleep(DELAY_MS)
                    
                    print('--> Generate the Board Support Package (BSP) for the Quartus Prime configuration')
                    b = bytes(' cd '+self.Quartus_proj_top_dir+"\n", 'utf-8')
                    edsCmdShell.stdin.write(b) 

                    b = bytes('bsp-create-settings --type spl --bsp-dir software/bootloader '+ \
                            '--preloader-settings-dir "'+self.Handoff_folder_name+'" ' +\
                            '--settings software/bootloader/settings.bsp\n','utf-8')

                    edsCmdShell.stdin.write(b)
                    edsCmdShell.communicate()
                    
                    
                # Check that BSP generation is okay
                if not os.path.isdir(self.Quartus_proj_top_dir+'/software/bootloader/generated') or \
                    not os.path.isfile(self.Quartus_proj_top_dir+'/software/bootloader/settings.bsp'):
                    print('ERROR: The BSP generation failed!')
                    return False
                
    ####################################################### Clone "u-boot-socfpga" ################################################
                if(os.path.isdir(self.U_boot_socfpga_dir)):
                    print('--> "u-boot-socfpga" is already available')
                    print('       Pull it from Github')
                    g = git.cmd.Git(self.U_boot_socfpga_dir)
                    g.pull()
                    
                else:
                    print('--> Cloning "u-boot-socfpga" Version ('+GIT_U_BOOT_SOCFPGA_URL+')\n')
                    print('       please wait...')

                    try:
                        git.Repo.clone_from(GIT_U_BOOT_SOCFPGA_URL, self.U_boot_socfpga_dir, branch=GIT_U_BOOT_SOCFPGA_BRANCH, progress=CloneProgress())
                    except Exception as ex:
                        print('ERROR: The cloning failed! Error Msg.:'+str(ex))
                        print('       Check your network connection and try it again')
                        return False

                    if not os.path.isabs(self.U_boot_socfpga_dir):
                        print('ERROR: Failed to clone u-boot-socfpga!')
                        print('       Check your network connection and try it again')
                        return False

                    print('       cloning done')

    ################################################## Find the EDS Filter script ##############ä####################################
                eds_filter_script_dir = '/'+'arch'+'/'+ \
                                        'arm'+'/'+'mach-socfpga'+'/'+'qts-filter.sh'
                # Find the filter script
                if not os.path.isfile(self.U_boot_socfpga_dir+eds_filter_script_dir):
                    print('ERROR: The EDS Filter script is not available on the default directory')
                    print('       "/arch/arm/mach-socfpga/qts-filter.sh"')
                    return False
                # Find the BPS for the selected device inside u-boot
                u_boot_bsp_qts_dir=u_boot_bsp_qts_dir_list[self.Device_id]
                if not os.path.isdir(self.U_boot_socfpga_dir+'/'+u_boot_bsp_qts_dir):
                    print('Error: The u-boot BSP QTS direcorory is for the device not available!')
                    print('       '+u_boot_bsp_qts_dir)
                    return False
    ####################################################### Run EDS filter script ################################################
                print('--> Run the Intel EDS Filter script')
                with subprocess.Popen(self.EDS_Folder+'/'+EDS_EMBSHELL_DIR, stdin=subprocess.PIPE) as edsCmdShell:
                    time.sleep(DELAY_MS)
                    b = bytes('cd '+self.Quartus_proj_top_dir+'/software/bootloader/u-boot-socfpga \n','utf-8')
                    edsCmdShell.stdin.write(b) 
                    #
                    # 
                    # soc_type      - Type of SoC, either 'cyclone5' or 'arria5'.
                    # input_qts_dir - Directory with compiled Quartus project
                    #                and containing the Quartus project file (QPF).
                    # input_bsp_dir - Directory with generated bsp containing
                    #                 the settings.bsp file.
                    # output_dir    - Directory to store the U-Boot compatible
                    #                 headers.

                    b = bytes('./'+eds_filter_script_dir+' '+self.Socfpga_devices_list[self.Device_id]+' ../../../ ../ ' \
                            '.'+u_boot_bsp_qts_dir+'  \n','utf-8')
                    edsCmdShell.stdin.write(b) 
                    #time.sleep(10*DELAY_MS)

                    edsCmdShell.communicate()
                    time.sleep(3*DELAY_MS)
            
            except Exception as ex:
                print('ERROR: Failed to start the Intel EDS Command Shell! MSG:'+ str(ex))
                return False

            # Check that the output files are available 
            if (not os.path.isdir(self.Quartus_bootloder_dir+'/'+"generated"))  or \
            (not os.path.isdir(self.Quartus_bootloder_dir+'/'+"generated"+'/'+"sdram")):
                print('ERROR: BSP Generation failed!')
                return False


            start_menuconfig = False 
            run_defconfig =True

            if generation_mode==0:
                print('\n################################################################################')
                print('#                                                                              #')
                print('#                     OPTIONAL: CHANGE U-BOOT MANUALLY                         #')
                print('#                                                                              #')
                print('#  At this point it is possible to change the code of "u-boot-socfpga"         #')
                print('#                                                                              #')
                print('--------------------------------------------------------------------------------')
                print('#                   --- "u-boot-socfpga" file Directory ---                   #')
                print('#   '+self.U_boot_socfpga_dir)
                print('--------------------------------------------------------------------------------')
                print('#                M: Start menuconfig for "u-boot-socfpga"                      #')
                print('#                D: Start menuconfig for "u-boot-socfpga" without defconfig    #')
                print('#                Q: Abort                                                      #')
                print('#    anything else: continue with compiling "u-boot-socfpga"                   #')
                print('------------------------------------------------------------------------------')
                __wait__ = input('Type anything to continue ... ')

                if __wait__ =='q' or __wait__=='Q':
                    return False
                
                if __wait__ =='m' or __wait__=='M':
                    start_menuconfig = True

                if __wait__ =='d' or __wait__=='D':
                    start_menuconfig = True
                    run_defconfig = False

        ###################################################   Build u-boot  ################################################
            print('--> Start the Intel Embedded Command Shell')
            try:
                with subprocess.Popen(self.EDS_Folder+'/'+EDS_EMBSHELL_DIR, stdin=subprocess.PIPE) as edsCmdShell:
                    time.sleep(DELAY_MS)
                    print('--> Compile "u-boot-socfpga"')

                    b = bytes(' cd '+self.Quartus_proj_top_dir+'/software/bootloader/u-boot-socfpga \n', 'utf-8')
                    edsCmdShell.stdin.write(b) 

                    b =bytes(export_path_cmd,'utf-8')
                    edsCmdShell.stdin.write(b) 
        
                    b = bytes('export CROSS_COMPILE=arm-linux-gnueabihf- \n','utf-8')
                    edsCmdShell.stdin.write(b) 

                    b = bytes('export ARCH=arm \n','utf-8')
                    edsCmdShell.stdin.write(b) 

                    if run_defconfig: 
                        # Clean make
                        b = bytes('make distclean \n','utf-8')
                        edsCmdShell.stdin.write(b) 
                        
                        # Make diskclean 
                        b = bytes('make '+u_boot_defconfig_list[self.Device_id]+'\n','utf-8')   
                        edsCmdShell.stdin.write(b) 
                    if not start_menuconfig: 
                        # Make 
                        b = bytes('make -j 24 \n','utf-8')
                        edsCmdShell.stdin.write(b) 

                    edsCmdShell.communicate()
                    time.sleep(DELAY_MS)
            
            except Exception as ex:
                print('ERROR: Failed to start the Intel EDS Command Shell! MSG:'+ str(ex))
                return False

            ################################################### Start menuconfig ###################################################
            # Start menuconfig for "u-boot-socfpga"
            if start_menuconfig:
                # Create "menuconfig.sh" shell script for starting menuconfig
                if os.path.isfile('menuconfig.sh'):
                    try:
                        os.remove('menuconfig.sh')
                    except Exception:
                        print('ERROR: Failed to remove menuconfig.sh')

                with open('menuconfig.sh', "a") as f:
                    f.write('#!/bin/sh\n')
                    f.write('export TOP_FOLDER=`pwd`\n')
                    f.write('cd && cd '+self.Quartus_proj_top_dir+'/software/bootloader/u-boot-socfpga\n')
                    f.write('make menuconfig\n')
                    f.write('cd $TOP_FOLDER\n')
                if not os.path.isfile('menuconfig.sh'):
                    print('ERROR: Failed to create "menuconfig.sh" script')
                    return False
                
                # Run the shell script to allow the user to use menuconfig
                print('--> Starting menuconfig for "u-boot-socfpga"')
                os.system('chmod +x menuconfig.sh  && sh  menuconfig.sh')
                __wait3__ = input('Type anything to continue (Q= Abort)... ')

                if __wait3__ == 'q' or __wait3__ == 'Q':
                    sys.exit()

                # Remove the shell script 
                if os.path.isfile('menuconfig.sh'):
                    try:
                        os.remove('menuconfig.sh')
                    except Exception:
                        print('ERROR: Failed to remove menuconfig.sh')

                # Build u-boot with the menuconfig changes 
                try:
                    with subprocess.Popen(self.EDS_Folder+'/'+EDS_EMBSHELL_DIR, stdin=subprocess.PIPE) as edsCmdShell:
                        time.sleep(DELAY_MS)
                        print('--> Compile "u-boot-socfpga"')

                        b = bytes(' cd '+self.Quartus_proj_top_dir+'/software/bootloader/u-boot-socfpga \n', 'utf-8')
                        edsCmdShell.stdin.write(b) 

                        b =bytes(export_path_cmd,'utf-8')
                        edsCmdShell.stdin.write(b) 

                        b = bytes('export CROSS_COMPILE=arm-linux-gnueabihf- \n','utf-8')
                        edsCmdShell.stdin.write(b) 

                        b = bytes('export ARCH=arm \n','utf-8')
                        edsCmdShell.stdin.write(b) 

                        b = bytes('make -j 24 \n','utf-8')
                        edsCmdShell.stdin.write(b) 

                        edsCmdShell.communicate()
                        time.sleep(DELAY_MS)
                
                except Exception as ex:
                    print('ERROR: Failed to start the Intel EDS Command Shell! MSG:'+ str(ex))
                    return False

            # Check that u-boot output file is there 
            if not os.path.isfile(self.U_boot_socfpga_dir+'/'+'u-boot-with-spl.sfp') or \
                not os.path.isfile(self.U_boot_socfpga_dir+'/'+'u-boot.img'):
                print('ERROR: u-boot build failed!')
                return False

            # Read the creation date of the output files to check that the files are new
            modification_time = os.path.getmtime(self.U_boot_socfpga_dir+'/'+'u-boot-with-spl.sfp') 
            current_time =  datetime.now().timestamp()

            # Offset= 5 min 
            if modification_time+ 5*60 < current_time:
                print('Error: u-boot build failed!')

            print('--> "u-boot-socfpga" build was successfully')
        # u-boot build

    ####################################### Copy the bootloader files to the partition #######################################
        print(' --> Copy the bootloader file "'+BOOTLOADER_FILE_NAME+'" to the RAW partition')

        # Find the RAW Partition and 
        self.Raw_folder_dir =''
        for part in self.PartitionList:
            if part.type_hex=='a2':
                self.Raw_folder_dir=excpath+'/'+IMAGE_FOLDER_NAME+'/'+part.giveWorkingFolderName(False)
        if self.Raw_folder_dir =='':
            print('ERROR: The chosen partition table has now RAW/NONE-partition.')
            print('       That is necessary for the bootloader')
            return False
        
        # Copy the bootloader file 
        if bootloader_build_required and not use_default_bootloader:
            print('--> Copy the bootloader executable to the partition')
            try:
                shutil.copy2(self.U_boot_socfpga_dir+'/'+BOOTLOADER_FILE_NAME,
                    self.Raw_folder_dir+'/'+BOOTLOADER_FILE_NAME)
            except Exception as ex:
                print('ERORR: Failed to copy the bootloader file! MSG: '+str(ex))
                return False

        print('     = Done')
        return True
    
    #
    #
    #
    # @brief Copy all essential Linux Distribution files (rootfs,zImage,Device Tree) to  
    #        the depending partition
    # @param copy_mode             0: The User can chose which files should be used 
    #                              1: Use compatible Yocto Project files
    #                              2: Use the existing files inside the partition
    # @note                        Use this method allways! It checks if all files are available
    # @return                      success
    #
    def CopyLinuxFiles2Partition(self,copy_mode=0):
    #########################################  Rootfs,zImage,... already in VFAT folder #######################################
        linux_files_available= False
        if os.path.isfile(self.Ext_folder_dir+'/rootfs.tar.gz') and os.path.isfile(self.Vfat_folder_dir+'/zImage'):
            # Check that a device tree file is available
            for file in os.listdir(self.Vfat_folder_dir):
                if os.path.isfile(self.Vfat_folder_dir+'/'+file) and \
                not file.find('.dts')==-1:
                    linux_files_available=True
                    print('--> All necessary Linux files are already available')
                    break

    ###################################### Find a Linux build with the Yocto Project    ######################################
        yocto_project_available =False
        if not copy_mode==2:
            print('--> Looking for the Yocto Project ')

            # Directory of the Yocto Project rootfs .tar.gz file
            yocto_rootfs_dir =''
            yocto_rootfs_name='-'

            # Directory of the Yocto Project compressed Kernel file 
            yocto_zimage_dir  =''
            yocto_zimage_name ='-'
            
            # Directory of the Yocto Project uncomplied devicetree file
            yocto_devicetree_dir=''  
            yocto_devicetree_name='-'

            yocto_base_dir =os.path.join(os.path.expanduser('~')) +'/'+ YOCTO_BASE_FOLDER
            yocto_deployImgaes_dir = yocto_base_dir+'/build/tmp/deploy/images'
            yocto_device_dir = yocto_deployImgaes_dir+'/'+self.Socfpga_devices_list[self.Device_id]+'/'

            if os.path.isdir(yocto_base_dir):
                print('    The Yocto Installation was found!')
                #  Find a Yocto Linux Distribution that is compatible with this project
                print('--> Find a Yocto Linux Distribution that is compatible with this project')
                print('    Serarch Dir: "'+yocto_device_dir+'"')
            
                if os.path.isdir(yocto_device_dir):
                    print('    A project with the same device "'+self.Socfpga_devices_list[self.Device_id]+'" was found')
                    # Find the zImage, the rootfs and devicetree files if available
                    for name in os.listdir(yocto_device_dir):
                        
                        if  os.path.isfile(yocto_device_dir+'/'+name) and \
                            not os.path.islink(yocto_device_dir+'/'+name):

                            if name.find("rootfs") !=-1:
                                yocto_rootfs_dir = yocto_device_dir+'/'+name
                                yocto_rootfs_name = name
                            elif name.find("zImage") !=-1:
                                yocto_zimage_dir = yocto_device_dir+'/'+name
                                yocto_zimage_name = name
                            elif name.find("devicetree") !=-1:
                                # NOTE: Must be checked!!
                                yocto_devicetree_dir = yocto_device_dir+'/'+name
                                yocto_devicetree_name = name 
                    # Something found?
                    yocto_project_available=  not yocto_rootfs_dir =='' and not yocto_zimage_dir==''
                if not yocto_project_available:
                    print('     No Yocto Installation was found!')
            else:
                print('     No Yocto Installation was found!')
        else:
            if not linux_files_available:
                print('ERROR: They are no rootfs-,zImage or device Tree '+ \
                        ' files inside the Partition folder available ') 
                print('       Please insert manually or use the Yocto-Project output')
                return False

        if yocto_project_available:
            # Read the modication date of the Yocto Project rootfs file 
            modification_time = time.ctime(os.path.getmtime(yocto_rootfs_dir))

            if copy_mode==0:
                yocto_project_available =False
                print('\n################################################################################')
                print('#                                                                              #')
                print('#            COMPATIBLE YOCTO PROJECT LINUX DISTRIBUTION WAS FOUND             #')
                print('#                     Use this distribution for the build?                     #')
                print('--------------------------------------------------------------------------------')
                print('#                   --- Yocto Linux Distribution  ---                          #')
                print('#    Directory: "'+yocto_device_dir+'" ')
                print('#    Modification Date: '+str(modification_time))
                print('#    rootfs: "'+yocto_rootfs_name)
                print('#    zImage: "'+yocto_zimage_name+'"')
                print('#    Devicetree: "'+yocto_devicetree_name+'"')
                print('--------------------------------------------------------------------------------')
                print('#                Y: Yes, use these files for this build                        #')
                print('#                M: No, copy file manually instead                             #')
                print('#                Q: Abort                                                      #')
                if not linux_files_available:
                    print('#    anything else: Yes, use these files for this build                        #')
                else:
                    print('#    anything else: Use the existing Linux files inside the Partition folder   #')
                print('------------------------------------------------------------------------------')
                __wait3__ = input('Type anything to continue ... ')
              
                if __wait3__ =='q' or __wait3__=='Q':
                    return False
                if __wait3__ =='y' or __wait3__=='Y':
                    yocto_project_available=True
                if __wait3__ =='m' or __wait3__=='M':
                    yocto_project_available=False
                    linux_files_available = False
            
        if yocto_project_available:
                print('--> Copy the Yocto Project files to the "'+IMAGE_FOLDER_NAME+'" folder')

                # Copy rootfs.tar.gz to the image partition folder
                print('    Copy "'+yocto_rootfs_name+'" and rename it to "rootfs.tar.gz"')
                try:
                    shutil.copy2(yocto_rootfs_dir,self.Ext_folder_dir+'/rootfs.tar.gz')
                except Exception as ex:
                    print('EROR: Failed to copy the rootfs file! MSG: '+str(ex))
                    return False
                
                # Copy compressed Kernel image to the image partition folder
                print('    Copy "'+yocto_zimage_name+'" and rename it to "zImage"')
                try:
                    shutil.copy2(yocto_zimage_dir,self.Vfat_folder_dir+'/zImage')
                except Exception as ex:
                    print('EROR: Failed to copy the zImage file! MSG: '+str(ex))
                    return False

                # Copy compressed Kernel image to the image partition folder
                if not yocto_devicetree_dir == '':
                    print('    Copy "'+yocto_devicetree_name+'" and rename it to "zImage"')
                    # NOTE: Work required!!
        elif linux_files_available:
            # Use the existing files 
            print('--> The existing Linux files inside the image folder will be used again')
        else:
            # Use the existing files 
            if copy_mode==0:
                print('--> Please copy the files manually to the Image folder')
                __wait7__ = input('Type anything to continue ... ')
                if __wait3__ =='q' or __wait3__=='Q':
                    sys.exit()

    ################################## Create the bootloader configuration file "extlinux.conf" ################################### 
        '''
        if not os.path.isfile(self.Vfat_folder_dir+'/extlinux/extlinux.conf'):
            print('--> Create boot configuration file "extlinux.conf" ')
            if not os.path.isdir(self.Vfat_folder_dir+'/extlinux'):
                os.mkdir(self.Vfat_folder_dir+'/extlinux')

            with open(self.Vfat_folder_dir+'/extlinux/extlinux.conf', "a") as f:
                f.write('LABEL Linux Default\n')
                f.write('   KERNEL ../zImage\n')
                f.write('   FDT ../socfpga_cyclone5_socdk.dtb\n')
                f.write('   APPEND root=/dev/mmcblk0p2 rw rootwait earlyprintk console=ttyS0,115200n8\n')
        '''

    ############################################ Create the u-boot script "boot.script" ########################################## 
        if not os.path.isfile(self.Vfat_folder_dir+'/boot.scr'):
            print('--> Copy the default "boot.script" partition')
            if self.Uboot_default_file_dir == '':
                print('ERROR: There is no default u-boot script file available!')
                print('       Please insert an own "boot.script" file to')
                print('       the VFAT/FAT partition')
                return False
            try:
                shutil.copy2(self.Uboot_default_file_dir,self.Vfat_folder_dir+'/boot.script')
            except Exception as ex:
                print('ERROR: Failed to copy the u-boot script file MSG: '+str(ex))
        return True

    #
    #
    # @brief Create a FPGA configuration file for configure the FPGA during boot or with Linux in case this
    #        feature was selected inside the u-boot script
    # @param copy_file             Only copy and rename a existing rbf file 
    # @param dir2copy              Directory with the rbf file to copy 
    # @param boot_linux            Generate configuration for
    #                              False : Writen during boot (Passive Parallel x8; 
    #                                      File name: <as in uboot script>.rbf)
    #                              True  : Can be written by Linux (Passive Parallel x16;
    #                                      File name: <as in uboot script>_linux.rbf)
    # @param linux_filename        ".rfb" output file name for the configuration with Linux 
    # @param linux_copydir         the location where the output Linux FPGA configuration file should be copied 
    # @return                      success
    #
    def GenerateFPGAconf(self,copy_file=False,dir2copy='',boot_linux =False, linux_filename='', linux_copydir=''):
        print(' --> Check if it is necessary to generate a FPGA configuration file ')
        # Check if a FPGA configuration binary generation is necessary
        # -> Only in case the u-boot script was configured to write the FPGA configuration  
        if os.path.isfile(self.Vfat_folder_dir+'/boot.script'):

            rbf_config_name_found =''
            rbf_config_found =False
            gen_fpga_conf=False
            # 1. Find a rbf file inside the VFAT partition
            if not boot_linux:
                print('    Scan VFAT partition for a ".rbf" FPGA config file')
                for file in os.listdir(self.Vfat_folder_dir):
                    if os.path.isfile(self.Vfat_folder_dir+'/'+file) and file.endswith('.rbf'):
                        if rbf_config_found:
                            print('Note: There are more than one ".rbf" configuration file')
                            print('      inside the VFAT partition available!')
                            print('      A new generation of the FPGA configuration is not possible')
                            rbf_config_name_found=''
                            return False
                        else:
                            rbf_config_name_found=file
                            rbf_config_found = True
                # 2.A. Rebuild an existing rbf file: Check that this file is used inside the u-boot script
                if rbf_config_found and not rbf_config_name_found=='':
                    print('    The file "'+rbf_config_name_found+'" found')
                    b = bytes(rbf_config_name_found, 'utf-8')
                    with open(self.Vfat_folder_dir+'/boot.script', 'rb', 0) as file, \
                    mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_READ) as s:
                        if s.find(b) != -1:
                            gen_fpga_conf = True
                    
                # Remove the old rbf file from the VFAT folder
                if self.unlicensed_ip_found==False or copy_file:    
                    try:
                        os.remove(self.Vfat_folder_dir+'/'+rbf_config_name_found)
                    except Exception:
                        print('ERROR: Failed to remove the old VFAT FPGA config file')
            else:
                if linux_filename=='' or linux_filename.find('.rbf')==-1:
                    print('Error: The selected Linux FPGA configuration file name is not vailed!')
                    sys.exit()
                if not os.path.isdir(linux_copydir):
                    print('Error: The selected Linux FPGA configuration file copy location is not a dir')
                    sys.exit()
                if os.path.isfile(linux_copydir+'/'+linux_filename):
                    print('    Remove the exsiting Linux FPGA configuration file')
                    try:
                        os.remove(linux_copydir+'/'+linux_filename)
                    except Exception:
                        print('ERROR: Failed to remove the old Linux FPGA config file from the selected dir')

            # 2.B. Build a new rbf file: Check if the u-boot script should write the FPGA configuration
            if not rbf_config_found and rbf_config_name_found=='':
                print('    No FPGA configuration file was found')
                print('    -> Check if the u-boot script should write the FPGA configuration')

                with open(self.Vfat_folder_dir+'/boot.script', 'rb', 0) as file:
                    for line in file:
                        line = str(line)
                        if not line.find('.rbf')==-1 and not line.startswith('#'):
                            rbf_end= line.find('.rbf')+4
                            rbf_start=0
                            for i in range(rbf_end,0,-1):
                                if line[i] ==' ':
                                    rbf_start = i+1
                                    break
                            if i > 3:
                                gen_fpga_conf = True
                                if boot_linux:
                                    rbf_config_name_found = linux_filename
                                else:
                                    rbf_config_name_found = line[rbf_start:rbf_end]
                                
                                    

            if self.unlicensed_ip_found==True and not copy_file: 
                print('\n#############################################################################')
                print('#        Your Quartus Prime project contains unlicend demo IPs               #')
                print('#                                                                            #')
                print('#                                                                            #')
                print('#              For this project a generation of a  FPGA                      #')
                print('#                 configuration file is not possible.                        #')
                print('#                                                                            #')
                print('#               Please insert a different ".rbf" file                        #')
                print('#   File name: "'+rbf_config_name_found+'"                                   #')
                print('#   Directory: "'+self.Vfat_folder_dir+'/'+rbf_config_name_found+'"          #')
                print('#                                                                            #')
                print('#        Q: Quit the script                                                  #')
                print('#        Any other input: Continue with the generation                       #')
                print('#                                                                            #')
                print('##############################################################################')
                _wait_ = input('#              Please type ...                                               #\n')
                if _wait_ == 'q' or _wait_ == 'Q':
                    sys.exit()

            # 3.a Generate the FPGA configuration file
            if gen_fpga_conf and not copy_file:
                if self.Sof_folder =='':
                    sof_file_dir = self.Quartus_proj_top_dir
                else:
                    sof_file_dir = self.Quartus_proj_top_dir+'/'+self.Sof_folder

                # Remove the old rbf file from the Quartus project top folder
                if os.path.isfile(sof_file_dir+'/'+rbf_config_name_found):
                    try:
                        os.remove(sof_file_dir+'/'+rbf_config_name_found)
                    except Exception:
                        print('ERROR: Failed to remove the old project folder FPGA config file')

                try:
                    with subprocess.Popen(self.EDS_Folder+'/'+EDS_EMBSHELL_DIR, stdin=subprocess.PIPE) as edsCmdShell:
                        time.sleep(DELAY_MS)
                        if not boot_linux:
                            print(' --> Generate a new FPGA configuration file for writting during boot')
                            print('     with the output name "'+rbf_config_name_found+'"')

                            b = bytes(' cd '+sof_file_dir+' \n', 'utf-8')
                            edsCmdShell.stdin.write(b) 
                            
                            b = bytes('quartus_cpf -c '+self.Sof_file_name+' '+rbf_config_name_found+' \n','utf-8')
                            edsCmdShell.stdin.write(b) 
                        else:
                            print(' --> Generate a new FPGA configuration file for writting with the HPS (Linux)')
                            print('     with the output name "'+rbf_config_name_found+'"')

                            b = bytes(' cd '+sof_file_dir+' \n', 'utf-8')
                            edsCmdShell.stdin.write(b) 
                            
                            b = bytes('quartus_cpf -m FPP -c '+self.Sof_file_name+' '+rbf_config_name_found+' \n','utf-8')
                            edsCmdShell.stdin.write(b) 

                        edsCmdShell.communicate()
                        time.sleep(DELAY_MS)
                    
                except Exception as ex:
                    print('ERROR: Failed to start the Intel EDS Command Shell! MSG:'+ str(ex))
                    return False

                 # Check that the generated rbf configuration file is now available
                if not os.path.isfile(sof_file_dir+'/'+rbf_config_name_found):
                    print('ERROR: Failed to generate the FPGA configuration file')
                    return False

                if not boot_linux:
                    ## For the uboot FPGA configuration file  
                    # Copy the file to the VFAT folder
                    try:
                        shutil.move(sof_file_dir+'/'+rbf_config_name_found,  \
                            self.Vfat_folder_dir+'/')
                    except Exception as ex:
                        print('ERROR: Failed to move the rbf configuration '+ \
                            'file to the vfat folder MSG:'+str(ex))
                        return False
                    print('    A new FPGA for configuration during boot was generated ')
                else:
                    ## For the Linux (HPS) FPGA configuration file  
                    # Copy the file to the rootfs /hoome folder folder
                    try:
                        shutil.move(sof_file_dir+'/'+rbf_config_name_found,  \
                            linux_copydir+'/')
                    except Exception as ex:
                        print('ERROR: Failed to move the rbf Linx configuration '+ \
                            'file to the selected folder MSG:'+str(ex))
                        return False
                    print('    A new FPGA configuration with Linux was generated ')

            # 3.b Copy an existing FPGA configuration to the partition
            elif gen_fpga_conf and copy_file:
                print(' --> Copy an existing FPGA configuration file to the partition')
                
                # Check that the rbf configuration file is available
                if not os.path.isfile(dir2copy):
                    print('ERROR: The file to copy does not exist!')
                    return False

                # Copy the file to the VFAT folder
                try:
                    if not boot_linux:
                        shutil.copy2(dir2copy,self.Vfat_folder_dir+'/'+ \
                            rbf_config_name_found)
                    else:
                        shutil.copy2(dir2copy,linux_copydir+'/'+ \
                            linux_filename)
                except Exception as ex:
                    print('ERROR: Failed to copy the rbf configuration '+ \
                        'file to the vfat folder MSG:'+str(ex))
                    return False
                print('    The new FPGA configuration file was inserted!')
            else:
                print('NOTE: It was no new FPGA configuration file generated!')
        return True

    #
    #
    # @brief Scan every Partition folder and unpackage all archive files such as the rootfs
    # @return                      success
    #
    def ScanUnpackagePartitions(self):

    ################################## Scan the partition folders to list all directories #######################################
        print('\n---> Scan every partition folder to find all file directories')
        print('      and calculate the total partition size')
        try:
            for part in self.PartitionList:
                # List every file inside the folder
                part.findFileDirectories(True,os.getcwd()+'/'+IMAGE_FOLDER_NAME+'/'+part.giveWorkingFolderName(False), \
                                         False,True)
        except Exception as ex:
            print(' ERROR: Failed to calculate the total partition size')
            print(' Msg.: '+str(ex))
            return False
        return True
    #
    #
    # @brief Generate a bootable Image file for the selected 
    #        feature was selected inside the u-boot script
    # @param ImageFileName         Name of the output ".img" image file
    # @param OutputZipFileName     Name of the output ".zip" compressed image file
    # @param compress_output       Compress the output image file to ".zip"
    # @param print_Table           Print the partatition table 
    # @return                      success
    #
    def GenerateImageFile(self,ImageFileName='',OutputZipFileName='', compress_output=False, \
                            print_Table= False):

        # Add a datecode to the output file names
        now = datetime.now()
        dt_string = now.strftime("%Y%m%d_%H%M")

        # Use the default name "SocfpgaLinux.img" as output file name
        if ImageFileName=='':
            self.ImageFileName   = "SocfpgaLinux"+dt_string+".img"
        else:
            self.ImageFileName = ImageFileName
        if OutputZipFileName=='':
            self.OutputZipFileName= "SocfpgaLinux"+dt_string+".zip"
        else: 
            self.OutputZipFileName = OutputZipFileName
        
        print('---> Calculate Partition sizes and the total size')
        try:
            for part in self.PartitionList:
                # List every file inside the folder
                part.findFileDirectories(True,os.getcwd()+'/'+IMAGE_FOLDER_NAME+'/' \
                            +part.giveWorkingFolderName(False),True,False)
                # Calculate the total file size of the partition 
                part.calculatePartitionFilesize(True)
        except Exception as ex:
            print(' ERROR: Failed to calculate the total partition size')
            print(' Msg.: '+str(ex))
            return False
    
    ################################# Insert the partition table to the BootImageCreator ######################################
        print('---> Insert the partition list to the image generator') 
        try:
            self.BootImageCreator = BootImageCreator(self.PartitionList,str(self.ImageFileName),os.getcwd())
        except Exception as ex:
            print(' ERROR: Failed to load the items of the XML file')
            print(' Msg.: '+str(ex))
            return False

        ############################################# Print the partition table ###################################################
        if print_Table:
            print('-> Print the loaded Partition table')
            self.BootImageCreator.printPartitionTable()

            _wait2_ = input('Start generating the image by typing anything to continue ... (q/Q for quit) ')
            if _wait2_ == 'q' or _wait2_ == 'Q':
                sys.exit()

    ############################################# Create the new Image File ###################################################
        self.BootImageCreator.generateImage()

    ############################# Print the Partition table of the image file with "fdisk" #####################################
        self.BootImageCreator.printFinalPartitionTable()

        if compress_output:
            print('---> Compress the output image as .zip')
            self.BootImageCreator.compressOutput(True,self.OutputZipFileName)
        return True


############################################                                ############################################
############################################             MAIN               ############################################
############################################                                ############################################

if __name__ == '__main__':
    print('\n##############################################################################')
    print('#                                                                            #')
    print('#    ########   ######     ##    ##  #######   ######  ########  #######     #')        
    print('#    ##     ## ##    ##     ##  ##  ##     ## ##    ##    ##    ##     ##    #')          
    print('#    ##     ## ##            ####   ##     ## ##          ##    ##     ##    #')    
    print('#    ########   ######        ##    ##     ## ##          ##    ##     ##    #')   
    print('#    ##   ##         ##       ##    ##     ## ##          ##    ##     ##    #')  
    print('#    ##    ##  ##    ##       ##    ##     ## ##    ##    ##    ##     ##    #')    
    print('#    ##     ##  ######        ##     #######   ######     ##     #######     #') 
    print('#                                                                            #')
    print("#       AUTOMATIC SCRIPT TO COMBINE ALL FILES OF AN EMBEDDED LINUX TO A      #")
    print("#                       BOOTABLE DISTRIBUTABLE IMAGE FILE                    #")
    print('#                                                                            #')
    print("#               by Robin Sebastian (https://github.com/robseb)               #")
    print('#                          Contact: git@robseb.de                            #')
    print("#                            Vers.: "+version+"                                    #")
    print('#                                                                            #')
    print('##############################################################################\n\n')

    ############################################ Runtime environment check ###########################################

    # Check properly Python Version
    if sys.version_info[0] < 3:
        print('ERROR: This script can not work with your Python Version!')
        print("Use Python 3.x for this script!")
        sys.exit()

    # Check that the Version runs on Linux
    if not sys.platform =='linux':
        print('ERROR: This script works only on Linux!')
        print("Please run this script on a Linux Computer!")
        sys.exit()
        
    if os.geteuid() == 0:
        print('ERROR: This script can not run with root privileges!')
        sys.exit()

    ###################################### Run the SoC-FPGA Platform Generator  ###########################################

    # Read the execution environment 
    socfpgaGenerator = SocfpgaPlatformGenerator()

    # Create the partition table 
    if not socfpgaGenerator.GeneratePartitionTable():
        sys.exit()

    # Create the required bootloader
    if not socfpgaGenerator.BuildBootloader():
        sys.exit()

    # Copy the Linux Distribution files (rootfs,zImage,device Tree) to the partition
    if not socfpgaGenerator.CopyLinuxFiles2Partition():
        sys.exit()
    
    # Generate the depending FPGA configuration file 
    #    specified inside the u-boot script
    if socfpgaGenerator.unlicensed_ip_found==False:
        if not socfpgaGenerator.GenerateBootFPGAconf():
            sys.exit()

    print('\n#############################################################################')
    print('#    Copy files to the partition folders to allow the pre-installment         #')
    print('#                    to the depending image partition                         #')
    print('#                                                                             #')
    print('#                     === Folders for every partition ===                     #')
    for part in socfpgaGenerator.PartitionList:
        print('# Folder: "'+IMAGE_FOLDER_NAME+'/'+part.giveWorkingFolderName(False)+'"| No.: '+ \
                                str(part.id)+' Filesystem: '+part.type+' Size: '+str(part.size_str))
    print('#                                                                            #')
    print('##############################################################################')
    print('#                                                                            #')
    print('#                    Compress the output image file?                         #')
    print('#     Should the output file be compressed as .zip to reduce the size        #')
    print('#     Image creator tools like "Rufus" can directly work with .zip files     #')
    print('#                                                                            #')
    print('#        Y: Compress the output image as .zip                                #')
    print('#        Q: Quit the script                                                  #')
    print('#        Any other input: Do not compress the output image                   #')
    print('#                                                                            #')
    print('##############################################################################')
    _wait_ = input('#              Please type ...                                               #\n')
    if _wait_ == 'q' or _wait_ == 'Q':
        sys.exit()
    elif _wait_ =='Y' or _wait_ =='y':
        compress_output = True
    else:
        compress_output = False
    print('##############################################################################')

    # Unzip all available archive files such as the rootfs 
    if not socfpgaGenerator.ScanUnpackagePartitions():
        sys.exit()

    print('\n#############################################################################')
    print('#                                                                            #')
    print('#                    the rootfs is unpackaged                                #')
    print('#                                                                            #')
    print('#        At this point it is enabled to change the rootfs manually           #')
    print('#                                                                            #')
    print('#        Q: Quit the script                                                  #')
    print('#        Any other input: Continue with generation of the image              #')
    print('#                                                                            #')
    print('##############################################################################')
    _wait_ = input('#              Please type ...                                               #\n')
    if _wait_ == 'q' or _wait_ == 'Q':
        sys.exit()

    # Generate with the files inside the partition folder an Image file
    # Use a date code as an output file
    if not socfpgaGenerator.GenerateImageFile('','',compress_output,True):
        sys.exit()
    
############################################################ Goodby screen  ###################################################
    print('\n################################################################################')
    print('#                                                                              #')
    print('#                        GENERATION WAS SUCCESSFUL                             #')
    print('# -----------------------------------------------------------------------------#')
    print('#                                                                              #')
    print('#                            ROBIN SEBASTIAN                                   #')
    print('#                     (https://github.com/robseb/)                             #')
    print('#                            git@robseb.de                                     #')
    print('#                                                                              #')
    print('################################################################################')
# EOF
