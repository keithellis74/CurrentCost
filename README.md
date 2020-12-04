# CurrentCost
CurrentCost Device to Home-Assistant

Original code by ptbw2000, modified by Keith Ellis

## Objectives
* Capture data from CurrentCost (Southern Electric current meter), readings every 6 seconds
* Record instant current usage
* Collect data over a period of 120 seconds and average it out, record average current usage
* Send instant current usage to MQTT server every 15 seconds (for Home Assistant to use)
* Send average current reading to Influx, for charting in Grafana

## Source data
The CurrentCost current meter has an RJ54 connector on the base, this has a serial connection which streams XML data every 6 seconds.

A two wire connection is needed, ground and data, this can be connected directly to a Raspberry Pi serial connection on the GPIO or via a serial to USB convertor and read in via the USB port.

The data comes out of the CurrentCost at 2400kbp/s

## Prerequisits
The following python libraries are required:
 * pyserial, install with 
 ```
 pip install pyserial
 ```
 * mqtt, install with 
 ```
 pip install paho-mqtt
 ```
 * You must have an mqtt broker setup and ready to receive the mqtt messages.  I will not cover this here, seek help from the internet.

 * influxDB
 ```
 pip install influxdb
 ```
