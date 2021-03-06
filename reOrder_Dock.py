# -*- coding: utf-8 -*-
"""
/***************************************************************************
 reOrderDock
                                Dock for reOrder script
 Option dock initialize
                             -------------------
        begin                : 2018-04-16
        last                 : 2017-04-16
        copyright            : (C) 2017 by Peillet Sebastien
        email                : peillet.seb@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
from datetime import datetime

from PyQt4.QtGui import QColor
from PyQt4 import QtGui, uic
from PyQt4.QtCore import pyqtSignal, QVariant
from PyQt4 import QtCore
from qgis.core import QgsVectorLayer, QgsVectorFileWriter, QgsVectorDataProvider, QgsField, \
                        QgsExpression, QgsFeatureRequest, QgsRasterPipe, QgsRasterFileWriter, \
                        QgsRectangle, QgsRasterLayer, QgsFeature, QgsPoint, QgsGeometry, QgsRaster, \
                        QgsCoordinateReferenceSystem

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'reOrderDock.ui'))


class Timer():
    """Processing timer"""

    startTimes = dict()
    stopTimes = dict()

    @staticmethod
    def start(key=0):
        """Start the timer"""
        Timer.startTimes[key] = datetime.now()
        Timer.stopTimes[key] = None

    @staticmethod
    def stop(key=0):
        """Stop the timer"""
        Timer.stopTimes[key] = datetime.now()

    @staticmethod
    def show(key=0):
        """Print computation time"""
        if key in Timer.startTimes:
            if Timer.startTimes[key] is not None:
                if key in Timer.stopTimes:
                    if Timer.stopTimes[key] is not None:
                        delta = Timer.stopTimes[key] - Timer.startTimes[key]
                        print 'Timer delta: %s' % delta

class ReorderProcess():
    """Along line point reordering

    according to given destination"""

    def __init__(self, exutoire, point_reseau):
        """Set all informations needed to order the network"""

        self.exutoire_layer = exutoire
        self.point_reseau_layer = point_reseau
        self.crs = QgsCoordinateReferenceSystem(self.point_reseau_layer.crs().authid())

        # Create ouput
        self.output = QgsVectorLayer("Point", "point", "memory")
        self.output.setCrs(self.crs)

        # Add fields
        name_T_id = "T_id"
        name_L_id = "L_id"
        name_P_id = "P_id"
        name_nat = "nature"
        provider = self.output.dataProvider()
        caps = provider.capabilities()
        if caps & QgsVectorDataProvider.AddAttributes:
            res = provider.addAttributes([QgsField(name_T_id, QVariant.String), QgsField(name_L_id, QVariant.String), QgsField(name_P_id, QVariant.String), QgsField(name_nat, QVariant.String)])
            self.output.updateFields()
        # Save field index
        self.index_nat = self.point_reseau_layer.fieldNameIndex('nature')
        self.index_pid = self.point_reseau_layer.fieldNameIndex('P_id')
        self.index_order = self.point_reseau_layer.fieldNameIndex('order')
        self.l_done = []


    def reorder(self, pt, count_order):

        feat = QgsFeature(self.output.pendingFields())
        pt_geom = pt.geometry()
        feat.setGeometry(pt_geom)

        tid = pt.attribute("T_id")
        lid = pt.attribute("L_id")
        ppid = pt.attribute("P_id")
        nat = pt.attribute("nature")

        if nat == 'start':
            self.output.startEditing()
            feat.setAttributes([tid, str(count_order), ppid, nat])
            print 'reorder: %s' % ([tid, lid, ppid, nat, str(count_order)])
            self.output.dataProvider().addFeatures([feat])
            self.output.commitChanges()
            self.output.updateExtents()
            while nat != 'end':
                expr = QgsExpression('L_id = %s and P_id = %s' % (lid, str(int(ppid) + 1)))
                req = QgsFeatureRequest(expr)
                n_pt_it = self.point_reseau_layer.getFeatures(req)
                n_pt = n_pt_it.next()
                n_pt_it = None

                feat = QgsFeature(self.output.pendingFields())
                n_pt_geom = n_pt.geometry()
                feat.setGeometry(n_pt_geom)

                tid = n_pt.attribute("T_id")
                lid = n_pt.attribute("L_id")
                ppid = n_pt.attribute("P_id")
                nat = n_pt.attribute("nature")

                self.output.startEditing()
                feat.setAttributes([tid, str(count_order), ppid, nat])
                print [tid, lid, ppid, nat, str(count_order)]
                self.output.dataProvider().addFeatures([feat])
                self.output.commitChanges()
                self.output.updateExtents()
        else:
            pid = 0
            self.output.startEditing()
            feat.setAttributes([tid, str(count_order), str(pid), 'start'])
            print [tid, lid, str(pid), 'start', str(count_order)]
            self.output.dataProvider().addFeatures([feat])
            self.output.commitChanges()
            self.output.updateExtents()
            nat = None
            feat = None
            while nat != 'start':
                ppid = str(int(ppid) - 1)
                expr = QgsExpression('L_id = %s and P_id = %s' % (lid, ppid))
                req = QgsFeatureRequest(expr)
                n_pt_it = self.point_reseau_layer.getFeatures(req)
                n_pt = n_pt_it.next()
                n_pt_it = None

                feat = QgsFeature(self.output.pendingFields())
                n_pt_geom = n_pt.geometry()
                feat.setGeometry(n_pt_geom)

                tid = n_pt.attribute("T_id")
                nat = n_pt.attribute("nature")
                if nat != 'start':
                    pid += 1
                    self.output.startEditing()
                    feat.setAttributes([tid, str(count_order), str(pid), nat])
                    print [tid, lid, str(pid), nat, str(count_order)]
                    self.output.dataProvider().addFeatures([feat])
                    self.output.commitChanges()
                    self.output.updateExtents()
                    feat = None
                else:
                    pid += 1
                    self.output.startEditing()
                    feat.setAttributes([tid, str(count_order), str(pid), 'end'])
                    print [tid, lid, str(pid), 'end', str(count_order)]
                    self.output.dataProvider().addFeatures([feat])
                    self.output.commitChanges()
                    self.output.updateExtents()
                    feat = None

    def executeReorder(self):

        count_order = 0
        # loop over exutoire features to process several network
        for exutoire in self.exutoire_layer.getFeatures():
            exutoire_geom = exutoire.geometry().buffer(1, 4).boundingBox()
            # Select the start point that intersects the outlet
            req = QgsFeatureRequest().setFilterRect(exutoire_geom)
            pts_reseau_sortie = self.point_reseau_layer.getFeatures(req)
            for pt_sortie in pts_reseau_sortie:
                count_order += 1
                L_id = pt_sortie.attribute("L_id")
                # Reorder the points of the first line of the network
                self.reorder(pt_sortie, count_order)
                nat = 'end'
                string = "L_id = %s AND nature = '%s'" % (count_order, nat)
                print string
                expr = QgsExpression(string)
                reque = QgsFeatureRequest(expr)
                # Select the last point of the first line
                pt_end_it = self.output.getFeatures(reque)
                pt_end = pt_end_it.next()
                pt_end_it = None
                # Make a buffer around the point to define a boundingBox
                pt_end_geom = pt_end.geometry().buffer(1, 4).boundingBox()
                req = QgsFeatureRequest(QgsExpression("L_id != %s" % (str(L_id)))).setFilterRect(pt_end_geom)
                # Select the next points
                next_ls = self.point_reseau_layer.getFeatures(req)
                self.l_done.append(L_id)
                list_next = []
                # Fill next_ls list with the next features
                for next_l in next_ls:
                    list_next.append(next_l)
                # While there is features in list_next, reorder process continues
                while len(list_next) != 0:
                    current_list = list_next
                    list_next = []
                    # Loop over the next features
                    for next_pt in current_list:
                        # Get line id
                        L_id = next_pt.attribute("L_id")
                        print L_id
                        # if the line has not been already reorder
                        if L_id not in self.l_done:
                            count_order += 1
                            #then reorder
                            self.reorder(next_pt, count_order)
                            string = "L_id = %s AND nature='%s'" % (count_order, nat)
                            print string
                            expr = QgsExpression(string)
                            req = QgsFeatureRequest(QgsExpression(expr))
                            pt_end_it = self.output.getFeatures(req)
                            pt_end = pt_end_it.next()
                            pt_end_it = None
                            pt_end_geom = pt_end.geometry().buffer(1, 4).boundingBox()
                            # Find the next feature
                            reque = QgsFeatureRequest(QgsExpression("L_id != %s" % (L_id))).setFilterRect(pt_end_geom)
                            next_ls = self.point_reseau_layer.getFeatures(reque)
                            self.l_done.append(L_id)
                            # Fill next_ls list again and loop
                            for next_l in next_ls:
                                list_next.append(next_l)
                    print len(list_next)

        expr = QgsExpression("nature = 'end'")
        req = QgsFeatureRequest(expr)
        end_pts = self.output.getFeatures(req)
        change_dict = {}
        change_list = []
        rm_ids = []
        #clean lines that aren't a cross border anymore because a small part has been removed
        for end_pt in end_pts:
            end_pt_geom = end_pt.geometry().buffer(1, 4).boundingBox()
            end_pt_id = end_pt.id()
            end_lid = end_pt.attribute("L_id")
            end_pid = end_pt.attribute("P_id")
            expr = QgsExpression("L_id != '%s'" % (end_lid))
            req = QgsFeatureRequest(expr).setFilterRect(end_pt_geom)
            int_pts = []
            for int_pt in self.output.getFeatures(req):
                lid_int_pt = int_pt.attribute("L_id")
                int_pts.append(int_pt)
            if len(int_pts) == 1:
                rm_ids.append(end_pt_id)
                if int(end_lid) in change_dict:
                    change_dict[int(lid_int_pt)] = change_dict[int(end_lid)]
                else:
                    change_dict[int(lid_int_pt)] = int(end_lid)
        print change_dict
        change_dict = sorted(change_dict.items(), key=lambda t: t[0])
        for ch_tuple in change_dict:
            print ch_tuple[0]
            end_lid = str(ch_tuple[1])
            end_pid = None
            for end_pt in self.output.getFeatures(QgsFeatureRequest(QgsExpression("L_id = '%s' and nature = '%s'" % (end_lid, "end")))):
                if end_pid is None:
                    end_pid = end_pt.attribute("P_id")
                elif int(end_pid) < int(end_pt.attribute("P_id")):
                    end_pid = end_pt.attribute("P_id")
            expr = QgsExpression("L_id = '%s'" % (str(ch_tuple[0])))
            req = QgsFeatureRequest(expr)
            for ch_pt in self.output.getFeatures(req):
                ch_pt_id = ch_pt.id()
                if ch_pt.attribute("nature") == "start":
                    rm_ids.append(ch_pt_id)
                else:
                    ch_tid = ch_pt.attribute("T_id")
                    ch_nature = ch_pt.attribute("nature")
                    self.output.startEditing()
                    self.output.changeAttributeValue(ch_pt_id, 1, end_lid)
                    self.output.changeAttributeValue(ch_pt_id, 2, end_pid)
                    self.output.commitChanges()
                    end_pid = int(end_pid) + 1
        self.output.startEditing()
        self.output.deleteFeatures(rm_ids)
        self.output.commitChanges()

        return self.output, self.crs

class reOrderDock(QtGui.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, iface, list_vect, list_vect_ind, parent=None):
        """Constructor."""
        super(reOrderDock, self).__init__(parent)
        self.setupUi(self)

        self.exutoire = None
        self.point_reseau = None
        self.list_vect = list_vect
        self.list_vect_ind = list_vect_ind

        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        self.initCombo()
        self.launchButton.clicked.connect(self.launchReOrder)
        self.canvas.layersChanged.connect(self.layersUpdate)
        self.connect(self, QtCore.SIGNAL('triggered()'), self.closeEvent)

    def closeEvent(self, event):
        """Close reOrder dock"""

        print "Closing re-order dock."
        self.close()

    def initCombo(self):
        """Initialize dock combo boxes"""
        self.reseauComboBox.addItems(self.list_vect)
        self.exutoireComboBox.addItems(self.list_vect)

    def layersUpdate(self):
        """Update layer list"""

        reseau_text = self.reseauComboBox.currentText()
        exe_text = self.exutoireComboBox.currentText()
        self.listVectLayer()
        reseau_ind = self.reseauComboBox.findText(reseau_text)
        exe_ind = self.exutoireComboBox.findText(exe_text)
        if reseau_ind != -1:
            self.reseauComboBox.setCurrentIndex(reseau_ind)
        if exe_ind != -1:
            self.exutoireComboBox.setCurrentIndex(exe_ind)
        return None

    def listVectLayer(self):
        """List line layer for the track selection"""

        # clear list and index
        self.reseauComboBox.clear()
        self.reseauComboBox.clearEditText()
        self.exutoireComboBox.clear()
        self.exutoireComboBox.clearEditText()

        self.list_vect = []
        self.list_vect_ind = []
        layers = self.iface.legendInterface().layers()
        index = 0
        for layer in layers:
            if layer.type() == 0:
                if layer.geometryType() == 0:
                    self.list_vect.append(layer.name())
                    self.list_vect_ind.append(index)
            index += 1
        self.reseauComboBox.addItems(self.list_vect)
        self.exutoireComboBox.addItems(self.list_vect)

    def launchReOrder(self):
        """Get the parameters and launch computation"""
        layers = self.iface.legendInterface().layers()
        selected_reseau_line = self.reseauComboBox.currentIndex()
        selected_exutoire_line = self.exutoireComboBox.currentIndex()
        self.point_reseau = layers[self.list_vect_ind[selected_reseau_line]]
        self.exutoire = layers[self.list_vect_ind[selected_exutoire_line]]
        self.output_path = self.outputEdit.text()
        l_done = []

        time = Timer()
        time.start()

        # Create ReorderProcess
        reorder_process = ReorderProcess(self.exutoire, self.point_reseau)
        # Launch computation
        output, crs = reorder_process.executeReorder()

        time.stop()
        print 're-order: processing Time:'
        time.show()

        error = QgsVectorFileWriter.writeAsVectorFormat(output, self.output_path, "utf-8", crs, "ESRI Shapefile")
        if error == QgsVectorFileWriter.NoError:
            print "re-order: Success!"
        out_layer = self.iface.addVectorLayer(self.output_path, "", "ogr")
        if not out_layer:
            print "re-order: Layer failed to load!"
