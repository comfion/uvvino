#!/usr/bin/python
# UvVino program for reading HPLC detector data.
# http://wiki.techinc.nl/index.php/UV/Vino
# <vtechinc@xs4all.nl>
# License: GPLv3

import sys
import serial, time, csv
from operator import attrgetter
from time import sleep
from PyQt4 import QtCore, QtGui
from uvvino_ui import Ui_UVVino

class UvVinodatahandler(QtCore.QThread):
	
	def __init__(self, parent = None):
    
		QtCore.QThread.__init__(self, parent)
		self.exiting = False
		self.connected = False
		self.firstval = False
		self.size = QtCore.QSize(0, 0)
				
	def __del__(self):
		
		self.connected = False
		self.exiting = True
		self.wait()
        
	def handledata(self,portname):
		self.exiting = False
#		print ("thread: connecting to port",str(portname))
		try:
			self.ser = serial.Serial(str(portname), 9600, timeout=0)
		except IOError:
				print("thread: IOError!")
				self.emit(QtCore.SIGNAL("output2(int)"),2)
				self.exitsignal()
		else:
			print ("thread: connected to: ",self.ser.portstr)
			#self.ser.write(chr(48)) #send close to begin with
			self.connected = True
			self.start()

	def openvalve(self,nvalve):
		print ("opening valve: ", nvalve)
		if(nvalve == 0):
			self.ser.write("0,0,0\n") 
		elif(nvalve == 1):
			self.ser.write("1,0,0\n") 
		elif(nvalve == 2):
			self.ser.write("0,1,0\n") 
		elif(nvalve == 3):
			self.ser.write("0,0,1\n") 	
			
		
	def run(self):
        
	# Note: This is never called directly. It is called by Qt once the
	# thread environment has been set up.
        
		#send start signal
		#self.ser.write(chr(49))
		
		print ("self.exiting",self.exiting)
		while not self.exiting:
			
			try:
				buf=self.ser.inWaiting()
				if (buf >0):
					data = self.ser.read(buf)
#					print("thread: Got:", data)
					if ((data.find("\x00")) < 0 ):
						data.replace("\n","");
						data.replace("\r","");
					
						lines = data.splitlines()
						for csvdata in lines:
#							print("thread: csvdata : ",csvdata)
							splcsv = csvdata.split(",")
							if (len(splcsv) == 2 and splcsv[0].isdigit() and splcsv[1].isdigit()):
								msecs= int(splcsv[0])
								raw=int(splcsv[1])
#								print("thread:milisecs: ",msecs)
#								print("thread:sending raw:",raw)
								self.emit(QtCore.SIGNAL("output(int,int)"),msecs,raw)		
								self.firstval = True
				
			except:
					print("thread: error")
					self.connected = False
					self.exiting = True
			else:
				sleep(1) 
		#if(self.ser.isOpen()):  
			#self.ser.write(chr(48)) #send stop signal
		self.ser.close()
		
	def exitsignal(self):
		print("thread: exitting..")
		
		#if(self.ser.isOpen()):  
			#self.ser.write(chr(48)) #send stop signal
		self.ser.close()
		self.connected = False
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
	
	mixinglist = []
	curmixentr = []
	mixlist_processing = False
	mixlist_finalized = False
	currentvalve = 0
	valve_opentime = 0
	nextitem_time = 0
	mix_starttime = 0
	
	
	def __init__(self, parent=None):
		QtGui.QWidget.__init__(self, parent)
		self.ui = Ui_UVVino()
		self.ui.setupUi(self)
		self.thread = UvVinodatahandler()
		
		self.modified = False
		self.saveAsActs = []
		self.createActions()
		self.createMenus()

		self.valvetimer = QtCore.QTimer()
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
		QtCore.QObject.connect(self.ui.mixing_addbutton,QtCore.SIGNAL("clicked()"), self.add_mixvalue)
		QtCore.QObject.connect(self.ui.valve_a_button,QtCore.SIGNAL("clicked()"), self.openvalve1)
		QtCore.QObject.connect(self.ui.valve_b_button,QtCore.SIGNAL("clicked()"), self.openvalve2)
		QtCore.QObject.connect(self.ui.valve_c_button,QtCore.SIGNAL("clicked()"), self.openvalve3)
		QtCore.QObject.connect(self.thread, QtCore.SIGNAL("output(int,int)"), self.addtoaxis)
		QtCore.QObject.connect(self.thread, QtCore.SIGNAL("output2(int)"), self.reporterror)
		
		self.is_running = False
		self.threadrunning = False
		self.timesetting = self.ui.time_set.value()
		self.absorbance_range = 1000
		print("update");
		self.update()
	
	def openvalve1(self):
		self.thread.openvalve(1)
	
	def openvalve2(self):
		self.thread.openvalve(2)
		
	def openvalve3(self):
		self.thread.openvalve(3)
				
	def reporterror(self,num):
		s = QtCore.QString("Cannot open port, type again")
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
			if(not self.mixinglist):
				if ((self.ui.valve_a.value() + self.ui.valve_b.value() + self.ui.valve_c.value()) == 100):
					t = {"a":self.ui.valve_a.value(), "b":self.ui.valve_b.value(), "c":self.ui.valve_c.value(), "time":0, "gradient":self.ui.mixing_grad_check.isChecked()}
					self.mixinglist.append(t)
				else:
					#report error but select valve 1 as default for opening
					print("values together not 100, defaulting to valve a")
					t = {"a":100, "b":0, "c":0, "time":0, "gradient":self.ui.mixing_grad_check.isChecked()}
					
			self.valvetimer.timeout.connect(self.processvalve)
			self.valvetimer.start(100)
			QtCore.QTimer.singleShot(1000, self.thread.openvalve(1))
						
			
	def stopcollecting(self):
		self.ui.lineEdit.SetEnabled = True
		self.is_running = False
		#self.lcdtimer.stop()
		self.valvetimer.stop()
		self.thread.openvalve(0)  #close all valves
		self.drawpos=0
		self.lastx=0
		self.lasty=0
		self.listcntl=0
		self.starttime=0;
		self.lasttime=0;
		self.mixinglist = []
		self.ui.valvetime.setMinimum(0)	
		self.ui.valvetime.setValue(0)	
		self.ui.valve_a.setValue(100)
		self.ui.valve_b.setValue(0)
		self.ui.valve_c.setValue(0)
		self.curmixentr = []
		self.mixlist_processing = False
		self.mixlist_finalized = False
		self.thread.firstval = False
		self.currentvalve = 0
		self.valve_opentime = 0
		self.nextitem_time = 0
		self.mix_starttime = 0
		print("stopping to collect")
		self.thread.exitsignal()
		s = QtCore.QString("Initialize")
		self.ui.startstop_button.setText(s)
		print(self.vlist)		

		self.analyzepeaks(self.vlist)	

	def analyzepeaks(self,adata):
		
		x_axis = []
		y_axis = []
		highest = 0
					
		startofpeak = 0
		endofpeak = 0

		detected_peaks = []
		foundpeak = False
		
		sumtotal = 0		
		
		#load x and y axis
		for csvdata in adata:
			splcsv = csvdata.split(",")
			x_axis.append(int(splcsv[0]))
			y_axis.append(int(splcsv[1]))

		#loop through the axis and detect peaks (in a most elegant fashion i must add - hail to the king baby)
		
		for n in range(len(x_axis)):
			curyval = y_axis[n]
			if( curyval > 2 and foundpeak == False):
				foundpeak = True
				startofpeak = n
				highest = y_axis[n]
			elif(y_axis[n] > highest and foundpeak == True):	
				highest = y_axis[n]
			elif(y_axis[n] < 2 and foundpeak == True):
				foundpeak = False
				if((n - startofpeak) < 2):
					startofpeak = 0
					endofpeak = 0
				else:
					endofpeak = n
					print("adding peak, start,highest,endofpeak:",startofpeak,highest,endofpeak)
					print("xaxis values for startofpeak and endofpeak",x_axis[startofpeak], x_axis[endofpeak])
					print("yaxis values for startofpeak and endofpeak",y_axis[startofpeak], y_axis[endofpeak])
					peakinfo = {"startofpeak":startofpeak, "highest":highest, "endofpeak":endofpeak, "totalarea":0, "areapercentage":0.00}
					detected_peaks.append(peakinfo.copy())
				
		
		#integrate the peaks
		print("number peaks:",len(detected_peaks))
		for n in range(len(detected_peaks)):
			print("print start of peak from current loop",detected_peaks[n]["startofpeak"])
			start = detected_peaks[n]["startofpeak"]
			end = detected_peaks[n]["endofpeak"]
			
			print ("x_axis[start]",x_axis[start])
			print ("x_axis[end]",x_axis[end])
			
			
			areasum = 0
			for x in range(x_axis[start],(x_axis[end] +1)):
				#sum the y values
				areasum = areasum + y_axis[x]
			
			detected_peaks[n]["totalarea"] = areasum
			print("areasum for peak",n,detected_peaks[n]["totalarea"]) 
			
			sumtotal = sumtotal + areasum
				
		# calculate %
		print("sumtotal:", sumtotal)
		
		for n in range(len(detected_peaks)):
			percentage = (float(detected_peaks[n]["totalarea"]) / float(sumtotal)) * 100.00
			detected_peaks[n]["areapercentage"] = round(percentage, 2)
						
		print("detected peaks")
		print("\n")
		print(detected_peaks)	
		
		if (not detected_peaks):
			text="No peaks detected"
		else:
			text = ""
			for n in range(len(detected_peaks)):
				text = text + "peak " + str((n+1)) + " area: " + str(detected_peaks[n]["areapercentage"]) + "% \n" 
				
		QtGui.QMessageBox.about(self, "Peak analysis", text)
	
	def addtoaxis(self,msecs,value):
		self.modified = True
#		print("recieved val: ",value)
#		print("recieved msecs: ",msecs)	
		if(value>1023):
			value = 1023
		seconds=msecs/1000
		
		if(self.starttime == 0):
			self.starttime=seconds
			
		if(self.lasttime == 0):
			self.lasttime = seconds
		elif (seconds > self.lasttime) :
#			print("sec > self.lasttime")
			lobj = str(seconds-self.starttime) + str(",") + str(value)
			self.vlist.append(lobj)
		
			painter = QtGui.QPainter()
			painter.begin(self.pdarea)
			painter.setPen(QtCore.Qt.red)
			wpc = 0.09
			hpc = 0.93
			iw = self.pdarea.width()
			ih = self.pdarea.height()
			
			# Set time (x) position
			xpos = iw * wpc + (seconds - self.starttime) * self.secondstep
		
			#Set peakheight (y) position
			y= ih *hpc - ih *wpc
			factor = y / 1023
		
			ypos = (ih*hpc) - (value * factor) 
		
#			print("ih*hpc: ",(ih*hpc))
#			print("factor",factor)
#			print("xpos: ",xpos)
#			print("ypos: ",ypos)
#			print("lastxpos: ",self.lastx)
#			print("lastypos: ",self.lasty)
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

	def add_mixvalue(self):
		# add values for m1x0r
		
		# check if total mixing values equals 100%
		if ((self.ui.valve_a.value() + self.ui.valve_b.value() + self.ui.valve_c.value()) == 100):
			t = {"a":self.ui.valve_a.value(), "b":self.ui.valve_b.value(), "c":self.ui.valve_c.value(), "time":self.ui.valvetime.value(), "gradient":self.ui.mixing_grad_check.isChecked()}
			self.mixinglist.append(t)
			print("turple added to vlist:", t)
			self.ui.valvetime.setMinimum(self.ui.valvetime.value() + 1)	
		else:
			#do error thang
			print("error mixing values not equal to 100%")
	
	def processvalve(self):
		
		
		if (self.thread.connected and self.thread.firstval and not self.mixlist_finalized):
			
			if (self.mixlist_processing == False):
				
				self.curmixentr = self.mixinglist.pop(0)
				if (self.mixinglist):			
					self.nextitem_time =  (self.mixinglist[0]["time"] - self.curmixentr["time"]) * 60 + self.lasttime
					print("self.nexitemtime , self.thread.firstval, self.lasttime:",self.nextitem_time, self.thread.firstval, self.lasttime)
				else:
					print("last entry in mixlist popped setting finalized to True")
					self.mixlist_finalized = True
				
				if (self.curmixentr["a"] == 100):
					self.thread.openvalve(1)		
					self.currentvalve = 0
					
				elif (self.curmixentr["b"] == 100):
					self.thread.openvalve(2)
					self.currentvalve = 0
									
				elif (self.curmixentr["c"] == 100):
					self.thread.openvalve(3)		
					self.currentvalve = 0
					
				else:
					self.mix_starttime = self.lasttime
					if (self.curmixentr["a"]):
						self.thread.openvalve(1)		
						self.currentvalve = 'a'
						self.valve_opentime = self.curmixentr["a"] / 10
					elif (self.curmixentr["b"]):
						self.thread.openvalve(2)
						self.currentvalve = 'a'
						self.valve_opentime = self.curmixentr["b"] / 10
					else:
						self.thread.openvalve(3)
						self.currentvalve = 'c'
						self.valve_opentime = self.curmixentr["c"] / 10
					
					self.valve_opentime = self.curmixentr["a"] / 10
					
					
				self.mixlist_processing = True
			
			else:
				if(self.lasttime > self.nextitem_time) :
					print("self lastime > self nexitimetime",self.lasttime, self.nextitem_time)
					self.mixlist_processing = False
				else:
					if (self.lasttime >= (self.mix_starttime + self.valve_opentime) and self.currentvalve):
						if (self.currentvalve == 'a'):
							if (self.curmixentr["b"]):
								self.thread.openvalve(2)
								self.mix_starttime = self.lasttime
								self.currentvalve = 'b'
								self.valve_opentime = self.curmixentr["b"] / 10
							elif (self.curmixentr["c"]):
								self.thread.openvalve(3)
								self.mix_starttime = self.lasttime
								self.currentvalve = 'c'
								self.valve_opentime = self.curmixentr["c"] / 10
						elif (self.currentvalve == 'b'):
							if (self.curmixentr["c"]):
								self.thread.openvalve(3)
								self.mix_starttime = self.lasttime
								self.currentvalve = 'c'
								self.valve_opentime = self.curmixentr["c"] / 10
							elif (self.curmixentr["a"]):
								self.thread.openvalve(1)
								self.mix_starttime = self.lasttime
								self.currentvalve = 'a'
								self.valve_opentime = self.curmixentr["a"] / 10							
						elif (self.currentvalve == 'c'):
							if (self.curmixentr["a"]):
								self.thread.openvalve(1)
								self.mix_starttime = self.lasttime
								self.currentvalve = 'a'
								self.valve_opentime = self.curmixentr["a"] / 10
							elif (self.curmixentr["b"]):
								self.thread.openvalve(2)
								self.mix_starttime = self.lasttime
								self.currentvalve = 'b'
								self.valve_opentime = self.curmixentr["b"] / 10																	
#		else:
#			print("processvalve called thread connected = ", self.thread.connected, "and mixlist finalized = ", self.mixlist_finalized )
		
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
#		self.stopcollecting()
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
			"Author: Harald Jorgensen (vtechinc@xs4all.nl)"
			))
        
if __name__ == "__main__":
	app = QtGui.QApplication(sys.argv)
	myapp = UvVinoMain()
	myapp.show()
	sys.exit(app.exec_())
