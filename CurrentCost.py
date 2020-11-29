import serial
import xml.etree.ElementTree as ET
import datetime
import time
import paho.mqtt.client as mqtt 

mqttBroker ="192.168.54.30" 

client = mqtt.Client(client_id="CurrentCost")
client.connect(mqttBroker) 


ser = serial.Serial(port='/dev/tty.usbserial-DN03ZPK9',
                    baudrate=2400,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=120)

ser.close()
ser.open()




def getStream():
	keepLooping = True
	inputBuffer = ""
	receiving = True
	while receiving == True and keepLooping == True:
		try:
			if ser.in_waiting > 0:
				x = ser.read(ser.in_waiting)
				inputBuffer = inputBuffer + str(x, 'utf-8')
				
				if inputBuffer.find("</msg>") > 0:
					tempbuf = inputBuffer.split("</msg>", 1)
					inputBuffer = tempbuf[1]
					tempbuf[0] = tempbuf[0]+"</msg>"
					
					root = ET.fromstring(tempbuf[0])

					temp = 0
					watts = 0

					for child in root:
						if child.tag == "tmpr" :
							temp = float(child.text)
						if child.tag == "ch1" :
							watts = int(child.find('watts').text)
							
					if watts > 0 :	
						receiving = False
						return temp, watts	
						#print("Temperature: ", temp)
						#print("Power: ", watts)									
						

		except serial.SerialTimeoutException:
			print ("TimeOut Error")
		except serial.SerialException:
			print ("serial Error")
		except KeyboardInterrupt:
			print ("Closing down")
			keepLooping = False



#def main():
looping = True
while(looping):
	try:
		temp, watts = getStream()
		print("Temperature = ", temp)
		print("Power = ", watts)
		time.sleep(0.5)
		client.publish("homeassistant/currentcost/temperature", temp)
		client.publish("homeassistant/currentcost/power", watts)


	except KeyboardInterrupt:
			print ("Closing down")
			looping = False
	

# Close down connection. A better way to do this would be to create
# a class to hold the connection objects, which would allow us to leave
# the io.adafruit.com connection open all the time. Version 02....

ser.close()

#if __name__ == "__main__":
#	main()