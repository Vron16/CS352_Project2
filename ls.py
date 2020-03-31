import socket as mysoc
import select, Queue, sys, threading

def handle_connection(client_connection_socket, ts1_hostname, ts1_listen_port, ts2_hostname, ts2_listen_port):
	# First, do a blocking recv call on connection_socket to get queried hostname from the client.
	# Then, create the inputs array, outputs array, and the array of message queues for the sockets.
	# Create 2 sockets, one for ts_1 and the other for ts_2, and put them into the inputs array.
	# Set both sockets to be nonblocking.
	# Put both sockets into the inputs array.
	# Send the queried hostname to both sockets.
	# Call select, with the inputs array and empty arrays for output and err and 5 second timeout.
	# Check if the size of the list we get back is 0 or 1.
	# If 1, then check socket received is the socket for ts_1 or ts_2.
	# Accordingly send back to connection_socket the same string + either ts1_hostname or ts2_hostname depending on which
	# socket we received. If the size was 0, send back to connection_socket Hostname - Error:HOST NOT FOUnD
	# Close the two sockets created and connection_socket and return.
	
	# Make sockets to communicate with ts1 and ts2 servers.
	try:
		ts1_ls_socket = mysoc.socket(mysoc.AF_INET, mysoc.SOCK_STREAM)
		print "[LS]: LS socket to communicate with TS1 server created"
	except mysoc.error as err:
		print "[LS]: Could not create socket to establish LS-TS1 connection due to error: ", str(err)
	ts1_hostname_ip = mysoc.gethostbyname(ts1_hostname)
	ts1_server_binding = (ts1_hostname_ip, ts1_listen_port)
	#ts1_ls_socket.setblocking(0)
	ts1_ls_socket.connect(ts1_server_binding)

	try:
		ts2_ls_socket = mysoc.socket(mysoc.AF_INET, mysoc.SOCK_STREAM)
		print "[LS]: LS socket to communicate with TS2 server created"
	except mysoc.error as err:
		print "[LS]: Could not create socket to establish LS-TS2 connection due to error: ", str(err)
	ts2_hostname_ip = mysoc.gethostbyname(ts2_hostname)
	ts2_server_binding = (ts2_hostname_ip, ts2_listen_port)
	#ts2_ls_socket.setblocking(0)
	ts2_ls_socket.connect(ts2_server_binding)

	# Keep servicing queried hostnames from the client until it is done.
	while 1:
		client_query = client_connection_socket.recv(4096).decode('utf-8').strip().lower()
		# If the query is 'done', then we break out of the loop and clean everything up.
		if (client_query == 'done'):
			ts1_ls_socket.send(client_query.encode('utf-8'))
			ts2_ls_socket.send(client_query.encode('utf-8'))	
			break
		print "[LS]: Received request to find IP address for the hostname:", client_query
		
		# Send the client query to both the TS 1 and TS 2 servers.
		ts1_ls_socket.send(client_query.encode('utf-8'))
		ts2_ls_socket.send(client_query.encode('utf-8'))

		# Now, call select with both TS server sockets as inputs so it listens to both simultaneously with a timeout of 5 seconds.
		ts_response_sockets, _, _ = select.select([ts1_ls_socket, ts2_ls_socket], [], [], 5)
		# If after 5 seconds no sockets are readable, then hostname is not found. Send error message back.
		if (len(ts_response_sockets) == 0):
			print "[LS]: Queried hostname is not in TS 1 or TS 2's tables. Error:HOST NOT FOUND."
			error_response = client_query + " - Error:HOST NOT FOUND"
			client_connection_socket.send(error_response.encode('utf-8'))
		# Otherwise, if exactly one socket is readable, then we can send that back to the client.
		elif (len(ts_response_sockets) == 1):
			if (ts_response_sockets[0] is ts1_ls_socket):
				address_response = ts1_ls_socket.recv(4096)
				address_response = address_response + " " + ts1_hostname
				print "[LS]: Found queried hostname in TS 1. Sending following string back to client:", address_response
				client_connection_socket.send(address_response.encode('utf-8'))
			elif (ts_response_sockets[0] is ts2_ls_socket):
				address_response = ts2_ls_socket.recv(4096)
				address_response = address_response + " " + ts2_hostname
				print "[LS]: Found queried hostname in TS 2. Sending following string back to client:", address_response
				client_connection_socket.send(address_response.encode('utf-8'))
			else:
				raise ValueError("[LS]: Error - Received an unexpected socket.")
		else:
			for sock in ts_response_sockets:
				data = sock.recv(4096)
				print "The data is:", data
			#raise ValueError("[LS]: Error - Multiple sockets responded to the query. Check that the TS1.txt and TS2.txt files have no overlap.")
	# The client has indicated that it is done. We can now safely tear down the connections to the TS servers and to the client.
	ts1_ls_socket.close()
	ts2_ls_socket.close()
	client_connection_socket.close()
	return

# Load-balancing server task
def ls_server():
	if len(sys.argv) != 6:
		raise TypeError('[LS]: Expected 5 but received %d arguments.' % len(sys.argv))

	# The port that the root server will listen on is provided as the sole argument to the program call.
	ls_listen_port = int(sys.argv[1])
	# The hostname of the first top-level server.
	ts1_hostname = sys.argv[2]
	# The port that the first top-level server is listening on.
	ts1_listen_port = int(sys.argv[3])
	# The hostname of the second top-level server.
	ts2_hostname = sys.argv[4]
	# The port that the second top-level server is listening on.
	ts2_listen_port = int(sys.argv[5])

	# Attempts to create a socket for the load-balancing server to listen for clients from. Communicates with IPV4 via TCP.
	try:
		ls_server_socket = mysoc.socket(mysoc.AF_INET, mysoc.SOCK_STREAM)
		print "[LS]: Load-Balancing Server socket created."
	except mysoc.error as err:
		print "[LS]: Could not create socket for load server to listen to connections from due to error:", err

	# Bind the server socket to the IP address of the machine it is running on and the port provided as input. 
	host = mysoc.gethostname()
	print "[LS]: Load-balancing server host name is:", host
	host_ip = mysoc.gethostbyname(host)
	print "[LS]: Load-balancing server host IP address is:", host_ip 
	ls_server_binding = ('', ls_listen_port)
	# We're going to make this server socket to listen to clients non-blocking.
	#ls_server_socket.setblocking(0)
	ls_server_socket.bind(ls_server_binding)

	# Listen to up to 10 connections at a time from clients
	ls_server_socket.listen(10)

	# Now, begin accepting clients and handling them one at a time
	while 1:
		# Call accept to block and wait for any new incoming connection requests to the socket and accept them.
		client_connection_socket, addr = ls_server_socket.accept()
		print "[LS]: Received a connection request from a client at:", addr

		# Create a new thread to serve the client while the current thread continues listening for connections.
		connection_handler_thread = threading.Thread(name='connection_handler', target=handle_connection, args=(client_connection_socket, ts1_hostname, ts1_listen_port, ts2_hostname, ts2_listen_port))
		connection_handler_thread.start()

	ls_server_socket.close()
	return

ls_server()