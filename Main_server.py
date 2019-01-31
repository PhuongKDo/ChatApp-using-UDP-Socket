##############################################################
'''                
                    -------------
                    Group Members:
                    -------------
                    Phuong Do
                    Kareem DaSilva
                    Rick DeSaussure
                    -------------
                    12/03/2018
                    COMP 3825
                    Reliable File Transfer
                    -------------
                    Video Demo@:
                    https://www.youtube.com/watch?v=TatQBgg-JL8
'''
##############################################################

import socket
import base64
import threading  
import sys
import time
from tkinter import *
from tkinter import filedialog
from tkinter import Text, Tk
import struct
import pickle
import random

##############################################################
# create socket for ack
ack_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# store list of all the clients
list_of_clients = [] 
##############################################################
# store the transfered file here
received_file = 'RECEIVED_FILE.db'

# probability of loss packet
probability = 0.01

# next expected packet number
next_sequence = 0

# store acks
acks = []
##############################################################
'''
+ REF: https://stackoverflow.com/questions/1767910/checksum-udp-calculation-python
+ Finding the checksum of the data of "16-bits"
'''
##############################################################
def carry_bit(a, b):
    c = a + b
    return (c & 0xffff) + (c >> 16)
##############################################################
def find_checksum(data):
    result = 0
    for m in range(0, len(data), 2):
        summ = ord(str(data)[m]) + (ord(str(data)[m + 1]) << 8)
        result = carry_bit(result, summ)
    return (not result) & 0xffff
##############################################################
'''
+ Send the ack data to ack_socket() to server's side
+ Using pickle to save the object, load the data to ack server
'''
##############################################################
def send_ack(s, p):

    while True:

        while acks:
            data = acks.pop(0)
            s.sendto(pickle.dumps(data[0]), (data[1][0], p))
##############################################################
def listen(s, h, p):
    global next_sequence 
    global acks
    # listen for emoji

    # listen for text message
    try:
        while True:
            # smaller recvfrom size for text
            message = server_socket.recvfrom(50)
            msg_list.insert(END, ("<" + str(message[1]) + "> " + str(message[0].decode('utf-8'))))
            
            #store new client into the list if the client is not already in the list
            if message[1] not in list_of_clients:
                list_of_clients.append(message[1])
                client_list.insert(END, str(message[1]))
            else:
                pass
    except:
    	pass

    # listen for image file   
    try:
        while True:
            # slightly larger recvfrom size for image
            message2 = server_socket.recvfrom(60000)
            img_msg = message2[0].decode("utf-8")
            msg_list.insert(END, ("Successful! Server received EMOJI file of size: " + str(len(img_msg))))
            f = open("RECEIVED_EMOJI_FILE.png", "wb")
            # decode the image using base64 and then store it in an image file
            decode = base64.b64decode(img_msg)
            f.write(decode)
            f.close()
    except:
        pass

    # listen for big file transfer
    while True:
        # receive data from socket
        recvd_data, addr = s.recvfrom(1000000)
        #msg_list.insert(END, ("<" + str(addr) + "> " + str(recvd_data.decode())))
        msg_list.insert(END, ("Packet successfully received!"))
        # load all the received data into an object using pickle
        packet = pickle.loads(recvd_data)

        #-------------------------------------#
        # seq(32bit)
        seq = packet[0]
        # checksum(16bit)
        checksum = packet[1]
        # packet_type(16bit)
        packet_type = packet[2]
        # data
        data = packet[3]
        #-------------------------------------#

        # create random loss packet depending on probability
        if random.random() < probability:
            #print("[[Packet loss!]] Sequence Number: ", int('0b' + seq, 2))
            msg_list.insert(END, ("[[Packet loss!]] Sequence Number: " + str(int('0b' + seq, 2))))
        # if greater than probability, packet is received   
        else:
            # calculate the data using find_checksum() method
            re_checksum = find_checksum(data)

            # if checksum matches
            if int('0b' + seq, 2) == next_sequence and re_checksum == checksum:
                # print("<< Receive >> ", int('0b' + seq, 2))
                msg_list.insert(END, ("<< File Receive! >> " + str(int('0b' + seq, 2))))

                # if package received, move to the next packet
                next_sequence += 1

                # make acknowledgement using z.fill() to fill 32 bits and 16 bits ack, then insert into ack[]
                acks.append([[bin(next_sequence)[2:].zfill(32), bin(0)[2:].zfill(16), '1010101010101010'], addr])

                # write data to file
                with open(received_file, 'ab') as f:
                    f.write(data)
            else:
                continue
##############################################################
def conn(event=None):
    global HOST
    global PORT
    global server_socket
    
    # set new ip/port if it's different from default
    HOST=ip_e.get("1.0","end-1c")
    PORT=int(prt_e.get("1.0","end-1c"))
    
    msg_list.insert(END, ("Server << " + HOST  +" >> is connected"))
##############################################################
'''
+ SERVER GUI: Using Tkinter
'''
##############################################################
# set tkinter to display GUI
root = Tk()
root.title("SERVER T.I.M | Tiger Instant Messager")
root.resizable(width=False, height=False)
root.geometry('550x650')
##############################################################
#----------------------------header--------------------------#
header_frame = Frame(root)

# tiger image for header 
photo_1=PhotoImage(file="icon_TIM.png")
lab_1 = Label(root, image=photo_1)
lab_1.pack()

# label for connection information
lab_2 = Label(header_frame, text="_________________________Connection information_________________________ ")
lab_2.pack(side=LEFT, fill=BOTH, expand=TRUE)
lab_2.configure(fg='#e95d00', font=("Orator Std", 8))

header_frame.pack(side=TOP,fill=BOTH,expand=TRUE)
##############################################################
#---------------------connecting labels----------------------#
conn_frame =Frame(root)

# label for ip address
ip = Label(conn_frame, text="IP Address: ")
ip.configure(fg='#ff6600', font=("Consolas", 9))
ip.pack(side=LEFT, fill=BOTH, expand=TRUE)

# label for port
prt = Label(conn_frame, text="PORT:")
prt.configure(fg='#ff6600', font=("Consolas", 9))
prt.pack(side=LEFT, fill=BOTH, expand=TRUE)

conn_frame.pack(side=TOP,fill=BOTH,expand=TRUE)
##############################################################
#----------------------connecting entries--------------------#
connection_frame =Frame(root)

# entry for ip address
ip_e = Text(connection_frame, height=2, width=5)
ip_e.configure(background='#161616', fg='#ff6600', font=("Consolas", 14))
ip_e.pack(side=LEFT, fill=BOTH, expand=TRUE)

# entry for port
prt_e = Text(connection_frame, height=2, width=5)
prt_e.configure(background='#161616', fg='#ff6600', font=("Consolas", 14))
prt_e.pack(side=LEFT, fill=BOTH, expand=TRUE)

connection_frame.pack(side=TOP,fill=BOTH,expand=TRUE)
##############################################################
#----------------------connecting buttons--------------------#
top_frame = Frame(root)

# label for connect to server
lab_7 = Label(root, text="______________________________Connect to Server_____________________________ ")
lab_7.configure(fg='#e95d00', font=("Orator Std", 8))
lab_7.pack(side=TOP, fill=BOTH, expand=TRUE)

# button for connect
b = Button(top_frame, text="Connect", command=conn)
b.configure(background='#ffd6be', fg='#232323', font=("Consolas", 10))
b.pack(side=LEFT, fill=BOTH, expand=TRUE)

top_frame.pack(side=TOP,fill=BOTH,expand=TRUE)
##############################################################
#----------------------chatbox frame-------------------------#
messages_frame = Frame(root)

# create scrollbar for chatbox
scrollbar = Scrollbar(messages_frame)

# label for chatbox
lab_4 = Label(root, text="______________________________ChatBox_____________________________ ")
lab_4.configure(fg='#e95d00', font=("Orator Std", 8))
lab_4.pack(side=TOP, fill=BOTH, expand=TRUE)

# display chatbox message
msg_list = Listbox(messages_frame, height=10, width=40, yscrollcommand=scrollbar.set)
scrollbar.pack(side=RIGHT, fill=Y)
msg_list.pack(side=LEFT, fill=BOTH,expand=TRUE)
msg_list.configure(background='#161616', fg='#ff6600', font=("Consolas", 14))

messages_frame.pack(side=TOP, fill=BOTH,expand=TRUE)
##############################################################
#----------------client list frame---------------------------#
client_list_frame = Frame(root)

# label for list of clients
lab_8= Label(root, text="______________________________List of Clients_____________________________ ")
lab_8.configure(fg='#e95d00', font=("Orator Std", 8))
lab_8.pack(side=TOP, fill=BOTH, expand=TRUE)

# create scroll bar for list of clients
scrollbar = Scrollbar(client_list_frame)

# display chatbox message
client_list = Listbox(client_list_frame,height=5, width=50,  yscrollcommand=scrollbar.set)
scrollbar.pack(side=RIGHT, fill=Y)
client_list.pack(side=LEFT, fill=BOTH,expand=TRUE)
client_list.configure(background='#84eef8', fg='#161616', font=("Consolas", 11))

client_list_frame.pack(side=BOTTOM, fill=BOTH,expand=TRUE)

##############################################################
'''
+ Set a default IP address and port to receive incoming datas.
+ Bind the IP address and port.
'''
##############################################################
# default ip and port
HOST = '127.0.0.1'
PORT = 33300

#set up server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((HOST,PORT))
msg_list.insert(END, ("Server is ONLINE."))
##############################################################
'''
+ Using multithreading, listen for text and image incoming datas.
'''
##############################################################
# create a thread to listen for text input and packages
threading.Thread(target=listen, args=(server_socket, HOST, PORT)).start()
# create a thread to listen to ack socket data
threading.Thread(target=send_ack, args=(ack_socket, 33000)).start()
##############################################################
# display text in list
pathlabel = Label(root)
pathlabel.pack()
##############################################################
# end GUI
root.mainloop()
##############################################################
