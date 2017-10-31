#!/usr/bin/python

#Adapted from Meatball's netxml-csv script by t0ddpar0dy

from lxml import etree
import os
import sys
import math

def run():
	
	if len(sys.argv) != 3:
		print "[*] Usage: %s input output" % sys.argv[0]
	else:
		output_file_name = sys.argv[2]
		input_file_name = sys.argv[1]
		if input_file_name != output_file_name:
			try:
				output = file(output_file_name, 'w')
			except:
				print "[-] Unable to create output file '%s' for writing." % output_file_name
				exit()

			try:
				doc = etree.parse(input_file_name)
			except:
				print "[-] Unable to open input file: '%s'." % input_file_name
				exit()

			print "\n>>>Parsing '%s.'" % input_file_name
			sys.stdout.write(">>>CSV written to '%s' " % output_file_name)
			output.write("BSSID,Privacy,ESSID,Lat,Long\n")
			result = parse_net_xml(doc)
			output.write(result[0])
			sys.stdout.write("\n[#] Complete.\r\n")
			sys.stdout.write("\nHere are your results\r\n\n")

			sys.stdout.write("[?] Your FURTHEST %s\n" % result[1])
			sys.stdout.write("[?] Your HIGHEST %s\n" % result[2])
			sys.stdout.write("[+] Your Total Calculated Points: %s\n\n" % result[3])

def parse_net_xml(doc):
	result = ""
	furthest = [0, "", 0, 0]
	highest = [0, ""]
	total = len(list(doc.getiterator("wireless-network")))
	tenth = total/10
	count = 0
	pointsWEP = 0
	pointsWPA = 0
	pointsWPA2 = 0
	pointsOPN = 0
	pointsFOX = 0
	pointsNeg = 0
	totalPoints = 0

	for network in doc.getiterator("wireless-network"):
		count += 1
		if (count % tenth) == 0:
			sys.stdout.write(".")
		type = network.attrib["type"]
		channel = network.find('channel').text
		bssid = network.find('BSSID').text
		#E0:3F:49:9E:00:60
		if bssid == '00:02:6F:C8:EF:80':
			pointsFOX = 1000

		if type == "probe" or channel == "0":
			continue

		encryption = network.getiterator('encryption')
		privacy = ""
		cipher = ""
		auth = ""
		if encryption is not None:
			for item in encryption:
				if item.text.startswith("WEP"):
					privacy = "WEP"
					cipher = "WEP"
					pointsWEP += 50
					auth = ""
					break
				elif item.text.startswith("WPA"):
					if item.text.endswith("PSK"):
						auth = "PSK"
					elif item.text.endswith("AES-CCM"):
						cipher = "CCMP " + cipher
					elif item.text.endswith("TKIP"):
						cipher += "TKIP "
				elif item.text == "None":
					privacy = "OPN"
					pointsOPN += 10

		cipher = cipher.strip()

		if cipher.find("CCMP") > -1:
			privacy = "WPA2"
			pointsWPA2 += 1

		if cipher.find("TKIP") > -1:
			privacy = "WPA"
			pointsWPA += 5

		power = network.find('snr-info')
		dbm = ""
		if power is not None:
			dbm = power.find('max_signal_dbm').text

		if int(dbm) > 1:
			dbm = power.find('last_signal_dbm').text

		if int(dbm) > 1:
			dbm = power.find('min_signal_dbm').text

		ssid = network.find('SSID')

		essid_text = ""
		if ssid is not None:
			essid_text = network.find('SSID').find('essid').text
			if essid_text == 'xfinitywifi':
				pointsNeg += 1

		gps = network.find('gps-info')
		lat, lon = '', ''
		if gps is not None:
			lat = network.find('gps-info').find('avg-lat').text
			lon = network.find('gps-info').find('avg-lon').text
			newAlt = network.find('gps-info').find('avg-alt').text

			newDist = calculateDistance(float(lat), float(lon))
			if newDist > furthest[0]:
				furthest[0] = newDist
				furthest[1] = essid_text
				furthest[2] = lat
				furthest[3] = lon
			if float(newAlt) > highest[0]:
				highest[0] = float(newAlt)
				highest[1] = essid_text

		# print "%s,%s,%s,%s,%s,%s,%s\n" % (bssid, channel, privacy, cipher, auth, dbm, essid_text)
		result += "%s,%s,%s\n" % (bssid, privacy, essid_text)
		totalPoints = pointsFOX + pointsWPA + pointsWPA2 + pointsOPN - pointsNeg
	
	sys.stdout.write("\n\n[+] FOX %d\n[+] WPA %d\n[+] WPA2 %d\n[+] OPN %d\n[-] XFINITYWIFI %d\n" % (pointsFOX, pointsWPA, pointsWPA2, pointsOPN, pointsNeg))

	return result, furthest, highest, totalPoints

def calculateDistance(x2,y2):
	#CTU Parking lot coords: 38.895260, -104.835075
	dist = math.sqrt((x2 - (38.895260))**2 + (y2 - (-104.835075))**2)
	return dist

def associatedClients(network, bssid, essid_text):
	clients = network.getiterator('wireless-client')

	if clients is not None:
		client_info = list()
		for client in clients:
			mac = client.find('client-mac')
			if mac is not None:
				client_mac = mac.text
				snr = client.find('snr-info')
				if snr is not None:
					power = client.find('snr-info').find('max_signal_dbm')
					if power is not None:
						client_power = power.text
						c = client_mac, client_power, bssid, essid_text
						client_info.append(c)

		return client_info

if __name__ == "__main__":
	  run()

