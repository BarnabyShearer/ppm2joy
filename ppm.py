#!/usr/bin/env python
"""
	vjoy module with decodes a 6 channel PPM signal captured via SUMP
	NOTE: Too slow to be useful.

	@author: bWare@iWare.co.uk
	@license: GPL v3
"""

import vjoy
import serial
import select
import thread
import time

channels=[200,200,200,200,200,200]

port = serial.Serial("/dev/ttyUSB0", 115200, timeout=0.02)

#Reset BP
port.write("\x00")
port.write("\x0F")
select.select([], [], [], 0.02)
port.read(2000)
port.flush()

#Enter SUMP mode
port.write("\x00\x00\x00\x00\x00")
select.select([], [], [], 0.02)

def getVJoyInfo():
	return {
		'name':       'PPM via SUMP',
		'relaxis':    [],
		'absaxis':    [vjoy.ABS_X, vjoy.ABS_Y, vjoy.ABS_RX, vjoy.ABS_RY, vjoy.ABS_THROTTLE, vjoy.ABS_RUDDER],
		'feedback':   [],
		'maxeffects': 0,
		'buttons':    []
	}

def doVJoyThink():
	global channels
	time.sleep(.01) # Run other thread
	events = []
	events.append([vjoy.EV_ABS, vjoy.ABS_X, channels[3]])
	events.append([vjoy.EV_ABS, vjoy.ABS_Y, channels[2]])
	events.append([vjoy.EV_ABS, vjoy.ABS_RX, channels[0]])
	events.append([vjoy.EV_ABS, vjoy.ABS_RY, channels[1]])
	events.append([vjoy.EV_ABS, vjoy.ABS_THROTTLE, channels[5]])
	events.append([vjoy.EV_ABS, vjoy.ABS_RUDDER, channels[4]])
	return events


def PoleInput():
	global channels
	global port

	while True:

		#Reset
		port.write("\x00")
		port.write("\x02")
		port.read(4) #1ALS

		#Trigger mask AUX
		port.write(chr(0b11000000))
		port.write(chr(0b00010000))
		port.write(chr(0b00000000))
		port.write(chr(0b00000000))
		port.write(chr(0b00000000))

		#<200kHz
		port.write(chr(0b10000000))
		port.write(chr(0b10000000))
		port.write(chr(0b00000010))
		port.write(chr(0b00000000))
		port.write(chr(0b00000000))

		#4K Samples
		port.write(chr(0b10000001))
		port.write(chr(0b00000000))
		port.write(chr(0b00000100))
		port.write(chr(0b00000000))
		port.write(chr(0b00000100))

		#Arm
		port.write("\x01")
	
		select.select([], [], [], 0.03)
	
		buf = [ord(x)==16 for x in port.read(4096)];
		buf.insert(True,0)
	
		chans = []
		chan = 0
		count = 0
		pulse = True
	
		try:
			while True:
				b = buf.pop()
				if not(pulse):
					if not(b): #end of channel
						pulse = True
						chans.append(count)
						chan += 1
						if chan==7:
							break;
						count = 0
					else:
						count += 1
				else:
					pulse = not(b)
		except IndexError:
			pass
	
		if len(chans)==7:
			#Valid frame
			keychan = chans.index(max(chans))
			for i in range(-6,0):
				channels[i] = chans[i+keychan]

thread.start_new_thread(PoleInput,())
