import socket
import sys
import string
import time
import random
from tabulate import tabulate

split_list = lambda x: (x[:len(x)//2], x[len(x)//2:])

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(('192.168.0.1', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

class User(object):
    # class Client(object):
    #     __config = {
    #         "color":False
    #     }
    #     def __init__(self, config: dict):

    class Message(object):
        __from = None
        __to = None
        __content = ''
        __msg_id = 0
        def __init__(self, __from, __to, content):
            get_id = lambda ip: (sum([int(c) if c in string.digits else 0 for c in ip[0]]) + ip[1])
            self.__from = __from
            self.__to = __to
            self.__content = content
            self.__msg_id = (get_id(__from['addr']) + get_id(__to['addr']) + random.randint(0,9999))
        def __getitem__(self, item):
            if item == "from":
                return self.__from
            if item == "to":
                return self.__to
            if item == "content":
                return self.__content
            if item == "msg_id":
                return self.__msg_id
            raise KeyError(item)
        def __setitem__(self, item, value):
            if item != 'content' and item in ('from','to','msg_id'):
                raise ValueError('You can only change the content of the message.')
            if item != 'content':
                raise KeyError(f'Unknown key: {item}.')
            self.__content = value
    user_config = {
        "name":'', # (name -> Nickname)
        "addr":None, # (addr -> IP Address)
        "msgs":{"recv":[],"sent":[]}, # (msgs -> Messages, recv -> Received, sent -> Sent)
        "friends":["Reserved for future use"],
        "reqs":["Reserved for future use"], # (reqs -> Requests)
        "msg_ip":False, # or <MESSAGE()> (msg_ip -> Message in progress)
        "joined":0, # UNIX timestamp
        "is_guest":False,
        "permissions":{
            "msg":False, # (msg -> Permission for sending messages to other users in the chatroom)
            "friends":False,  # For future use (friends -> Permission to send friend requests)
        },
        "client_conf":{
            "color":False
        },
    }
    def __init__(self, config:dict={}, perm_all = False):
        self.user_config.update(config);self.user_config['permissions'].update(dict([(i, True) for i in self.user_config['permissions']]))
    __getitem__ = lambda self, key: self.user_config.get(key)
    def __setitem__(self, key, value): self.user_config[key] = value
    get = __getitem__
    update = lambda self, new_dict: self.user_config.update(new_dict)

class Server:
    def __init__(self, dest, port):
        self.server_port, self.server_addr = port, dest
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.server_addr, self.server_port))

    send_to_client = lambda self, msg, addr_port_tuple: self.sock.sendto(msg.encode("utf-8"), addr_port_tuple)

    forward_message = send_to_client

    def start(self):
        users: dict[User] = {}  # "USER" : <USER()>
        msgs: dict[User.Message] = {} # "MSG ID" : <MESSAGE()>
        new_guest = lambda ip: User({'is_guest':True,'addr':ip,'name':f'Guest #{(sum([int(c) if c in string.digits else 0 for c in ip[0]]) + ip[1])}'})
        def get_user_by_ip(ip):
            print(users)
            for user_key in users:
                user = users[user_key]
                if user['addr'] == ip: return user
                print(user['name'], user['addr'])
                print(ip)
                print()
            return None
        def name_is_valid(name:str)->bool:
            allowed_chars = string.ascii_letters+string.digits+'_'
            for c in name:
                if c in allowed_chars:
                    continue
                return False
            return True
        def new_user(name,ip):
            print(users)
            new_usr = User({'addr':ip,'name':name,'joined':int(time.time()),"is_guest":False}, True)
            users[name] = new_usr
        # def send_msg(__from: User, __to: User, __msg: str):
        #     __from['msgs']['sent'] += []
            
        while True:
            resp = self.sock.recvfrom(4096); client_message, client_addr_port = resp[0].decode(), resp[1]
            send_resp = lambda msg: self.forward_message(msg, client_addr_port)
            cmd, cmdlen = client_message.split(), len(client_message.split())
            client = get_user_by_ip(client_addr_port) or new_guest(client_addr_port)

            if client['msg_ip']:
                if cmd[0] == '.':
                    new_msg = client['msg_ip']
                    client['msg_ip'] = False
                    client['msgs']['sent'] += [new_msg]
                    new_msg['to']['msgs']['recv'] += [new_msg]
                    send_resp(f'Successfully sent message to {new_msg["to"]["name"]}.\n')
                    continue
                client['msg_ip']['content'] += client_message+'\n'
                send_resp('\0')
                continue

            # User commands
            if cmd[0] == "join":
                if cmdlen != 2: send_resp("Incorrect cmd usage.\nUsage:\n\tjoin (name)\n"); continue
                if not client.get('is_guest'): send_resp("To change ur name, u need to leave the chatroom first by typing `leave` cmd.\n"); continue
                if len(cmd[1]) not in range(3,16): send_resp("The name must contain from 3 to 15 characters.\n"); continue
                if cmd[1].lower() in users: send_resp("This name is already taken.\n"); continue
                if not name_is_valid(cmd[1]): send_resp("This name contains invalid characters.\n"); continue
                new_user(cmd[1],client_addr_port); send_resp(f"Hello and welcome to the chatroom, {cmd[1]}!\nTo list the commands, write the command `cmd`.\n")
            
            elif cmd[0] == "whoami":
                if cmdlen != 1: send_resp("Incorrect cmd usage.\nUsage:\n\twhoami\n"); continue
                send_resp(f"Username: {client.get('name')}\nIP Address: {client_addr_port[0]}:{client_addr_port[1]}\nJoin date: {client.get('joined')}\n")
            
            elif cmd[0] == "users":
                if cmdlen != 1: send_resp("Incorrect cmd usage.\nUsage:\n\tusers\n"); continue
                usrnames = [g if g != client.get('name') else g+" (you)" for g in list(users.keys())][:19]+[f"And {len(users.keys())-19} more..."] if len(list(users.keys())) >= 20 else list(users.keys())
                print(usrnames)
                send_resp("Users in the chatroom:\n"+"\n".join(usrnames)+'\n')
            
            elif cmd[0] in ("exit", "quit", "q"):
                if cmdlen != 1: send_resp(f"Incorrect cmd usage.\nUsage:\n\t{cmd[0]}\n"); continue
                if not client.get('is_guest'):
                    del users[client['name']]
                send_resp("See you next time!\n")

            # Messages
            elif cmd[0] in ["msg","send_msg","sendmsg"]:
                if client['is_guest']: send_resp("Guests can't send messages. Please join the chatroom first.\n"); continue
                if not client['permissions']['msg']: send_resp("You don't have permission to send messages.\n"); continue
                if cmdlen != 2: send_resp(f"Incorrect cmd usage.\nUsage:\n\t{cmd[0]} (name)\n"); continue
                if cmd[1] not in users: send_resp(f"I can't find {cmd[1]}.\n"); continue
    
                send_resp("OK. Write a msg and put a dot after the last line to send it.\n")
                to_usr = users[cmd[1]]
                client['msg_ip'] = User.Message(client, to_usr, '')

            # List of commands
            elif cmd[0] == 'cmd':
                if cmdlen != 1: send_resp("Incorrect cmd usage.\nUsage:\n\tcmd\n"); continue
                commands = {
                    "join (name)":'Adds a user with the specified name to the chatroom.',
                    'whoami':'Displays information about the current user.',
                    'users':'Displays all users in the chatroom as a list.',
                    "cmd":"Displays a list of available commands.",
                }
                res = "\n".join([f"{_cmd} -- {commands[_cmd]}" for _cmd in commands])+'\n'
                send_resp(res)

            else:
                send_resp(f"Unknown command.\nTo list the commands, write the command `cmd`.\n")
            # self.forward_message(client_message.rstrip()+'\r\n', client_addr_port)

if __name__ == "__main__":
    PORT = 80
    DEST = None or get_local_ip()

    print("Server started. Address:", DEST, "Port:", PORT)
    SERVER = Server(DEST, PORT)
    try:
        SERVER.start()
    except (KeyboardInterrupt, SystemExit):
        exit()