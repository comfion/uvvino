#!/usr/bin/python
# UvVino program for reading HPLC detector data.
# http://wiki.techinc.nl/index.php/UV/Vino
# <vtechinc@xs4all.nl>
# License: GPLv3

import sys
import serial, time, csv
from time import sleep
from PyQt4 import QtCore, QtGui
from uvvino_ui import Ui_UVVino

class UvVinodatahandler(QtCore.QThread):
	
	def __init__(self, parent = None):
    
		QtCore.QThread.__init__(self, parent)
		self.exiting = False
		self.size = QtCore.QSize(0, 0)
		
		
	def __del__(self):
    
		self.exiting = True
		self.wait()
        
	def handledata(self,portname):
		self.exiting = False
		print ("from thread: connecting to port",str(portname))
		try:
			self.ser = serial.Serial(str(portname), 9600, timeout=0)
		except IOError:
				print("IOError!")
				self.emit(QtCore.SIGNAL("output2(int)"),2)
				self.exitsignal()
		else:
			print ("from thread: connected to: ",self.ser.portstr)
			self.ser.write(chr(48)) #send close to begin with
			self.start()
		

	def run(self):
        
	# Note: This is never called directly. It is called by Qt once the
	# thread environment has been set up.
        
		#send start signal
		#self.ser.write(chr(49))
		vinorun = 0
		print ("self.exiting",self.exiting)
		while not self.exiting:
			
			try:
				buf=self.ser.inWaiting()
				if (buf >0):
					data = self.ser.read(buf)
					print("Got:", data)
					if (data.find("waiting") > 0):
						print("vino waiting text:", data)
						vinorun = 1
						self.ser.write(chr(49))
					if ((data.find("\x00")) < 0 and vinorun == 1):
						data.replace("\n","");
						data.replace("\r","");
					
						lines = data.splitlines()
						for csvdata in lines:
							print("csvdata : ",csvdata)
							splcsv = csvdata.split(",")
							if (len(splcsv) == 2 and splcsv[0].isdigit() and splcsv[1].isdigit()):
								msecs= int(splcsv[0])
								raw=int(splcsv[1])
								print("from thread:milisecs: ",msecs)
								print("from thread:sending raw:",raw)
								self.emit(QtCore.SIGNAL("output(int,int)"),msecs,raw)		
				
			except:
					print("error")	
			else:
				sleep(1) 
		if(self.ser.isOpen()):  
			self.ser.write(chr(48)) #send stop signal
		self.ser.close()
		
	def exitsignal(self):
		print("thread:exitting..")
		
		if(self.ser.isOpen()):  
			self.ser.write(chr(48)) #send stop signal
		self.ser.close()
		self.exiting = True

		
class UvVinoMain(QtGui.QMainWindow):
	
	drawpos=0
	lastx=0
	lasty=0
	secondstep=0
	listcnt=0
	vlist = []
	starttime=0;
	lasttime=0;
	
	def __init__(self, parent=None):
		QtGui.QWidget.__init__(self, parent)
		self.ui = Ui_UVVino()
		self.ui.setupUi(self)
		self.thread = UvVinodatahandler()
		
		self.modified = False
		self.saveAsActs = []
		self.createActions()
		self.createMenus()

		#self.lcdtimer=QtCore.QTimer()
		#self.lcdtimer.timeout.connect(self.runlcd)
					
		self.pdarea = QtGui.QImage(QtCore.QSize(1109,700),QtGui.QImage.Format_RGB32)
		self.pdarea.fill(QtGui.qRgb(255, 255, 255))
			
		self.rangegroup = QtGui.QButtonGroup(self)
		self.rangegroup.setObjectName("rangegroup")
		self.rangegroup.addButton(self.ui.radio_AU)
		self.rangegroup.addButton(self.ui.radio_mau)
		self.rangegroup.addButton(self.ui.radio_mv)
		self.rangegroup.addButton(self.ui.radio_raw)

		QtCore.QObject.connect(self.ui.startstop_button,QtCore.SIGNAL("clicked()"), self.startstop_datacollection)
		QtCore.QObject.connect(self.thread, QtCore.SIGNAL("output(int,int)"), self.addtoaxis)
		QtCore.QObject.connect(self.thread, QtCore.SIGNAL("output2(int)"), self.reporterror)
						
		self.is_running = False
		self.threadrunning = False
		self.timesetting = self.ui.time_set.value()
		self.absorbance_range = 1000
		print("update");
		self.update()
		
	def reporterror(self,num):
		s = QtCore.QString("Cannot open port, type again") # turn into a popup
		self.ui.lineEdit.setText(s)
		self.stopcollecting()
		self.update()
		
	def startstop_datacollection(self):
		if self.is_running:
			print("Stopping")
			self.stopcollecting()
			
		else:
			print("Starting")
			self.is_running = True
			self.ui.lineEdit.SetEnabled = False
			self.vlist = []	
			self.setupaxis()
			self.thread.handledata(self.ui.lineEdit.text())
			s = QtCore.QString("Stop")
			self.ui.startstop_button.setText(s)
			self.epoch = int(time.time())
			self.runlcd()
			#self.lcdtimer.start(1000)
			#QtCore.QTimer.singleShot((1000 * 60 * self.ui.time_set.value()), self.stopcollecting)
						
			
	def stopcollecting(self):
		self.ui.lineEdit.SetEnabled = True
		self.is_running = False
		#self.lcdtimer.stop()
		self.drawpos=0
		self.lastx=0
		self.lasty=0
		self.listcntl=0
		self.starttime=0;
		self.lasttime=0;
		print("stopping to collect")
		self.thread.exitsignal()
		s = QtCore.QString("Start")
		self.ui.startstop_button.setText(s)
		print(self.vlist)		
	
	def addtoaxis(self,msecs,value):
		self.modified = True
		print("recieved val: ",value)
		print("recieved msecs: ",msecs)	
		if(value>1023):
			value = 1023
		seconds=msecs/1000
		
		if(self.starttime == 0):
			self.starttime=seconds
			
		if(self.lasttime == 0):
			self.lasttime = seconds
		elif (seconds > self.lasttime) :
			print("sec > self.lasttime")
			lobj = str(seconds-self.starttime) + str(",") + str(value)
			self.vlist.append(lobj)
		
			painter = QtGui.QPainter()
			painter.begin(self.pdarea)
			wpc = 0.09
			hpc = 0.93
			iw = self.pdarea.width()
			ih = self.pdarea.height()
			painter.setPen(QtCore.Qt.red)	
			# Set time (x) position
			xpos = iw * wpc + (seconds - self.starttime) * self.secondstep
		
			#Set peakheight (y) position
			y= ih *hpc - ih *wpc
			factor = y / 1023
		
			ypos = (ih*hpc) - (value * factor) 
		
			print("ih*hpc: ",(ih*hpc))
			print("factor",factor)
			print("xpos: ",xpos)
			print("ypos: ",ypos)
			print("lastxpos: ",self.lastx)
			print("lastypos: ",self.lasty)
			painter.drawLine(QtCore.QLineF(self.lastx, self.lasty, xpos, ypos))
			self.lastx=xpos
			self.lasty=ypos
			self.lasttime=seconds
			
			ts = time.strftime('%H:%M:%S', time.localtime(0 - 3600 + (seconds - self.starttime)))
			self.ui.lcd.display(ts)
		
			#self.drawpos=self.drawpos+1
			painter.end()
			self.update()
		
	def setupaxis(self):
		
		self.clearImage()
		
		painter = QtGui.QPainter()
		painter.begin(self.pdarea)
		#painter = qp
		
				
		wpc = 0.09
		hpc = 0.93
		iw = self.pdarea.width()
		ih = self.pdarea.height()
		
		tly= ih * hpc - ih *wpc
		
		print("intial iw:",iw)
		print("intial ih:",ih)
		print("intial ih*hpc:",(ih*hpc))
		
		linerange = 20
		timerange=self.ui.time_set.value()
		
		
		
		painter.drawLine(QtCore.QLineF(iw * wpc, ih * hpc, iw * hpc, ih * hpc))
		painter.drawLine(QtCore.QLineF(iw * wpc, ih * hpc, iw * wpc, ih * wpc))
		
		self.lastx = iw * wpc
		self.lasty = ih * hpc
		
		lx = iw * hpc - iw * wpc
		ly = ih * hpc - ih * wpc
		
		# Determine how many pixels to jump for every second
		self.secondstep =  lx / (self.ui.time_set.value() *60) 
		
				
		linedistance = lx / linerange
		
		for x in range(1,(linerange+1)):
			painter.drawLine(QtCore.QLineF(iw * wpc + (linedistance *x), ih * hpc,iw * wpc + (linedistance *x), ih * hpc+10))
		
		linedistance = ly / linerange
		
		for y in range(1,(linerange+1)):
			painter.drawLine(QtCore.QLineF(iw * wpc, ih * hpc - (linedistance * y),iw * wpc-10, ih * hpc - (linedistance *y)))
		
		painter.setFont(QtGui.QFont('Decorative', 10))
        
		offset = QtCore.QPointF(iw * wpc-9, ih * hpc+15)
		painter.drawText(offset, "0")
		
		offset = QtCore.QPointF(iw / 2 -60 , ih - 5)
		painter.drawText(offset, "Time (minutes)")
		
		offset = QtCore.QPointF(15,40)
		curbtn = self.rangegroup.checkedButton()
		rangtxt = curbtn.toolTip()
		#print("rangetext:",rangtxt)
		painter.drawText(offset, rangtxt)
		
		linedistance = (lx / (linerange / 2))
		
		for x in range(1,(linerange/2)+1):
			offset = QtCore.QPointF(iw * wpc + (linedistance *x)-4, ih * hpc + 23)
			tmps = str(x*(timerange * 0.1))
			if (timerange > 99):
				nstr = tmps[:3]
				nstr = nstr.replace(".", "")
			elif (timerange < 10):
				nstr=tmps
			else :
				nstr = tmps[:2]
			#print("text: ",nstr)
			painter.drawText(offset, nstr)
		
		linedistance = (ly / (linerange / 2))
		
		if(rangtxt == "AU"):
			linediv = 1
		elif(rangtxt == "mAU"):
			linediv = 1000
		elif(rangtxt == "uVolt"):
			linediv = 1.1
		elif(rangtxt == "RAW"):
			linediv = 1024
		else:
			linediv = 1000
		
		
		for y in range(1,(linerange/2)+1):
			offset = QtCore.QPointF(iw * wpc -60, ih * hpc - (linedistance *y))
			self.text2 = str(y*(linediv / 10.0))
			painter.drawText(offset, self.text2)
		
		painter.end()
		
	def clearImage(self):
		self.pdarea.fill(QtGui.qRgb(255, 255, 255))
		self.update()
	
	
	def runlcd(self):
		
		ts = time.strftime('%H:%M:%S', time.localtime(0 - 3600))
		self.ui.lcd.display(ts)

	def paintEvent(self, event):
		
		qp = QtGui.QPainter()
		
		textColor = QtGui.QColor(QtCore.Qt.black)
		#qp.fillPath(self.path, textColor)
		
		qp.begin(self)
		qp.setRenderHint(QtGui.QPainter.Antialiasing)
		#qp.drawPath(self.path)
		qp.drawImage(QtCore.QPoint(0, 23), self.pdarea)
		#self.setupaxis(qp)
			
		qp.end()
		self.initial = False
		
	def createActions(self):
		
		for format in QtGui.QImageWriter.supportedImageFormats():
			text = self.tr("%1...").arg(QtCore.QString(format).toUpper())

			action = QtGui.QAction(text, self)
			action.setData(QtCore.QVariant(format))
			self.connect(action, QtCore.SIGNAL("triggered()"), self.save)
			self.saveAsActs.append(action)

		self.exitAct = QtGui.QAction(self.tr("E&xit"), self)
		self.exitAct.setShortcut(self.tr("Ctrl+Q"))
		self.connect(self.exitAct, QtCore.SIGNAL("triggered()"),self, QtCore.SLOT("close()"))

		self.aboutAct = QtGui.QAction(self.tr("&About"), self)
		self.connect(self.aboutAct, QtCore.SIGNAL("triggered()"), self.about)

	def createMenus(self):
		self.saveAsMenu = QtGui.QMenu(self.tr("&Save As"), self)
		for action in self.saveAsActs:
			self.saveAsMenu.addAction(action)

		self.fileMenu = QtGui.QMenu(self.tr("&File"), self)
		self.fileMenu.addMenu(self.saveAsMenu)
		self.fileMenu.addSeparator()
		self.fileMenu.addAction(self.exitAct)

		self.helpMenu = QtGui.QMenu(self.tr("&Help"), self)
		self.helpMenu.addAction(self.aboutAct)
        
		self.menuBar().addMenu(self.fileMenu)
		self.menuBar().addMenu(self.helpMenu)
		
	def closeEvent(self, event):
		if self.maybeSave():
			event.accept()
		else:
			event.ignore()
	
	def save(self):
		action = self.sender()
		fileFormat = action.data().toByteArray()
		self.saveFile(fileFormat)
		
	def maybeSave(self):
		if self.modified:
			ret = QtGui.QMessageBox.warning(self, self.tr("UV/Vino"), self.tr("The recording has not been saved.\n"
						"Do you want to save the collected data?"),
						QtGui.QMessageBox.Yes | QtGui.QMessageBox.Default,
						QtGui.QMessageBox.No,
						QtGui.QMessageBox.Cancel | QtGui.QMessageBox.Escape)
			if ret == QtGui.QMessageBox.Yes:
				return self.saveFile("png")
			elif ret == QtGui.QMessageBox.Cancel:
				return False
		
		return True

	def saveFile(self, fileFormat):
		self.stopcollecting()
		initialPath = QtCore.QDir.currentPath() + "/untitled." + fileFormat

		filename = QtGui.QFileDialog.getSaveFileName(self, self.tr("Save As"),
									initialPath,
									self.tr("%1 Files (*.%2);;All Files (*)")
									.arg(QtCore.QString(fileFormat))
									.arg(QtCore.QString(fileFormat)))
		if filename.isEmpty():
			return False
		else:
			fn = filename.split(".")[0]
			fn=fn + str(".dump")
			print("opening: ",fn)
			thefile = open(fn, 'w') 
			for item in self.vlist:
				thefile.write("%s\n" % item)
			return self.saveImage(filename, fileFormat)
	
	def saveImage(self, filename, fileFormat):
		visibleImage = self.pdarea
		
		if visibleImage.save(filename, fileFormat):
			self.modified = False
			return True
		else:
			return False

	def about(self):
		QtGui.QMessageBox.about(self, self.tr("About Uv/Vino"), self.tr(
			"<p>The <b>Uv/Vino</b> program "
			"lalalalalala"
			))
        
if __name__ == "__main__":
	app = QtGui.QApplication(sys.argv)
	myapp = UvVinoMain()
	myapp.show()
	sys.exit(app.exec_())
