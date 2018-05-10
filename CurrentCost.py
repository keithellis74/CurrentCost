import serial
import xml.etree.ElementTree as ET
import datetime


ser = serial.Serial(port='/dev/ttyUSB0',
                    baudrate=57600,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=120)

ser.close()
ser.open()

keepLooping = True
inputBuffer = ""
while(keepLooping):
	
	try:
		if ser.inWaiting() > 0:
			x = ser.read(ser.inWaiting())
			inputBuffer = inputBuffer + str(x)
			
			if inputBuffer.find("</msg>") > 0:
				temp = inputBuffer.split("</msg>", 1)
				inputBuffer = temp[1]
				temp[0] = temp[0]+"</msg>"
				
				root = ET.fromstring(temp[0])
				#tree = ET.parse('msg.xml')
				#root = tree.getroot()
				temp = 0;
				watts = 0;

				for child in root:
					print child.tag, child.attrib, child.text
					if child.tag == "tmpr" :
						temp = float(child.text)
					if child.tag == "ch1" :
						watts = int(child.find('watts').text)
						
				if watts > 0 :		
					print "Temperature: ", temp
					print "Power: ", watts
				
	
	except serial.SerialTimeoutException:
		print "TimeOut Error"
	except serial.SerialException:
		print "serial Error"
	except KeyboardInterrupt:
		print "Closing down"
		keepLooping = False
		

ser.close()


	

