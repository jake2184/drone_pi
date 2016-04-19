#!/usr/bin/env python


import sys, struct, time, os, atexit

from argparse import ArgumentParser
parser = ArgumentParser(description=__doc__)

parser.add_argument("--baudrate", type=int,
                  help="master port baud rate", default=115200)
parser.add_argument("--device", required=True, help="serial device")
parser.add_argument("--rate", default=4, type=int, help="requested stream rate")
parser.add_argument("--source-system", dest='SOURCE_SYSTEM', type=int,
                  default=255, help='MAVLink source system for this GCS')
parser.add_argument("--showmessages", action='store_true',
                  help="show incoming messages", default=False)
args = parser.parse_args()

from pymavlink import mavutil


def wait_heartbeat(m):
    '''wait for a heartbeat so we know the target system IDs'''
    print("Waiting for APM heartbeat")
    m.wait_heartbeat()
    print("Heartbeat from APM (system %u component %u)" % (m.target_system, m.target_system))


def closeLink(master):
    print("Ending")
    master.close()

def log(logfile, msg):
    string = msg.name + " {"
    for field in msg.ordered_fieldnames:
        toAdd = field + ":" + str(getattr(msg, field)) + ", "
        string = string + toAdd
    string = string[:-2]
    string = string + " }\n"
    logfile.write(string)


def show_messages(m, logfile):
    '''show incoming mavlink messages'''
    msg_count = 0
    while True:
        msg = m.recv_match(blocking=True)
        if not msg:
            return
        t = msg.get_type()
        if t == "BAD_DATA":
            if mavutil.all_printable(msg.data):
                sys.stdout.write(msg.data)
                sys.stdout.flush()
        elif t == "HEARTBEAT":
            pass
        elif t == "ATTITUDE":
            pass
        else:
            msg_count = msg_count + 1
            sys.stdout.write(str(msg_count) + " ")
            print(msg)
            log(logfile, msg)


# create a mavlink serial instance
master = mavutil.mavlink_connection(args.device, baud=args.baudrate)

atexit.register(closeLink, master)
# wait for the heartbeat msg to find the system ID
wait_heartbeat(master)


# print("Sending all stream request for rate %u" % args.rate)
# for i in range(0, 3):
#     master.mav.request_data_stream_send(master.target_system, master.target_component,
#                                         #mavutil.mavlink.MAV_DATA_STREAM_ALL,
#                                         65,
#                                         args.rate, 1)
#
# for i in range(0, 3):
#     master.mav.request_data_stream_send(master.target_system, master.target_component,
#                                         #mavutil.mavlink.MAV_DATA_STREAM_ALL,
#                                         65,
#                                         args.rate, 1)

logfile = open("log.txt", 'w')

if args.showmessages:
    show_messages(master, logfile)