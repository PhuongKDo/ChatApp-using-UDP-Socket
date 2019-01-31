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
from tkinter import *
from tkinter import filedialog
import threading
import time
import base64
import struct
import sys
from tkinter import Text, Tk
import pickle

##############################################################
QuitSet=['/q','/qc','QQ' 'quit', 'Quit', 'QUIT', 'qUIT']
##############################################################
file = ''
# Window size
N = 200
# Max Segment Size 
MSS = 2000
##############################################################
# Create socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
##############################################################
# Store all the packets
packets = [] 
# After receiving ACK, put new packets into new_buffer and send
new_buffer = []  
# Create a thread lock with function acquire() and release()
lock = threading.Lock()
# Check ack
ack = 0

# set current time
cur_time = 0
start_time = 0

# set current data
most_recent_data = 0
most_recent_prepared = 0
##############################################################
t1 = threading.Thread()
t2 = threading.Thread()
t3 = threading.Thread()
ack_socket = socket.socket()
##############################################################
'''
+ REF: https://stackoverflow.com/questions/1767910/checksum-udp-calculation-python
+ Finding the checksum of the data 
+ Checksum is the sum of 16bits data that can carry over 
    for comparison to detect errors in data.
'''
##############################################################
# When data overflows, add the beginning bit to the sum
def carry_bit(a, b):
    c = a + b
    return (c & 0xffff) + (c >> 16)
##############################################################
# Calculate the checksum of the data
def find_checksum(data):
    result = 0
    for m in range(0, len(data), 2):
        # Using ord to return the unicode of the data
        data_sum = ord(str(data)[m]) + (ord(str(data)[m+1]) << 8)
        # Check the data_sum incase of bit needing to carry over
        result = carry_bit(result, data_sum)
    return (not result) & 0xffff
##############################################################
# Send packets
def socket_send(data):
    global most_recent_data
    global lock

    # acquire lock so the data synchronize
    lock.acquire()
    
    while data:
        p = data.pop(0)
        client_socket.sendto(pickle.dumps(p), (HOST, PORT))
        #print("Send packet: ", int('0b' + p[0], 2))
        msg_list.insert(END, ("Send packet: " + str(int('0b' + p[0], 2))))
        # update the current sent data
        most_recent_data= max(most_recent_data, int('0b' + p[0], 2))

    lock.release()
##############################################################
# Listen ACK thread
def listen_ack(s, h):
    global new_buffer
    global ack
    global most_recent_data
    global most_recent_prepared
    global cur_time
    global packets
    # Listen to ACK
    while True:
        # receive ack packet
        ack_packet, addr = s.recvfrom(1024)
        ack_packet = pickle.loads(ack_packet)
        # get ack number(next expected packet)
        ack = int('0b' + ack_packet[0], 2)  
        #print(" \r\n<< Received >> ACK: ", ack)
        msg_list.insert(END, "<< Received >> ACK: " + str(ack))
        if len(packets) > ack:
            # the next packet of "most recent send packet" or "most recent planed to send packet"
            # is the smallest packet we should send
            # "ack + N - 1" is the largest packet number we should send
            cur_time = time.time()
            for j in range(max(most_recent_data + 1, most_recent_prepared + 1), min(len(packets), ack+N)):
                # In this thread, only send new packet (slide the window to next)
                most_recent_prepared = max(most_recent_prepared, j)
                new_buffer.append(packets[j])
                print("<< Preparing >> ", j)
                msg_list.insert(END, ("<< Preparing >> " + str(j)))
        elif ack == len(packets):
            #print("Packet successfully sent!! ", "<< TIME >> ", time.time()-start_time)
            msg_list.insert(END, str("Packet successfully sent!! << TIME >>: " + str(time.time()-start_time)))
            # close threads once the packet is sent
            t1.start()
            t2.start()
            t3.start()
            t1.join()
            t2.join()
            t3.join()
            # close ack socket once packet is sent
            a_sock = ack_socket
            ack_socket.close()
            # close client socket
            client_socket.close()
            # reset default variables once packet is sent
            packets = [] 
            new_buffer = []  
            ack = 0
            break
##############################################################
# Send thread
def send_packet(h, p):
    global new_buffer

    while True:
        # send packet from new_buffer
        while new_buffer:
            socket_send(new_buffer)
##############################################################
def timer():
    global cur_time
    global start_time

    resend_buffer = []
    while True:
        # set timer
        if time.time() >= cur_time + 0.1:
            # Prepare resend packets
            for k in range(ack, min(len(packets), ack+N)):
                resend_buffer.append(packets[k])
            #print(" << Timeout >> Sequence Number: ", ack)
            msg_list.insert(END," << Timeout >> Sequence Number: " + str(ack))
            socket_send(resend_buffer)
            cur_time = time.time()
        if ack == len(packets):
            #print("Success!!!", " << TIME >>: ", time.time()-start_time)
            msg_list.insert(END, str("Success!!! << TIME >>: " + str(time.time()-start_time)))
            break
##############################################################
# Open filedialog menu and pick a file type
# Test thus far are file type of: .pdf, .txt, .png, .pdf
def input_file(event=None):
    global file
    # testcase file to pick during testing
    # testcase_txt.txt
    # testcase_pdf.pdf
    # testcase_img.png
    # testcase_db.db
    file = filedialog.askopenfilename()
    init_readfile(file)
##############################################################
def input_emoji_img(emoji_img):
    global file
    #pick a file
    file = emoji_img
    init_readfile(file)
##############################################################
# Read file and make packets
def init_readfile(selected_file):
	#inituate file sharing threads
    init_filesharing()
    #input and read file
    file = selected_file
    #calculate the size of the file
    msg_list.insert(END, ("Sending packet of size: " + str(len(file))))
    seq = 0
    with open(file, 'rb') as f:

        while True:
            # Split file by MSS (Max Segment Size)
            split_file = f.read(MSS) 

            # if file file exists, find the checksum
            if split_file:
                # Calculate checksum
                checksum = find_checksum(split_file)
                # Make acknowledgement using z.fill() to fill 32 bits and 16 bits ack, then insert into ack[]
                packets.append([bin(seq)[2:].zfill(32), checksum, '0101010101010101', split_file])
                seq += 1
            else:
                break

    # Build packets to be sent at window size in the very beginning, then listen to ACK and send packets
    # (Hence this part only execute once)
    for i in range(min(N, len(packets))):
        new_buffer.append(packets[i])

    # set current time
    cur_time = time.time()
    start_time = time.time()

    # set current data
    most_recent_data = 0
    most_recent_prepared = min(N-1, len(packets)-1)

####################### Send Text ############################
def send_message(event=None):
    global HOST
    global PORT
    global f
    global msg_list

    # set up client socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # message input from user's entry
    msg = my_msg.get()

    # keep the entry area blank for new text message input
    my_msg.set("")

    # send message to server socket
    client_socket.sendto(msg.encode(),(HOST,PORT))

    # close client application
    if msg in QuitSet:
        s.close()
        root.quit()

    msg_list.insert(END, ("<< ME >> " + msg))
    c_log = ">> " + msg

    # insert messages into chathistory
    f.write(str(c_log)+"\r\n")

    # close chathistory
    if msg in QuitSet:
        f.write('Quit command entered, bye')
        c_log = 'Quit command entered, bye'
        msg_list.insert(END, ">> " + c_log)
        f.write(str(c_log)+"\r\n")
        f.close()

    # close client socket once 
    client_socket.close()

    # restart client socket for new incoming data
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

##############################################################
def conn():
	global HOST
	global PORT
	global client_socket
	global f

	c_log=''

    # set new ip/port if not default from user entry
	HOST=ip_e.get("1.0","end-1c")
	PORT=int(prt_e.get("1.0","end-1c"))
    
	msg_list.insert(END, "Connecting to Host: " + HOST + " Port: " + str(PORT)+'...')

	# try-catch to check if file exists
	try:   
		f = open("chat_history.txt", "a+")
	except Exception as e:
		print('problem: '+e)
	finally:
		f=open("chat_history.txt", "a+")

    # insert time and connection into chat history
	f.write("\n==========================================================\n")
	localtime=time.asctime(time.localtime(time.time()))
	c_log = "Connecting to " + HOST + " : " + str(PORT) + " @ "+localtime
	f.write(str(c_log)+"\r\n")

    # alert server that client joined
	msg = "Client << " + HOST +" >> connected to server."
	client_socket.sendto(msg.encode(),(HOST,PORT))

##############################################################
# pick emoji 1 / Display chosen emoji in emoji tkinter Frame
# use base64 to encode the image file as a string and send it through socket
def send_emoji1(event=None):
    #emoji is 64x64x px
    myimage = open("1.png", "rb")
    encode = base64.b64encode(myimage.read())
    client_socket.sendto(encode,(HOST,PORT))
    msg_list.insert(END, ">> Sending emoji to server...")
# Pick emoji 2 / Display chosen emoji in emoji tkinter Frame
def send_emoji2(event=None):
    myimage = open("2.png", "rb")
    encode = base64.b64encode(myimage.read())
    client_socket.sendto(encode,(HOST,PORT))
    msg_list.insert(END, ">> Sending emoji to server...")
# Pick emoji 3 / Display chosen emoji in emoji tkinter Frame
def send_emoji3(event=None):
    myimage = open("3.png", "rb")
    encode = base64.b64encode(myimage.read())
    client_socket.sendto(encode,(HOST,PORT))
    msg_list.insert(END, ">> Sending emoji to server.")
# Pick emoji 4 / Display chosen emoji in emoji tkinter Frame
def send_emoji4(event=None):
    myimage = open("4.png", "rb")
    encode = base64.b64encode(myimage.read())
    client_socket.sendto(encode,(HOST,PORT))
    msg_list.insert(END, ">> Sending emoji to server...")
# Pick emoji 5 / Display chosen emoji in emoji tkinter Frame
def send_emoji5(event=None):
    myimage = open("5.png", "rb")
    encode = base64.b64encode(myimage.read())
    client_socket.sendto(encode,(HOST,PORT))
    msg_list.insert(END, ">> Sending emoji to server...")
# Pick emoji 6 / Display chosen emoji in emoji tkinter Frame
def send_emoji6(event=None):
    myimage = open("6.png", "rb")
    encode = base64.b64encode(myimage.read())
    client_socket.sendto(encode,(HOST,PORT))
    msg_list.insert(END, ">> Sending emoji to server...")
##############################################################
'''
+ CLIENT GUI: Using Tkinter
'''
##############################################################
root = Tk()
root.title("CLIENT T.I.M | Tiger Instant Messager")
root.resizable(width=False, height=False)
root.geometry('550x750')


# variable for chatbox message
my_msg = StringVar()  

# file to store chat history
f = open("chat_history.txt", "a+")

##############################################################
# set default IP and port for easy testing
HOST = '127.0.0.1'
PORT = 33300
##############################################################
#----------------------------header------------b--------------#
header_frame = Frame(root)

# tiger icon header
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

#display chatbox message
msg_list = Listbox(messages_frame, height=10, width=40, yscrollcommand=scrollbar.set)
scrollbar.pack(side=RIGHT, fill=Y)
msg_list.pack(side=LEFT, fill=BOTH,expand=TRUE)
msg_list.configure(background='#161616', fg='#ff6600', font=("Consolas", 14))

messages_frame.pack(side=TOP, fill=BOTH,expand=FALSE)
##############################################################
#----------------------enter message here--------------------#
# label for send text
lab_3 = Label(root, text="______________________________Send Text_____________________________ ")
lab_3.configure(fg='#e95d00', font=("Orator Std", 8))
lab_3.pack(side=TOP, fill=BOTH, expand=TRUE)
##############################################################
#---------------------------entry frame----------------------#
#type message
entry_field = Entry(root, textvariable=my_msg)
entry_field.bind("<Return>", send_message)
entry_field.pack(side=TOP,fill=BOTH,expand=TRUE)
entry_field.configure(background='#232323', fg='#84eef8')
#----------------------buttons frames------------------------#
#submit/upload file Frame
bottom_frame = Frame(root)
bottom_frame.config(borderwidth=2,bg='white')

lab_4 = Label(root, text="______________________________Data Transfer_____________________________ ")
lab_4.configure(fg='#e95d00', font=("Orator Std", 8))
lab_4.pack(side=TOP, fill=BOTH, expand=TRUE)

#Submit
# message_button = Button(bottom_frame, text="Submit",bg="white")
message_button = Button(bottom_frame, text="Submit",bg="white",command=send_message)

message_button.configure(background='#84eef8', fg='#232323', font=("Consolas", 10))
message_button.pack(in_=bottom_frame,side=RIGHT,fill=BOTH, expand=True)

#button to upload file
file_button = Button(bottom_frame, text="Upload File",bg="white",command=input_file)
file_button.configure(background='#84eef8', fg='#232323', font=("Consolas", 10))
file_button.pack(in_=bottom_frame,side=RIGHT,fill=BOTH, expand=True)

bottom_frame.pack(side=TOP,fill=BOTH,expand=TRUE)
##############################################################
#----------------------top emoji list--------------------------#
emoji_frame=Frame(root)
lab_4 = Label(root, text="______________________________Emoji Picker_____________________________ ")
lab_4.configure(fg='#e95d00', font=("Orator Std", 8))
lab_4.pack(side=TOP, fill=BOTH, expand=FALSE)

emoji_b1 = Button(root,command=send_emoji1)
photo_b1=PhotoImage(file="1.png")
emoji_b1.config(image=photo_b1, background='#ffd6be')
emoji_b1.pack(in_=emoji_frame,side=LEFT,fill=BOTH, expand=True)
label_b1 = Label(root, image=photo_b1)

emoji_b1 = Button(root,command=send_emoji2)
photo_b2=PhotoImage(file="2.png")
emoji_b1.config(image=photo_b2, background='#ffd6be')
emoji_b1.pack(in_=emoji_frame,side=LEFT,fill=BOTH, expand=True)
label_b2 = Label(root, image=photo_b2)

emoji_b1 = Button(root,command=send_emoji3)
photo_b3=PhotoImage(file="3.png")
emoji_b1.config(image=photo_b3, background='#ffd6be')
emoji_b1.pack(in_=emoji_frame,side=LEFT,fill=BOTH, expand=True)
label_b3 = Label(root, image=photo_b3)

emoji_b1 = Button(root,command=send_emoji4)
photo_b4=PhotoImage(file="4.png")
emoji_b1.config(image=photo_b4, background='#ffd6be')
emoji_b1.pack(in_=emoji_frame,side=LEFT,fill=BOTH, expand=True)
label_b4 = Label(root, image=photo_b4)

emoji_b1 = Button(root,command=send_emoji5)
photo_b5=PhotoImage(file="5.png")
emoji_b1.config(image=photo_b5, background='#ffd6be')
emoji_b1.pack(in_=emoji_frame,side=LEFT,fill=BOTH, expand=True)
label_b5 = Label(root, image=photo_b5)

emoji_b1 = Button(root,command=send_emoji6)
photo_b6=PhotoImage(file="6.png")
emoji_b1.config(image=photo_b6, background='#ffd6be')
emoji_b1.pack(in_=emoji_frame,side=LEFT,fill=BOTH, expand=True)
label_b6 = Label(root, image=photo_b6)

emoji_frame.pack(side=BOTTOM,fill=BOTH,expand=TRUE)
# ##############################################################
def init_filesharing(even=None):
    # set up socket for client and ack
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # create socket to receive acknowledgement
    ack_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ack_socket.bind(("", 33000))
    # create 3 threads to listen for incoming packet, ack, and a timer
    t1 = threading.Thread(target=send_packet, args=(HOST, PORT))
    t1.start()
    t2 = threading.Thread(target=listen_ack, args=(ack_socket, HOST))
    t2.start()
    t3 = threading.Thread(target=timer)
    t3.start()
##############################################################
# display text in list
pathlabel = Label(root)
pathlabel.pack()
######################## thread ##############################
root.mainloop()
##############################################################
# threading.Thread(target=listen_message).start()
