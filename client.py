import socket as mysoc
import sys

# Load-balancing server client task
def ls_client():
	if len(sys.argv) != 3:
		raise TypeError('[C]: Expected 2 but received only %d arguments.' % len(sys.argv))
	ls_hostname = sys.argv[1]
	ls_listen_port = int(sys.argv[2])
	
	# Create socket to communicate with the load balancing server
	try:
		ls_client_socket = mysoc.socket(mysoc.AF_INET, mysoc.SOCK_STREAM)
		print "[C]: Client socket to communicate with load-balancing server created"
	except mysoc.error as err:
		print "[C]: Could not create socket to establish client-load balancing server connection due to error: ", str(err)

	# Create tuple that represents the IP address and port number that the load-balancing server is listening at, then connect socket to that tuple
	ls_hostname_ip = mysoc.gethostbyname(ls_hostname)
	ls_server_binding = (ls_hostname, ls_listen_port)
	ls_client_socket.connect(ls_server_binding)

	# Open the text file containing all the hostnames whose IP addresses we want from the DNS servers. Also create/open an output file to
	# write the hostnames with their corresponding IP addresses (or an error if the IP address did not exist for that hostname in both the
	# root and top-level servers' look-up tables)
	try:
		input_file = open("PROJ2-HNS.txt", "r")
		output_file = open("RESOLVED.txt", "w+")
	except IOError as err:
		print "[C]: Could not open input/output file due to error: ", str(err)

	 # Read hostname queries line by line
	hostname = input_file.readline()
	while hostname:
		# Print hostname query to terminal console
		print "[C]: The client is about to query the DNS system for the following hostname: ", str(hostname.strip())

		# Send the query to the load-balancing server
		ls_client_socket.send(hostname.strip().encode('utf-8'))

		# Receive response from load-balancing server
		ls_response = ls_client_socket.recv(4096).decode('utf-8')

		# We've found the IP address for the query. Simply output to terminal and write to output file.
		print "[C]: Found the following entry for the requested hostname: ", str(ls_response)
		output_file.write(ls_response + str("\n"))
		
		hostname = input_file.readline()

	ls_client_socket.send('done'.encode('utf-8'))
	
	input_file.close()
	output_file.close()
	ls_client_socket.close()
	return

ls_client()