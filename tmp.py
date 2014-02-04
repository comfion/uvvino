import sys
from PyQt4 import QtCore, QtGui
from uvvino_ui import Ui_UVVino

class StartQT4(QtGui.QMainWindow):
	
	def __init__(self, parent=None):
		QtGui.QWidget.__init__(self, parent)
		self.ui = Ui_UVVino()
		self.ui.setupUi(self)
		
		self.pdarea = QtGui.QImage(QtCore.QSize(888,600),QtGui.QImage.Format_RGB32)
		self.pdarea.fill(QtGui.qRgb(255, 255, 255))
		
		self.setAttribute(QtCore.Qt.WA_StaticContents)
		self.myPenWidth = 1
		self.myPenColor = QtCore.Qt.black
		
		self.rangegroup = QtGui.QButtonGroup(self)
        self.rangegroup.setObjectName("rangegroup")
        self.rangegroup.addButton(self.radio_AU)
		self.rangegroup.addButton(self.radio_mau)
		self.rangegroup.addButton(self.radio_mv)
		self.rangegroup.addButton(self.radio_raw)
    
        
        
        
		QtCore.QObject.connect(self.ui.startstop_button,QtCore.SIGNAL("clicked()"), self.startstop_datacollection)
		
		bgcolor = QtGui.QColor(QtCore.Qt.white)
		
		self.is_running = False
		self.timesetting = self.ui.time_set.value()
		self.absorbance_range = 1000
					

	def startstop_datacollection(self):
		if self.is_running:
			print("Running")
			
			self.stopcollecting()
		else:
			print("Not running")
			self.collectdata()
			
	def stopcollecting(self):
		print("stopping to collect")
		s = QtCore.QString("Start")
		self.ui.startstop_button.setText(s)
		self.is_running = False
	
	def collectdata(self):
		print("collecting data")
		s = QtCore.QString("Stop")
		self.ui.startstop_button.setText(s)
		self.is_running = True
		
	def axis(self):
		
		painter = QtGui.QPainter()
		painter.begin(self.pdarea)
		
		wpc = 0.1
		hpc = 0.9
		iw = self.pdarea.width()
		ih = self.pdarea.height()
		
		linerange=20
		
		painter.drawLine(QtCore.QLineF(iw * wpc, ih * hpc, iw * hpc, ih * hpc))
		painter.drawLine(QtCore.QLineF(iw * wpc, ih * hpc, iw * wpc, ih * wpc))
		
		lx = iw * hpc - iw * wpc
		ly = ih * hpc - ih * wpc
		
		linedistance = lx / linerange
		
		for x in range(1,(linerange+1)):
			painter.drawLine(QtCore.QLineF(iw * wpc + (linedistance *x), ih * hpc,iw * wpc + (linedistance *x), ih * hpc+10))
		
		linedistance = ly / linerange
		
		for y in range(1,(linerange+1)):
			painter.drawLine(QtCore.QLineF(iw * wpc, ih * hpc - (linedistance * y),iw * wpc-10, ih * hpc - (linedistance *y)))
		
		painter.setFont(QtGui.QFont('Decorative', 10))
        
		offset = QtCore.QPointF(iw * wpc-9, ih * hpc+15)
		painter.drawText(offset, "0")
		
		offset = QtCore.QPointF(iw / 2 -60 , ih - 15)
		painter.drawText(offset, "Time (minutes)")
		
		offset = QtCore.QPointF((iw * wpc)-80, ih/2)
		rangtxt = self.ui.rangebuttongroup.checkedButton()
		painter.drawText(offset, rangtxt)
		
		painter.end()
		
	def setupaxis(self):
		print("called by main");
		
		self.path = QtGui.QPainterPath()
		
					
		self.path.moveTo(self.width() * 0.2, self.height() * 0.8)
		self.path.lineTo(self.width() * 0.9, self.height() * 0.8)
		self.path.moveTo(self.width() * 0.2, self.height() * 0.8)
		self.path.lineTo(self.width() * 0.2, self.height() * 0.1)
		
		
		
		lx = self.width() * 0.9 - self.width() * 0.2
		ly = self.height() * 0.9 - self.height() * 0.1
		print("lengte x:",lx)
		print("lengte y:",ly)
		
			
		linedistance = lx / 20
		print ("ldist", linedistance)
				
		for x in range(1,21):
			self.path.moveTo(self.width() * 0.2+(linedistance * x), self.height() * 0.8)
			self.path.lineTo(self.width() * 0.2+(linedistance * x), self.height() * 0.8+10)
        
		print ("ldist", linedistance)
		
		linedistance = ly / 20
		for y in range(1,21):
			self.path.moveTo(self.width() * 0.2, self.height() * 0.8 - (linedistance * y))
			self.path.lineTo(self.width() * 0.2-10, self.height() * 0.8 - (linedistance * y))
			
		
		newfont = self.font()
		newfont.setPointSize(8)
		
		offset = QtCore.QPointF(self.width() * 0.2-9, self.height() * 0.8+15)
		self.text2 = "0"					
		self.path.addText(offset, newfont, self.text2)
		
		offset = QtCore.QPointF((self.width() * 0.17)-80, 30)
		self.text2 = "Absorbance"					
		self.path.addText(offset, newfont, self.text2)
		
		offset = QtCore.QPointF((self.width() * 0.17)-70, 50) 
		self.text2 = "(mAU)"					
		self.path.addText(offset, newfont, self.text2)
		
		offset = QtCore.QPointF(self.width() / 2 -40 , self.height() - 5)
		self.text2 = "Time"
		self.path.addText(offset, newfont, self.text2)
		
		offset = QtCore.QPointF(self.width() / 2 , self.height() - 5)
		self.text2 = "(minutes)"
		self.path.addText(offset, newfont, self.text2)
		
		
		linedistance = lx / 10
		
		for x in range(1,11):
			offset = QtCore.QPointF(self.width() * 0.2+(linedistance * x)-3,  self.height() * 0.85)
			self.text2 = str(x*(self.timesetting / 10))
			self.path.addText(offset, newfont, self.text2)
		
		linedistance = ly / 10
		
		for y in range(1,11):
			offset = QtCore.QPointF(self.width() * 0.18 - 30 , self.height() * 0.8 - (linedistance * y) +3)
			self.text2 = str(y*(self.absorbance_range / 10))
			self.path.addText(offset, newfont, self.text2)
	
	def paintEvent(self, event):
		
		
		qp = QtGui.QPainter()
		
		textColor = QtGui.QColor(QtCore.Qt.black)
		#qp.fillPath(self.path, textColor)
		
		qp.begin(self)
		qp.setRenderHint(QtGui.QPainter.Antialiasing)
		#qp.drawPath(self.path)
		qp.drawImage(QtCore.QPoint(0, 23), self.pdarea)
		qp.end()
		self.axis()
		
		
if __name__ == "__main__":
	app = QtGui.QApplication(sys.argv)
	myapp = StartQT4()
	myapp.show()
	sys.exit(app.exec_())
