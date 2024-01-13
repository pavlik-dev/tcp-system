G=print
D=input
B=''
A=True
import socket as C,sys,random as H,string as I
import time
from threading import Thread as J
K=lambda o:G(o,end=B)
def L(m=B,t=object):
	while A:
		try:return t(D(m))
		except ValueError:G('The data you entered cannot be converted to '+t.__name__+'.');continue
def P(__try,__exceptions,__except):
	try:return __try()
	except __exceptions:return __except()
class M:
	serv_resp=A
	def __init__(A,dest,port):A.saddr,A.sport=dest,port;A.sock=C.socket(C.AF_INET,C.SOCK_DGRAM);A.sock.bind((B,H.randint(10000,40000)))
	send_to_server=lambda s,msg:s.sock.sendto(msg.encode('utf-8'),(s.saddr,s.sport))
	def st(B):
		while A:
			st = time.time()
			while not B.serv_resp:
				if (time.time() - st) > 10:
					print('Timeout.')
					exit()
				...
			del st
			B.send_to_server(D(':').strip());B.serv_resp=False
	def rh(C):
		while A:D=C.sock.recvfrom(4096);E=D[0].decode();K(B.join([A if A in I.printable else B for A in E]));C.serv_resp=A
N=D('IP:')
O=L('Port:',int)
E=M(N,O)
try:F=J(target=E.rh);F.daemon=A;F.start();E.st()
except(KeyboardInterrupt,SystemExit):sys.exit()