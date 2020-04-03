import threading
import time
import random
import socket as mysoc
import sys
def server():
    try:
        ss=mysoc.socket(mysoc.AF_INET, mysoc.SOCK_STREAM)
        print("[S]: Server socket created")
    except mysoc.error as err:
        print('{} \n'.format("socket open error ",err))

    server_binding=('',int(sys.argv[1]))
    ss.bind(server_binding)
    ss.listen(1)
    host=mysoc.gethostname()
    print("[S]: Server host name is: ",host)
    localhost_ip=(mysoc.gethostbyname(host))
    print("[S]: Server IP address is  ",localhost_ip)
    csockid,addr=ss.accept()
    print ("[S]: Got a connection request from a client at", addr)

# send a intro  message to the client.
    msg="Welcome to the ts2 DNS system"
    csockid.send(msg.encode('utf-8'))

    fp = open("PROJ2-DNSTS2.txt", 'r')
    lines = fp.readlines()
    dns = []
    for L in lines:
        entry = L.strip().split(' ')
        dns.append(entry)
#   finishes storing of each entry of table via lists
    for entry in dns:
        print(entry)
    fp.close()
#   entry look e.g.: ['qtsdatacenter.aws.com', '128.64.3.2', 'A']



    while 1:
        hostname = csockid.recv(4096)
        hostname = hostname.decode('utf-8')

        print(hostname)

        if(hostname == None or hostname == ""):
            break


        for entry in dns: #searches match between hostname and which entry of dns
            if entry[0].lower() == hostname.lower():
                print('Query successful')
                outputstr = " ".join(entry)
                csockid.send(outputstr.encode('utf-8'))
                break
                #csockid.send(outputstr.encode('utf-8'))

        print('not sending')
        #csockid.send(outputstr.encode('utf-8'))

        # Close the server socket
    ss.close()
    exit()


