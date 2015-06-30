
import sip
# sip.setapi('QVariant', 2)
import numpy as np


import sys
# sys.path.append('E:/Merlin/Notebooks/')
import qd_tools as qd
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import QTime, QTimer, QDate, pyqtSignal
from scipy.interpolate import griddata

import mpltools.color as color

import pyqtgraph as pg
# import pyqtgraph.exporters
import pyqtgraph.dockarea as dockarea

# import shutil


# %load_ext autoreload
# %autoreload 2


# import os
# import time

def first_index(the_list, substring):
    for i, s in enumerate(the_list):
        if substring in s:
              return i
    return False

class PlotFrame(QtGui.QWidget):
    def __init__(self, parent=None):
        super(PlotFrame, self).__init__(parent)
        self.plotAxes = [0,1,2]
        self.display_num = 2

        self.area = dockarea.DockArea()

        layout = QtGui.QVBoxLayout()
        inputs = QtGui.QHBoxLayout()

        self.channel_model = QtGui.QStandardItemModel()
        self.display_model = QtGui.QStandardItemModel()
        c_x = pg.ComboBox()
        c_y = pg.ComboBox()
        c_z = pg.ComboBox()
        c_display = pg.ComboBox()
        self.combos = [c_x, c_y, c_z]
        for c in self.combos:
            c.setDuplicatesEnabled(True)
            c.setModel(self.channel_model)
            inputs.addWidget(c)
        inputs.addWidget(c_display)
        c_display.setModel(self.display_model)
        self.display_items = ['','Waterfall', '2d plot']
        for i in self.display_items:
            dItem = QtGui.QStandardItem(i)
            self.display_model.appendRow(dItem)
        c_display.setCurrentIndex(self.display_num)


        QtCore.QObject.connect(c_x, QtCore.SIGNAL('activated(int)'), self.ax0changed)
        QtCore.QObject.connect(c_y, QtCore.SIGNAL('activated(int)'), self.ax1changed)
        QtCore.QObject.connect(c_z, QtCore.SIGNAL('activated(int)'), self.ax2changed)
        QtCore.QObject.connect(c_display, QtCore.SIGNAL('activated(int)'), self.displayChanged)

        inputs.addWidget(QtGui.QPushButton('test'))
        layout.addWidget(self.area)
        layout.addLayout(inputs)
        self.setLayout(layout)

        self.plotDock = dockarea.Dock("Data", size=(500, 500))

        self.DataPlot = pg.PlotWidget()
        self.plotItem = self.DataPlot.getPlotItem()
        self.DataPlot.enableAutoRange('x', True)
        self.DataPlot.enableAutoRange('y', True)
        self.DataPlot.showGrid(x=1, y=1, alpha=0.5)
        # self.DataPlot.plot(data)

        self.area.addDock(self.plotDock, 'top')
        self.colorBar = pg.HistogramLUTWidget()
        self.plotDock.addWidget(self.DataPlot, 0, 0)
        self.plotDock.addWidget(self.colorBar, 0, 1)

    def axChanged(self, box, num):
        print(box, ': ', num)
        self.plotAxes[box] = num
        self.plotData()
        # print(self.combos[box].view)
        # print(c)
        # print (num)
        # print(self.channel_model.item(num).getChildren())

    def setPath(self, path):
        self.DataPlot.clear()
        # selected = [c.currentText() for c in self.combos]
        # print(selected)
        self.channel_model.clear()

        self.item = qd.dataItem(str(path))
        self.item.loadData()


        for value in self.item.sweeps:
            item = QtGui.QStandardItem(value)
            item.sweep = True
            self.channel_model.appendRow(item)

        for value in self.item.measures:
            item = QtGui.QStandardItem(value)
            item.sweep = False
            self.channel_model.appendRow(item)

        name_item = QtGui.QStandardItem('---')
        self.channel_model.appendRow(name_item)

        self.combos[0].setCurrentIndex(self.plotAxes[0])
        self.combos[1].setCurrentIndex(self.plotAxes[1])
        if self.plotAxes[2] == None:
            self.combos[2].setCurrentIndex(len(self.item.axes)+1)
        else:
            self.combos[2].setCurrentIndex(self.plotAxes[2])

        self.plotData()

    def plotData(self):
        self.DataPlot.clear()
        # self.plotItem = self.DataPlot.getPlotItem()
        pa = self.plotAxes

        an0 = self.ax_name(pa[0])
        an1 = self.ax_name(pa[1])
        an2 = self.ax_name(pa[2])
        if self.display_items[self.display_num] == 'Waterfall':
            grouped = self.item.groupby(an0)
            colors = np.array(255*color.colors_from_cmap(len(grouped), cmap='gnuplot', start=0.2, stop=0.8))
            colors = colors.astype(int)
            i = -1
            for label, data in grouped:
                i += 1
                pen = pg.mkPen(pg.mkColor(colors[i]))
                x = np.array(data[an1])
                y = np.array(data[an2])
                self.plotItem.plot(x, y, pen= pen)
        elif self.display_items[self.display_num] == '2d plot':
            data = self.item.data
            x= data[an0]
            y= data[an1]
            z= np.array(data[an2])

            # # define grid.
            nx = len(x.unique())
            ny = len(y.unique())
            # print(nx,ny)
            # nx = 512
            # ny = 500
            xi = np.linspace(min(x),max(x),nx)
            yi = np.linspace(min(y),max(y),ny)
            # grid the data.
            grid_z0 = griddata((x, y), z, (xi[None,:], yi[:,None]),method='nearest')

            img = pg.ImageItem(grid_z0.T)
            self.colorBar.setImageItem(img)
            self.plotItem.addItem(img)
        else:
            data = self.item.data
            x = data[an0]
            y = data[an1]
            self.plotItem.plot(x, y)

    def ax_name(self, number):
        return self.channel_model.item(number).text()

    def savePlot(self, fileName):
        # create an exporter instance, as an argument give it
        # the item you wish to export
        exporter = pg.exporters.ImageExporter(self.DataPlot.getPlotItem())
        # set export parameters if needed
        exporter.parameters()['width'] = 2048
        # save to file
        exporter.export(fileName)

    @QtCore.pyqtSlot("int")
    def ax0changed(self, num):
        self.axChanged(0, num)

    @QtCore.pyqtSlot("int")
    def ax1changed(self, num):
        self.axChanged(1, num)

    @QtCore.pyqtSlot("int")
    def ax2changed(self, num):
        self.axChanged(2, num)

    @QtCore.pyqtSlot("int")
    def displayChanged(self, num):
        self.display_num = num
        self.plotData()


class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.setWindowTitle('qData Display')
        self.setGeometry(450, 100, 1200, 800)

        self.splitter = QtGui.QSplitter(self)

        self.setCentralWidget(self.splitter)

        dirModel = QtGui.QFileSystemModel()
        dirModel.setRootPath(QtCore.QDir.rootPath())

        self.FolderTree = QtGui.QTreeView(self.splitter)
        self.FolderTree.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        # Set the model of the view.
        self.FolderTree.setModel(dirModel)
        # Set the root index of the view as the user's home directory.
        self.FolderTree.setRootIndex(dirModel.index(r'./test_data/'))
        self.FolderTree.hideColumn(1)
        self.FolderTree.hideColumn(2)
        self.FolderTree.hideColumn(3)
        self.FolderTree.setMinimumWidth(200)
        self.FolderTree.setSizePolicy(QtGui.QSizePolicy.Minimum,
                                      QtGui.QSizePolicy.Minimum)
        self.plotItem = PlotFrame()
        self.splitter.addWidget(self.plotItem)

        self.splitter.setStretchFactor(1, 1)

        QtCore.QObject.connect(self.FolderTree.selectionModel(), QtCore.SIGNAL('selectionChanged(QItemSelection, QItemSelection)'), self.FolderSelected)


    @QtCore.pyqtSlot("QItemSelection, QItemSelection")
    def FolderSelected(self, selected, deselected):
        index = selected.indexes()
        self.FolderTree.setCurrentIndex(index[0])
        # self.tree_schedule.setCurrentIndex(index[0])
        # deindex = deselected.indexes()
        model = self.FolderTree.model()

        path = model.filePath(index[0])
        item = qd.scanFolder(path)
        if item:
            self.plotItem.setPath(path)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
