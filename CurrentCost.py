import serial
import xml.etree.ElementTree as ET
import datetime
import Adafruit_IO as AIO

remoteMQTTuser = "ptbw2000"
remoteMQTTpassword = "!!! CHANGE TO YOUR ADAFRUIT.IO KEY. REDACT BEFORE PUSHING !!!"
remoteMQTTtopic = "PVPower"
remoteMQTTtopic2 = "Temperature"

# You should not need to change anything below this line.

remoteMQTTbroker = "io.adafruit.com"
remoteMQTTport = 1883


# MQTT callbacks.

def AIOconnected(client):
	# Connected function will be called when the client is connected to Adafruit IO.
	return()

def AIOdisconnected(client):
	# Disconnected function will be called when the client disconnects.
	return()


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
					
					AIOclient = AIO.MQTTClient(remoteMQTTuser, remoteMQTTpassword)
					
					# Setup the callback functions defined above.
					AIOclient.on_connect    = AIOconnected
					AIOclient.on_disconnect = AIOdisconnected

					# Connect to the Adafruit IO server.
					AIOclient.connect()

					# Now the program needs to use a client loop function to ensure messages are
					# sent and received.  There are a few options for driving the message loop,
					# depending on what your program needs to do.
					AIOclient.loop_background()

					# Publish data element to remote server. This is a blind send - we don't
					# check return values. I know, bad style.
					
					AIOclient.publish(remoteMQTTtopic, watts)
					AIOclient.publish(remoteMQTTtopic2, temp)

					# Close down connection. A better way to do this would be to create
					# a class to hold the connection objects, which would allow us to leave
					# the io.adafruit.com connection open all the time. Version 02....
					AIOclient.disconnect()
					
					
				
	
	except serial.SerialTimeoutException:
		print "TimeOut Error"
	except serial.SerialException:
		print "serial Error"
	except KeyboardInterrupt:
		print "Closing down"
		keepLooping = False
		

ser.close()


	

