#coding: utf-8
''' 升级记录
'''
__author__ = 'XIVN1987'

import sys, os
import _winreg
import shutil
import uuid

import xml.etree.ElementTree as et

import sip
sip.setapi('QString', 2)
from PyQt4 import QtCore, QtGui, uic


class MDK2VS2015(QtGui.QWidget):
    def __init__(self, parent=None):
        super(MDK2VS2015, self).__init__(parent)
        
        uic.loadUi('MDK2VS2015.ui', self)
        
        key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, 'Software\\Keil\\\xa6\xccVision4\\Recent Projects')
        for i in range(1, 11):
            value, type = _winreg.QueryValueEx(key, 'Project %d' %i)
            self.cmbMDK.insertItem(i, value)
    
    @QtCore.pyqtSlot()
    def on_btnMDK_clicked(self):
        mdkproj = QtGui.QFileDialog.getOpenFileName(self, caption=u'指定MDK项目文件', filter='MDK Project (*.uvproj)')
        if mdkproj:
            self.cmbMDK.insertItem(0, mdkproj)
    
    @QtCore.pyqtSlot()
    def on_btnGen_clicked(self):
        mdkproj = self.cmbMDK.currentText()
        
        mdkpath = mdkproj[:mdkproj.rindex('\\')+1]
        mdkname = mdkproj[mdkproj.rindex('\\')+1:mdkproj.rindex('.')]        
        
        shutil.copy(r'Template\Template.sln',             mdkpath+mdkname+'.sln')
        shutil.copy(r'Template\Template.vcxproj',         mdkpath+mdkname+'.vcxproj')
        shutil.copy(r'Template\Template.vcxproj.filters', mdkpath+mdkname+'.vcxproj.filters')
        shutil.copy(r'Template\Template.sdf',             mdkpath+mdkname+'.sdf')
        
        self.mdkproj = {'mdkproj': mdkproj, 'mdkpath': mdkpath, 'mdkname': mdkname}
        self.parse_mdkproj(mdkproj)
        
        self.repair_sln(mdkpath+mdkname+'.sln')
        self.repair_vcxproj(mdkpath+mdkname+'.vcxproj')
        self.repair_vcxproj_filters(mdkpath+mdkname+'.vcxproj.filters')
        
        QtGui.QMessageBox.information(self, u'生成VS项目成功', u'根据MDK项目文件自动生成Visual Studio 2015项目成功!  ')
    
    def repair_sln(self, vssln):
        text = open(vssln, 'r').read()
        file = open(vssln, 'w')
        file.write(text.replace('Template', self.mdkproj['mdkname'].encode('utf-8')))
        file.close()
    
    def repair_vcxproj(self, vsproj):
        et.register_namespace('', "http://schemas.microsoft.com/developer/msbuild/2003")
        tree = et.parse(vsproj)
        root = tree.getroot()
        
        group_c = et.SubElement(root, 'ItemGroup')
        group_a = et.SubElement(root, 'ItemGroup')
        
        for group in self.mdkproj['Groups']:
            for file in self.mdkproj['Groups'][group]:
                if file.endswith('.c'):
                    et.SubElement(group_c, 'ClCompile', attrib={'Include': self.mdkproj['Groups'][group][file]})
                elif file.endswith('.s'):
                    et.SubElement(group_a, 'None', attrib={'Include': self.mdkproj['Groups'][group][file]})
        
        key = _winreg.OpenKey(_winreg.HKEY_CLASSES_ROOT, 'UVPROJXFILE\\Shell\\open\\command')
        mdk_Uv4 = _winreg.QueryValue(key, '')
        mdk_inc = mdk_Uv4[1:mdk_Uv4.rindex('uVision')] + r'uVision\ARM\ARMCC\include'
        
        for group in root.iterfind('{http://schemas.microsoft.com/developer/msbuild/2003}PropertyGroup/{http://schemas.microsoft.com/developer/msbuild/2003}NMakeIncludeSearchPath'):
            group.text = mdk_inc + ';' + ';'.join(self.mdkproj['IncludePaths'])
        
        for group in root.iterfind('{http://schemas.microsoft.com/developer/msbuild/2003}PropertyGroup/{http://schemas.microsoft.com/developer/msbuild/2003}NMakePreprocessorDefinitions'):
            group.text = '__CC_ARM' + ';' + ';'.join(self.mdkproj['Defines'])
        
        for group in root.iterfind('{http://schemas.microsoft.com/developer/msbuild/2003}PropertyGroup/{http://schemas.microsoft.com/developer/msbuild/2003}NMakeBuildCommandLine'):
            group.text = self.mdkproj['TargetName'] + '.BAT'       
        
        for group in root.iterfind('{http://schemas.microsoft.com/developer/msbuild/2003}PropertyGroup/{http://schemas.microsoft.com/developer/msbuild/2003}NMakeCleanCommandLine'):
            group.text = ''
        
        for group in root.iterfind('{http://schemas.microsoft.com/developer/msbuild/2003}PropertyGroup/{http://schemas.microsoft.com/developer/msbuild/2003}NMakeReBuildCommandLine'):
            group.text = self.mdkproj['TargetName'] + '.BAT'       
        
        tree.write(vsproj, encoding='utf-8')
    
    def repair_vcxproj_filters(self, vsprojfilt):
        et.register_namespace('', "http://schemas.microsoft.com/developer/msbuild/2003")
        tree = et.parse(vsprojfilt)
        root = tree.getroot()
        
        self.vsgrps = []
        for group in self.mdkproj['Groups']:
            vsgrps = []
            words = group.split('/') if group.count('/') else group.split('\\')
            for n in range(1, len(words)+1):
                vsgrp = ''
                for i in range(0, n):
                    vsgrp = vsgrp + words[i] + '\\'
                vsgrps.append(vsgrp[:-1])
                            
            for vsgrp in vsgrps:
                if not self.vsgrps.count(vsgrp):
                    self.vsgrps.append(vsgrp)
        
        for vsgrp in self.vsgrps:
            filters = root.find('{http://schemas.microsoft.com/developer/msbuild/2003}ItemGroup')
            filter = et.SubElement(filters, 'Filter', attrib={'Include': u"源文件\\" + vsgrp})
            UniqueIdentifier = et.SubElement(filter, 'UniqueIdentifier')
            UniqueIdentifier.text='{'+str(uuid.uuid1())+'}'
        
        group_c = et.SubElement(root, 'ItemGroup')
        group_a = et.SubElement(root, 'ItemGroup')
        
        for group in self.mdkproj['Groups']:
            for file in self.mdkproj['Groups'][group]:
                if file.endswith('.c'):
                    item = et.SubElement(group_c, 'ClCompile', attrib={'Include': self.mdkproj['Groups'][group][file]})
                    Filter = et.SubElement(item, 'Filter')
                    Filter.text = u"源文件\\" + group.replace('/', '\\') if group.count('/') else u"源文件\\" + group
                elif file.endswith('.s'):
                    item = et.SubElement(group_a, 'None', attrib={'Include': self.mdkproj['Groups'][group][file]})
                    Filter = et.SubElement(item, 'Filter')
                    Filter.text = u"源文件\\" + group.replace('/', '\\') if group.count('/') else u"源文件\\" + group
        
        tree.write(vsprojfilt, encoding='utf-8')
    
    def parse_mdkproj(self, mdkproj):
        root = et.parse(mdkproj).getroot()
        
        self.mdkproj['TargetName'] = root.find('Targets/Target/TargetName').text
        
        defines = root.find('Targets/Target/TargetOption/TargetArmAds/Cads/VariousControls/Define').text
        self.mdkproj['Defines'] = defines.split() if defines else []
        
        incdirs = root.find('Targets/Target/TargetOption/TargetArmAds/Cads/VariousControls/IncludePath').text
        self.mdkproj['IncludePaths'] = incdirs.split() if incdirs else []
        
        self.mdkproj['Groups'] = {}
        for group in root.find('Targets/Target/Groups').iterfind('Group'):
            groupName = group.find('GroupName').text
            self.mdkproj['Groups'][groupName] = {}
            for file in group.find('Files').iterfind('File'):
                self.mdkproj['Groups'][groupName][file.find('FileName').text] = file.find('FilePath').text


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    win = MDK2VS2015()
    win.show()
    app.exec_()
