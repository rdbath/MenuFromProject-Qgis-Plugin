﻿"""
/***************************************************************************
Name            : menu_from_project plugin
Description          : Build layers shortcut menu based on QGis project
Date                 :  10/11/2011 
copyright            : (C) 2011 by AEAG
email                : xavier.culos@eau-adour-garonne.fr 
***************************************************************************/

/***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************/

@todo: alerte si le projet est configuré <Paths><Absolute>False 

"""
# Import the PyQt and QGIS libraries
import os
import sys
from qgis.core import *

from PyQt4 import QtWebKit
from PyQt4.QtCore import * 
from PyQt4.QtGui import *
from PyQt4 import QtXml
from ui_browser import Ui_browser

from menu_conf_dlg import menu_conf_dlg

# Initialize Qt resources from file resources.py
import resources


class menu_from_project: 

    def __init__(self, iface):
        self.path = QFileInfo(os.path.realpath(__file__)).path()
        self.iface = iface
        self.toolBar = None
        
        # new multi projects var
        self.projects = []
        self.menubarActions = []
        self.canvas = self.iface.mapCanvas()
        self.optionTooltip = (False)
        self.optionCreateGroup = (False)
        self.optionLoadAll = (False)
        self.read()       
        
        # default lang
        locale = QSettings().value("locale/userLocale")
        self.myLocale = locale[0:2]
        # dictionnary
        localePath = self.path+"/i18n/menu_from_project_" + self.myLocale + ".qm"
        # translator
        if QFileInfo(localePath).exists():
            self.translator = QTranslator()
            self.translator.load(localePath)
            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

    def store(self):
        s = QSettings()
        s.remove("menu_from_project/projectFilePath")

        index = 0
        
        s.setValue("menu_from_project/optionTooltip", (self.optionTooltip))
        s.setValue("menu_from_project/optionCreateGroup", (self.optionCreateGroup))
        s.setValue("menu_from_project/optionLoadAll", (self.optionLoadAll))
        
        s.beginWriteArray("menu_from_project/projects")
        for project  in self.projects:
            s.setArrayIndex(index)
            s.setValue("file", project["file"])
            s.setValue("name", project["name"])
            index = index + 1
            
        s.endArray()

    def read(self):
        s = QSettings()
        #try:
        # old single project conf         
        filePath = s.value("menu_from_project/projectFilePath", "")
        
        #QgsMessageLog.logMessage('-'+filePath+'-', 'Extensions')
        
        if (filePath != "" and filePath != None):
            title = str(filePath).split('/')[-1]
            title = str(title).split('.')[0]
            self.projects.append({"file":filePath, "name":title})
            self.store()
        else:
            # patch : lecture ancienne conf
            size = s.beginReadArray("projects")
            for i in range(size):
                s.setArrayIndex(i)
                file = ((s.value("file").toString()))
                name =((s.value("name").toString()))
                if file != "":
                    self.projects.append({"file":file, "name":(name)})
            s.endArray()

            size = s.beginReadArray("menu_from_project/projects")
            #QgsMessageLog.logMessage(str(size), 'Extensions')
            for i in range(size):
                s.setArrayIndex(i)
                file = s.value("file", "")
                name = s.value("name", "")
                #QgsMessageLog.logMessage(name, 'Extensions')
                if file != "":
                    self.projects.append({"file":file, "name":name})
                    
            s.endArray()
        
        self.optionTooltip = s.value("menu_from_project/optionTooltip", (True), type=bool)
        
        # create group option only since 1.9
        self.optionCreateGroup = s.value("menu_from_project/optionCreateGroup", (False), type=bool)
            
        self.optionLoadAll = s.value("menu_from_project/optionLoadAll", (False), type=bool)
        
        #except:
        #    pass
        
    def isAbsolute(self, doc):
        absolute = False
        try:
            props = doc.elementsByTagName("properties")
            if props.count()==1:
                node = props.at(0)
                pathNode = node.namedItem("Paths")
                absoluteNode = pathNode.namedItem("Absolute")
                absolute = ("true" == absoluteNode.firstChild().toText().data())
        except:
            pass
        
        return  absolute

    def _actionHovered(self, action): 
        tip = action.toolTip() 
        if (tip != "-"):
            QToolTip.showText(QCursor.pos(), tip)
        else: 
            QToolTip.hideText()
      
    def getMaplayerDomFromQgs(self, fileName, layerId):
        xml = file(unicode(fileName)).read()
        doc = QtXml.QDomDocument()
        doc.setContent(xml)

        maplayers = doc.elementsByTagName("maplayer")
        for i in range(maplayers.size()):
            ml = maplayers.item(i)
            idelt = ml.toElement().elementsByTagName("id")
            id = ""
            
            if (idelt != None):
                id = idelt.item(0).toElement().text()
            
            if (id == layerId):
                return m1
            
            return None
        
    def addMenuItem(self, filename, node, menu, domdoc):
        yaLayer = False
        initialFilename = filename
        
        if node == None:
            return yaLayer
            
        element = node.toElement()
        
        absolute = self.isAbsolute(domdoc)
        projectpath = QFileInfo(os.path.realpath(filename)).path()

        # if legendlayer tag
        if element.tagName() == "legendlayer":
            try:
                legendlayerfiles = node.toElement().elementsByTagName("legendlayerfile")
                legendlayerfile = legendlayerfiles.item(0)
                layerId = legendlayerfile.toElement().attribute("layerid")
                action = QAction(element.attribute("name"), self.iface.mainWindow())
                
                if (self.optionTooltip == (True)): 
                    try:
                        maplayers = domdoc.elementsByTagName("maplayer")
                        # @todo: optimization
                        for i in range(maplayers.size()):
                            ml = maplayers.item(i)
                            idelt = ml.toElement().elementsByTagName("id")
                            id = ""
                            
                            if (idelt != None):
                                id = idelt.item(0).toElement().text()
                            
                            attrEmbedded = ml.toElement().attribute("embedded", "0")
                            if (attrEmbedded == "1"):
                                id = ml.toElement().attribute("id", "")
                                
                            if (id == layerId):
                                # embedded layers ?
                                if (attrEmbedded == "1"):
                                    embeddedFilename = ml.toElement().attribute("project", "")
                                    # read embedded project
                                    if not absolute and (embeddedFilename.find(".")==0):
                                        embeddedFilename = projectpath + "/" + embeddedFilename
                                        QgsMessageLog.logMessage('addMenuItem '+embeddedFilename, 'Extensions')

                                    ml = self.getMaplayerDomFromQgs(embeddedFilename, id)
                                    filename = embeddedFilename
                            
                                if ml != None:
                                    #QgsMessageLog.logMessage("m1 ok", 'Extensions')
                                    try:
                                        title = ml.toElement().elementsByTagName("title").item(0).toElement().text()
                                        #QgsMessageLog.logMessage(title, 'Extensions')
                                            
                                        abstract = ml.toElement().elementsByTagName("abstract").item(0).toElement().text()
                                        action.setStatusTip(title)
                                        if (abstract != "") and (title == ""):
                                            action.setToolTip("<p>"+abstract+"</p>")
                                        else:
                                            if (abstract != "" or title != ""):
                                                action.setToolTip("<b>"+title + "</b><br/>" + abstract)
                                            else:
                                                action.setToolTip("-")
                                    except:
                                        #raise
                                        pass
                                    
                                break
                    except:
                        #raise
                        pass
                
                menu.addAction(action)
                yaLayer = True
                helper = lambda _filename,_who,_menu: (lambda: self.do_aeag_menu(_filename, _who, _menu))
                action.triggered.connect(helper(filename, layerId, menu))
            except:
                #raise
                pass
            
            node = node.nextSibling()
            if (node != None):
                # ! recursion
                self.addMenuItem(initialFilename, node, menu, domdoc)
        # / if element.tagName() == "legendlayer":
                
        # if legendgroup tag
        if element.tagName() == "legendgroup":
            name = element.attribute("name")
            if name == "-":
                menu.addSeparator()
                node = node.nextSibling()
                if (node != None):
                    # ! recursion
                    self.addMenuItem(initialFilename, node, menu, domdoc)

            elif name.startswith("-"):
                action = QAction(name[1:], self.iface.mainWindow())
                font = QFont()
                font.setBold(True)
                action.setFont(font)
                menu.addAction(action) 

                nextNode = node.nextSibling()
                if (nextNode != None):
                    # ! recursion
                    self.addMenuItem(initialFilename, nextNode, menu, domdoc)
                    
            else:
                # construire sous-menu
                sousmenu = menu.addMenu('&'+element.attribute("name"))
                sousmenu.menuAction().setToolTip("-")

                childNode = node.firstChild()

                #  ! recursion
                r = self.addMenuItem(initialFilename, childNode, sousmenu, domdoc)

                if r and self.optionLoadAll and (len(sousmenu.actions()) > 1):
                    action = QAction(QApplication.translate("menu_from_project", "&Load all", None, QApplication.UnicodeUTF8), self.iface.mainWindow())
                    font = QFont()
                    font.setBold(True)
                    action.setFont(font)
                    sousmenu.addAction(action) 
                    helper = lambda _filename,_who,_menu: (lambda: self.do_aeag_menu(_filename, _who, _menu))
                    action.triggered.connect(helper(None, None, sousmenu))
                
                nextNode = node.nextSibling()
                if (nextNode != None):
                    # ! recursion
                    self.addMenuItem(initialFilename, nextNode, menu, domdoc)
        # / if element.tagName() == "legendgroup":
                   
        return yaLayer
    
    def addMenu(self, name, filename, domdoc):
        # main project menu
        menuBar = self.iface.editMenu().parentWidget()
        projectMenu = QMenu('&'+name, menuBar)
        
        if (self.optionTooltip == (True)): 
            projectMenu.hovered.connect(self._actionHovered)

        projectAction = menuBar.addMenu(projectMenu)
        self.menubarActions.append(projectAction);

        # build menu on legend schema
        legends = domdoc.elementsByTagName("legend")
        if (legends.length() > 0):
            node = legends.item(0)
            if (node != None):
                node = node.firstChild()
                self.addMenuItem(filename, node, projectMenu, domdoc)

    def initMenus(self):
        menuBar = self.iface.editMenu().parentWidget()
        for action in self.menubarActions:
            #QMessageBox.information(None, "Cancel", str("del"))
            menuBar.removeAction(action)
            del(action)
            
        self.menubarActions = []

        for project in self.projects:
            #QMessageBox.information(None, "Cancel", str("open " + _toAscii(project["name"])))
            try:
                xml = file(unicode(project["file"])).read()
                doc = QtXml.QDomDocument()
                doc.setContent(xml)
                
                self.addMenu(project["name"], project["file"], doc)
            except:
                #raise
                QgsMessageLog.logMessage('Menu from layer : invalid ' + str(project["file"]), 'Extensions')
                pass
        
    def initGui(self):          
        self.act_aeag_menu_config = QAction(QApplication.translate("menu_from_project", "Projects configuration", None, QApplication.UnicodeUTF8)+"...", self.iface.mainWindow())
        self.iface.addPluginToMenu(QApplication.translate("menu_from_project", "&Layers menu from project", None, QApplication.UnicodeUTF8), self.act_aeag_menu_config)
        # Add actions to the toolbar
        self.act_aeag_menu_config.triggered.connect(self.do_aeag_menu_config)

        self.act_aeag_menu_help = QAction(QApplication.translate("menu_from_project", "Help", None, QApplication.UnicodeUTF8)+"...", self.iface.mainWindow())
        self.iface.addPluginToMenu(QApplication.translate("menu_from_project", "&Layers menu from project", None, QApplication.UnicodeUTF8), self.act_aeag_menu_help)
        self.act_aeag_menu_help.triggered.connect(self.do_help)
        
        # build menu
        self.initMenus()


    def unload(self):
        menuBar = self.iface.editMenu().parentWidget()
        for action in self.menubarActions:
            menuBar.removeAction(action)

        self.iface.removePluginMenu(QApplication.translate("menu_from_project", "&Layers menu from project", None, QApplication.UnicodeUTF8), self.act_aeag_menu_config)
        self.iface.removePluginMenu(QApplication.translate("menu_from_project", "&Layers menu from project", None, QApplication.UnicodeUTF8), self.act_aeag_menu_help)
        self.act_aeag_menu_config.triggered.disconnect(self.do_aeag_menu_config)
        self.act_aeag_menu_help.triggered.disconnect(self.do_help)

        self.store()

    def do_aeag_menu_config(self):
        dlg = menu_conf_dlg(self.iface.mainWindow(), self)
        dlg.setModal(True)
        
        dlg.show()
        result = dlg.exec_()
        del dlg
        
        if result != 0:
            self.initMenus()

    # run method that performs all the real work
    def do_aeag_menu(self, filename, who, menu=None):
        self.canvas.freeze(True)
        self.canvas.setRenderFlag(False)
        idxGroup = None
        theLayer = None
        groupName = None

        try:
            if type(menu.parentWidget()) == QMenu and self.optionCreateGroup:
                groupName = menu.title().replace("&", "")

                idxGroup = self.iface.legendInterface().groups().index(groupName) if groupName in self.iface.legendInterface().groups() else -1
                
                if idxGroup < 0:
                    idxGroup = self.iface.legendInterface().addGroup(groupName, True)
    
            # load all layers
            if filename == None and who == None and self.optionLoadAll:
                i = 0
                for action in reversed(menu.actions()):
                    if action.text() != QApplication.translate("menu_from_project", "&Load all", None, QApplication.UnicodeUTF8):
                        action.trigger()
            else:
                # read QGis project
                xml = file(unicode(filename)).read()
                doc = QtXml.QDomDocument()
                doc.setContent(xml)

                # is project in relative path ?                
                absolute = self.isAbsolute(doc)

                layers = doc.elementsByTagName("maplayer")
                i=0
                while i<layers.count():
                    node = layers.at(i)
                    idNode = node.namedItem("id")
                    if idNode != None:
                           
                        id = idNode.firstChild().toText().data()
                        # layer founds
                        if id == who:
                            # give it a new id (for multiple import)
                            import uuid
                            newLayerId = QUuid.createUuid().toString()
                            idNode.firstChild().toText().setData(newLayerId)

                            # if relative path, adapt datasource
                            if not absolute:
                                try:
                                    datasourceNode = node.namedItem("datasource")
                                    datasource = datasourceNode.firstChild().toText().data()
                                    providerNode = node.namedItem("provider")
                                    provider = providerNode.firstChild().toText().data()
                                
                                    if provider == "ogr" and (datasource.find(".")==0):
                                        projectpath = QFileInfo(os.path.realpath(filename)).path()
                                        newlayerpath = projectpath + "/" + datasource 
                                        datasourceNode.firstChild().toText().setData(newlayerpath)
                                except:
                                    #raise
                                    pass
                            
                            # read modified layer node
                            QgsProject.instance().read(node)
                                    
                            if self.optionCreateGroup:
                                theLayer = QgsMapLayerRegistry.instance().mapLayer(newLayerId)
                                
                                if idxGroup >= 0 and theLayer != None:
                                    self.iface.mainWindow().statusBar().showMessage("Move to group "+str(idxGroup))
                                    self.iface.legendInterface().refreshLayerSymbology(theLayer)
                                    self.iface.legendInterface().moveLayer(theLayer, idxGroup)
                                    self.iface.legendInterface().refreshLayerSymbology(theLayer)
                                #else:
                                #    if idxGroup == 0:
                                #        self.iface.mainWindow().statusBar().showMessage("Group not found ?")
                                #    if theLayer == None:
                                #        self.iface.mainWindow().statusBar().showMessage("Layer not found ?")
                                    
                            break
                            
                    i=i+1        
        except:
            #raise
            QgsMessageLog.logMessage('Menu from layer : invalid ' + filename, 'Extensions')
            pass
        
        self.canvas.freeze(False)    
        self.canvas.setRenderFlag(True)
        self.canvas.setDirty(True)
        #self.canvas.refresh()    
        
    def do_help(self):
        try:
            self.hdialog = QDialog()
            self.hdialog.setModal(True)
            self.hdialog.ui = Ui_browser()
            self.hdialog.ui.setupUi(self.hdialog)
            
            if os.path.isfile(self.path+"/help_"+self.myLocale+".html"):
                self.hdialog.ui.helpContent.setUrl(QUrl(self.path+"/help_"+self.myLocale+".html"))
            else:
                self.hdialog.ui.helpContent.setUrl(QUrl(self.path+"/help.html"))

            self.hdialog.ui.helpContent.page().setLinkDelegationPolicy(QtWebKit.QWebPage.DelegateExternalLinks) # Handle link clicks by yourself
            self.hdialog.ui.helpContent.linkClicked.connect(self.doLink)
            
            self.hdialog.ui.helpContent.page().currentFrame().setScrollBarPolicy(Qt.Vertical, Qt.ScrollBarAlwaysOn)
            
            self.hdialog.show()
            result = self.hdialog.exec_()
            del self.hdialog
        except:
            QgsMessageLog.logMessage(sys.exc_info()[0], 'Extensions')
            #
            pass
        
    def doLink( self, url ):
        if url.host() == "" :
            self.hdialog.ui.helpContent.page().currentFrame().load(url)
        else:
            QDesktopServices.openUrl( url )