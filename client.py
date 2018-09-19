# coding=utf-8
import socket, os, sys, threading, struct, time, hashlib

def generateCheckSum(package):
	print(package)
	checksum = hashlib.md5()
	checksum.update(package)
	return checksum.digest()

def generatePackage(seqNum, line):
	timestamp = time.time()

	# Packing Message #
	seq = struct.pack("!q", seqNum)
	seconds = struct.pack('!q', int(timestamp))
	nanoseconds = struct.pack('!l', int((timestamp-int(timestamp))*pow(10,9)))
	msgSize = struct.pack("!h", len(line))
	msg = line.encode('latin1')

	partialPackage = seq + seconds + nanoseconds + msgSize + msg
	
	checksum = generateCheckSum(partialPackage)

	return partialPackage + checksum

def waitPackageAck(currentPackage, lastReceivedAck, window, udp, dest):
	print('Waiting')

	ackPackage = udp.recvfrom(36)[0]
	print('Ack', ackPackage)
	
	seqnum = ackPackage[0:8]
	sec = ackPackage[8:16]
	nsec = ackPackage[16:20]
	receivedChecksum = ackPackage[20:36]
	
	checksum = generateCheckSum(seqnum + sec + nsec)

	seqnum = struct.unpack('!q', seqnum)[0]

	if(checksum == receivedChecksum):
		print('Received correct Ack, move window!')
		if(lastReceivedAck == seqnum):
			window[0][1] = 1
			window.pop()

			while(window[0][1] == 1):
				window.pop()
			
			if(currentPackage):
				udp.sendto(currentPackage, dest)
		
		else: 
			window[seqnum][1] = 1

	else:
		print('Received incorrect Ack, should resend the package')
		udp.sendto(sentPackages[seqnum])

def main(filePath, address, windowSize, timeout, errorProbability):

	[HOST, PORT] = address.split(':')
	udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	dest = (HOST, int(PORT))

	seqNum = 0
	lastSentPackage = 0
	lastReceivedAck = 0
	window = []

	file = open(filePath, "r") 
	for line in file:
		currentPackage = generatePackage(seqNum, line)
		
		print('\n************** Package **************\n')
		print(currentPackage)

		if(len(window) < windowSize):
			print('Sending')
			udp.sendto(currentPackage, dest)
			window.append((currentPackage, 0))
			lastSentPackage += 1

		else:
			waitPackageAck(currentPackage, lastReceivedAck, window, udp, dest)

		print('Ending ~')

	# while(len(sentPackages) !== receivedPackages):
	# 	waitPackageAck(null, receivedPackages)

	udp.close()

if __name__ == "__main__":
	main(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), float(sys.argv[5]))

# Run command: python client.py teste.txt 127.0.0.1:5000 1 1 1
