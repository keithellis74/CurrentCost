import serial
import xml.etree.ElementTree as ET
import datetime

'''
remoteMQTTuser = "ptbw2000"
remoteMQTTpassword = "!!! CHANGE TO YOUR ADAFRUIT.IO KEY. REDACT BEFORE PUSHING !!!"
remoteMQTTtopic = "PVPower"
remoteMQTTtopic2 = "Temperature"

# You should not need to change anything below this line.

remoteMQTTbroker = "io.adafruit.com"
remoteMQTTport = 1883
'''



ser = serial.Serial(port='/dev/tty.usbserial-DN03ZPK9',
                    baudrate=2400,
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
		if ser.in_waiting > 0:
			x = ser.read(ser.in_waiting)
			inputBuffer = inputBuffer + str(x, 'utf-8')
			
			if inputBuffer.find("</msg>") > 0:
				tempbuf = inputBuffer.split("</msg>", 1)
				inputBuffer = tempbuf[1]
				tempbuf[0] = tempbuf[0]+"</msg>"
				
				root = ET.fromstring(tempbuf[0])

				temp = 0;
				watts = 0;

				for child in root:
					if child.tag == "tmpr" :
						temp = float(child.text)
					if child.tag == "ch1" :
						watts = int(child.find('watts').text)
						
				if watts > 0 :		
					print("Temperature: ", temp)
					print("Power: ", watts)									
					

	except serial.SerialTimeoutException:
		print ("TimeOut Error")
	except serial.SerialException:
		print ("serial Error")
	except KeyboardInterrupt:
		print ("Closing down")
		keepLooping = False

# Close down connection. A better way to do this would be to create
# a class to hold the connection objects, which would allow us to leave
# the io.adafruit.com connection open all the time. Version 02....

ser.close()