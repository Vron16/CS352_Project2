import socket as mysoc
import sys
import threading

def handle_connection(connection_socket, ts_dns_table):
    # Using the client connection socket passed in from the main thread, wait to receive data from the
    # client using recv. Save the query in client_query after decoding it with UTF-8.
    client_query = connection_socket.recv(4096).decode('utf-8').strip().lower()
    print("[TS1]: Received request to find IP address for the hostname:", client_query)
    # Now, check if the rs_dns_table dictionary contains a key corresponding to the hostname queried by the
    # client. If so, create the string as it appeared in the file and send it back to the client. Otherwise,
    # send ts_information so that client can connect with the top-level server.
    if client_query in ts_dns_table:
        address_response = ts_dns_table[client_query]
        print("[TS1]: Query Found.Sending back to LS:", address_response)
        connection_socket.send(address_response.encode('utf-8'))
    else:
        error_response = client_query + " - Error:HOST NOT FOUND"
        print("[TS1]: Could not locate query in top-level server DNS table. Error:HOST NOT FOUND.")
        connection_socket.send(error_response.encode('utf-8'))
    # Close the connection with the client and return
    connection_socket.close()
    return


# This function is what runs at startup, populates the top-level server's DNS table, sets up and binds to the socket based on the specified
# port, and then listens for incoming connections. When they are received, a new child thread is spawned to handle it.
def ts_server():
    if len(sys.argv) != 2:
        raise TypeError('[TS1]: Expected 2 but received %d arguments.' % len(sys.argv))

    # The port that the root server will listen on is provided as the sole argument to the program call.
    port = int(sys.argv[1])

    # Opens PROJI-DNSTS1.txt and reads in contents line by line. All lines that end with the flag A are stored
    # into a dictionary. Any other flag raises an error.

    input_file = open("PROJ2-DNSTS1.txt", "r")
    line = input_file.readline()
    ts_dns_table = {}

    while line:
        line_parsed = line.split()
        hostname = line_parsed[0].strip()
        hostname_lowercase = hostname.lower()
        ip_address = line_parsed[1]
        flag = line_parsed[2]
        if flag == 'A':
            ts_dns_table[hostname_lowercase] = line.strip()
        else:
            raise ValueError("[TS1]: Error - PROJ2-DNSTS1.txt file contains unrecognized flags.")
        line = input_file.readline()

    input_file.close()

    # Attempts to create a socket for the top-level server to listen from. Communicates with IPV4 via TCP.
    try:
        ts_server_socket = mysoc.socket(mysoc.AF_INET, mysoc.SOCK_STREAM)
        print("[TS1]: Server socket created")
    except mysoc.error as err:
        print("[TS1]: Could not create socket for root server to listen to connections from due to error:", err)

    # Bind the server socket to the IP address of the machine it is running on and the port provided as input.
    host = mysoc.gethostname()
    print("[TS1]: Top-level server host name is:", host)
    host_ip = mysoc.gethostbyname(host)
    print("[TS1]: Top-level server host IP address is:", host_ip)
    ts_server_binding = ('', port)
    ts_server_socket.bind(ts_server_binding)

    # Listen to up to 10 connections at a time from clients
    ts_server_socket.listen(10)

    while 1:
        # Call accept to block and wait for any new incoming connection requests to the socket and accept them.
        connection_socket, addr = ts_server_socket.accept()
        print("[TS1]: Received a connection request from a client at:", addr)

        # Create a new thread to serve the client while the current thread continues listening for connections.
        connection_handler_thread = threading.Thread(name='connection_handler', target=handle_connection,
                                                     args=(connection_socket, ts_dns_table))
        connection_handler_thread.start()

    ts_server_socket.close()
    return


ts_server()