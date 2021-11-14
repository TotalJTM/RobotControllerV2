# from serial import Serial
# from _thread import *
# import threading
# from roboutils import Timer
# import time

# class Serial_Comm:
# 	def __init__(self, ):
# 		self.queue_in = []
# 		self.queue_out = []
# 		self.sp = None
# 		self.sthread = None

# 		self.th_flag = False

# 	def connect(self, baud=115200, port=None, prefix='/dev/ttyACM'):
# 		try:
# 			self.sp = Serial(f'{prefix}{port}', baud)
# 			return True
# 		except:
# 			print(f'Invalid serial port {prefix}{port}')
# 			return False

# 	def th_receive(self):
# 		#print("receive happening")
# 		mes = self.sp.readline()
# 		#print(mes)
# 		if mes:
# 			#print(f'Thread response {mes}')
# 			self.queue_in.append(mes.decode('utf-8'))
# 		else:
# 			return

# 	def receive_thread(self, timeout=0.2):
# 		th_timer = Timer(timeout)
# 		while self.th_flag:
# 			th_timer.start()
# 			th_iter = threading.Thread(target=self.th_receive)
# 			th_iter.daemon = True
# 			th_iter.start()
# 			#th_iter = threading.Thread(target=self.receive_bytes)
# 			while not th_timer.expired():
# 				#print(f'not expired ')#{th_iter}
# 				time.sleep(.005)

# 			if self.th_flag is False:
# 				return

# 			self.sp.flushInput()
# 			#th_iter.kill()
# 			#print("thread reset")
# 			#msg = self.receive()
# 			#time.sleep(1)
# 			#print(msg)
# 			#if th_iter is not None:
# 			#	print(f'Thread response {th_iter}')
# 			#	self.queue_in.append(th_iter)
# 			#else:
# 			#	print("No received data")

# 	def start_receive_thread(self):
# 		if self.sp is not None:
# 			self.th_flag = True
# 			self.sthread = threading.Thread(target=self.receive_thread)#, args=(self)
# 			self.sthread.start()

# 	def send_bytes(self, bytes_arr):
# 		if self.sp is not None:
# 			self.sp.write(bytes_arr)
# 			#for b in bytes_arr:
# 			#	self.sp.write(b)

# 	def receive(self):
# 		response = self.sp.readline()
# 		#print(response)
# 		if response:
# 			return response.decode('utf-8')
# 		else:
# 			return None

# 	def receive_bytes(self):
# 		response = self.sp.readline()
# 		print(response)
# 		if response:
# 			return response
# 		else:
# 			return None

# 	def stop_threads(self):
# 		self.th_flag = False




#	JTM 2021
#	custom serial port class v2.0

from serial import Serial
from _thread import *
import threading
from roboutils import Timer
import time

class Serial_Comm:
	def __init__(self, ):
		self.queue_in = []
		self.sp = None
		self.sthread = None

		self.th_flag = False

	def connect(self, baud=115200, port=None, prefix='/dev/ttyACM'):
		try:
			self.sp = Serial(f'{prefix}{port}', baud)
			return True
		except:
			print(f'Invalid serial port {prefix}{port}')
			return False

	def th_receive(self):
		mes = self.sp.readline()
		if mes:
			self.queue_in.append(mes.decode('utf-8'))
		else:
			return

	def receive_thread(self, timeout=0.01):
		th_timer = Timer(timeout)
		while self.th_flag:
			th_timer.start()
			th_iter = threading.Thread(target=self.th_receive)
			th_iter.daemon = True
			th_iter.start()
			while not th_timer.expired():
				time.sleep(.001)

			if self.th_flag is False:
				return
			self.sp.flushInput()

	def start_receive_thread(self):
		if self.sp is not None:
			self.th_flag = True
			self.sthread = threading.Thread(target=self.receive_thread)
			self.sthread.start()

	def send_bytes(self, bytes_arr):
		if self.sp is not None:
			self.sp.write(bytes_arr)

	def receive(self):
		response = self.sp.readline()
		if response:
			return response.decode('utf-8')
		else:
			return None

	def receive_bytes(self):
		response = self.sp.readline()
		print(response)
		if response:
			return response
		else:
			return None

	def stop(self):
		self.th_flag = False

