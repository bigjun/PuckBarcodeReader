#!/usr/bin/env python3

import sys
from PyQt4 import QtGui, QtCore

from image import CvImage
from datamatrix import DataMatrix


"""
Todo:

Currently there are two main types of error:
    1 - The datamatrix finder pattern is completely missed by the search algorithm
    2 - Matrix is read but there are too many errors. This is almost always because
        the sample locations are systematically out of alignment with the matrix
        pixels.
"""


TEST_IMAGE_PATH = 'C:/PROJECTS_WORKSPACE/8815 Diamond/barcode/test-images/'
TEST_OUTPUT_PATH = 'C:/PROJECTS_WORKSPACE/8815 Diamond/barcode/test-output/'


class BarcodeReader(QtGui.QMainWindow):

    def __init__(self):
        super(BarcodeReader, self).__init__()

        # GUI Elements
        self.tabs = None
        self.originalImageFrame = None
        self.originalImageTab = None
        self.highlightImageFrame = None
        self.highlightImageTab = None
        self.barcodeTable = None
        self.console = None

        # Variables
        self.inputFilePath = ''

        self.init_ui()

        # ---  TESTING -------
        filepath = TEST_IMAGE_PATH + "skew1.jpg"
        #self.process_image(filepath)

    def init_ui(self):
        """ Create the basic elements of the user interface
        """
        self.setGeometry(100, 100, 850, 800)
        self.setWindowTitle('Diamond Puck Barcode Scanner')
        self.setWindowIcon(QtGui.QIcon('web.png'))

        self.init_menu_bar()

        # Create Tab control
        self.tabs = QtGui.QTabWidget()
        self.tabs.setFixedSize(700, 730)
        self.originalImageTab = QtGui.QWidget()
        self.highlightImageTab = QtGui.QWidget()
        self.tabs.addTab(self.originalImageTab, "Original")
        self.tabs.addTab(self.highlightImageTab, "Highlight")

        # Create image frames
        self.originalImageFrame = QtGui.QLabel(self.originalImageTab)
        self.originalImageFrame.setStyleSheet("background-color: black")
        self.originalImageFrame.setGeometry(0, 0, 700, 700)
        self.highlightImageFrame = QtGui.QLabel(self.highlightImageTab)
        self.highlightImageFrame.setStyleSheet("background-color: black")
        self.highlightImageFrame.setGeometry(0, 0, 700, 700)

        # Create barcode table
        self.barcodeTable = QtGui.QTableWidget()
        self.barcodeTable.setFixedWidth(110)
        self.barcodeTable.setColumnCount(1)
        self.barcodeTable.setRowCount(10)
        self.barcodeTable.setHorizontalHeaderLabels(['Barcode'])
        self.barcodeTable.setColumnWidth(0, 100)
        self.barcodeTable.clearContents()

        # Create status message console
        self.console = QtGui.QLineEdit("hello")

        # Set Window layout
        hbox = QtGui.QHBoxLayout()
        hbox.setSpacing(10)
        hbox.addWidget(self.tabs)
        hbox.addWidget(self.barcodeTable)
        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.console)
        vbox.addStretch(1)
        hbox2 = QtGui.QHBoxLayout()
        hbox2.addLayout(vbox)
        hbox2.addStretch(1)

        main_widget = QtGui.QWidget()
        main_widget.setLayout(hbox2)
        self.setCentralWidget(main_widget)

        self.show()

    def init_menu_bar(self):
        """Create and populate the manu bar
        """
        # load action
        load_action = QtGui.QAction(QtGui.QIcon('open.png'), '&Load Image', self)
        load_action.setShortcut('Ctrl+L')
        load_action.setStatusTip('Load Image')
        load_action.triggered.connect(self.new_image_from_file)

        # snap action
        preview_action = QtGui.QAction(QtGui.QIcon('open.png'), '&Webcam Preview', self)
        preview_action.setShortcut('Ctrl+W')
        preview_action.setStatusTip('Show webcam preview')
        preview_action.triggered.connect(CvImage.stream_webcam)

        # snap action
        snap_action = QtGui.QAction(QtGui.QIcon('open.png'), '&Capture Image From Webcam', self)
        snap_action.setShortcut('Ctrl+T')
        snap_action.setStatusTip('Load Capture Image From Webcam')
        snap_action.triggered.connect(self.new_image_from_camera)

        # exit action
        exit_action = QtGui.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(QtGui.qApp.quit)

        # create menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        file_menu.addAction(load_action)
        file_menu.addAction(preview_action)
        file_menu.addAction(snap_action)
        file_menu.addAction(exit_action)

    def new_image_from_file(self):
        """Load a process (scan for barcodes) an image from file
        """
        filepath = str(QtGui.QFileDialog.getOpenFileName(self, 'Open file', TEST_IMAGE_PATH))
        if filepath:
            self.barcodeTable.clearContents()
            self.tabs.setCurrentIndex(0)
            self.originalImageFrame.clear()
            self.highlightImageFrame.clear()
            self.setWindowTitle('Diamond Puck Barcode Scanner - ' + filepath)
            self.process_image(filepath)

    def new_image_from_camera(self):
        #frame = CvImage.capture_image_from_camera()
        frame = CvImage.get_current_webcam_frame()
        filename = TEST_OUTPUT_PATH + 'camtest.png'
        frame.save_as(filename)
        self.process_image(filename)



    def process_image(self, filepath):
        self.inputFilePath = filepath
        self.display_image_in_frame(self.inputFilePath, self.originalImageFrame)
        self.console.setText("")

        cv_image = CvImage(self.inputFilePath)
        try:
            datamatricies, puck = DataMatrix.ScanImage(cv_image)
            self.refill_table_with_barcodes(datamatricies, puck)
            self.highlight_barcodes_from_image(cv_image, datamatricies, puck)
            if puck.error:
                self.console.setText(puck.error)
        except Exception as ex:
            self.console.setText(ex.message)

    @staticmethod
    def display_image_in_frame(filename, frame):
        pixmap = QtGui.QPixmap(filename)
        frame.setPixmap(pixmap.scaled(frame.size(),
            QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
        frame.setAlignment(QtCore.Qt.AlignCenter)

    def highlight_barcodes_from_image(self, cvimg, datamatricies, puck):
        # Draw features on image
        cvimg.draw_puck_template(puck, CvImage.BLUE)
        cvimg.draw_datamatrix_highlights(datamatricies, CvImage.GREEN, CvImage.RED)
        cvimg.draw_puck_pin_circles(puck, CvImage.GREEN)
        cvimg.draw_puck_pin_rois(puck, CvImage.ORANGE)
        cvimg.crop_image(puck.puck_center, 1.1*puck.puck_radius)

        # Save and display image
        filename = TEST_OUTPUT_PATH + 'highlight_test.png'
        cvimg.save_as(filename)
        self.display_image_in_frame(filename, self.highlightImageFrame)
        self.tabs.setCurrentIndex(1)

    def refill_table_with_barcodes(self, datamatricies, puck):
        num_slots = puck.template.slots
        self.barcodeTable.clearContents()
        self.barcodeTable.setRowCount(num_slots)

        # Colour empty boxes grey
        for s in range(num_slots):
            barcode = QtGui.QTableWidgetItem()
            barcode.setBackgroundColor(QtGui.QColor(128, 128, 128, 100))
            barcode.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            self.barcodeTable.setItem(s, 0, barcode)

        for dm in datamatricies:
            slot = dm.pinSlot
            if slot < 1 or slot > num_slots:
                continue

            index = slot - 1

            # Barcode data column
            if dm.data is not None:
                barcode = QtGui.QTableWidgetItem(dm.data)
                barcode.setBackgroundColor(QtGui.QColor(0, 255, 0, 100))
                barcode.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                self.barcodeTable.setItem(index, 0, barcode)
            else:
                barcode = QtGui.QTableWidgetItem("")
                barcode.setBackgroundColor(QtGui.QColor(255, 0, 0, 100))
                barcode.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                self.barcodeTable.setItem(index, 0, barcode)

def main():
    app = QtGui.QApplication(sys.argv)
    ex = BarcodeReader()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
