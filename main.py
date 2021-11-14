from serialcomms import Serial_Comm
from networkcomms import Network_Sock
from roboutils import Timer
import time, sys, json

#host socket IP address and port
server_ip = '192.168.1.5'
server_port = 12345

class Robot_Controller:

	def __init__(self, vehicle=None, sock_conn=None, serial_conn=None):
		self.vehicle = None
		self.ns = None
		self.ser = None

		self.serial_started = False
		self.socket_started = False
		self.vehicle_started = False

		#self.control_thread_flag = False
		#self.control_thread = None

	def start_socket(self, ip, port, timeout=2.5):
		self.ns = Network_Sock()
		thread_timer = Timer(timeout)
		thread_timer.start()
		while not self.ns.connect(ip, port) and not thread_timer.expired():
			time.sleep(.01)

		if self.ns.is_connected():
			self.ns.start_receive_thread()
			return True
		else:
			self.ns = None
			return False

	def start_serial(self, baud, port, prefix):
		self.ser = Serial_Comm()
		if self.ser.connect(baud, port, prefix):
			self.ser.start_receive_thread()
			return True
		else:
			self.ser = None
			return False

	def assign_vehicle(self, vehicle_class):
		self.vehicle = vehicle_class

	def start(self):
		if not self.serial_started:
			self.serial_started = self.start_serial(115200, 10, 'COM')
		if not self.socket_started:
			self.socket_started = self.start_socket(server_ip, server_port)
		if not self.vehicle_started:
			try:
				self.vehicle.start_vehicle_timers()
				self.vehicle_started = True
			except:
				self.vehicle_started = False

		print(f'Socket started: {self.socket_started} | Serial started: {self.serial_started} | Vehicle started: {self.vehicle_started}')
		return [self.serial_started, self.socket_started, self.vehicle_started]
	

	def stop(self):
		self.estop()
		self.ser.stop()
		self.ns.stop()

		self.serial_started = False
		self.socket_started = False
		self.vehicle_started = False


	def get_data_from_socket_queue(self):
		data = []
		#cq = self.ns.pop_latest_from_queue()
		cq = self.ns.get_queue()
		#print(cq)
		for line in cq:
			line = json.loads(line)
			for dp in line["arr"]:#cq["arr"]:
				data.append(dp)
		self.ns.clear_queue()
		return data

	def estop(self):
		frame = bytes([0x55,0xFA,0x00,0x00,0x00,0x00])
		self.ser.send_bytes(frame)

	def run(self):
		gd = self.get_data_from_socket_queue()
		self.vehicle.update_vehicle_states(gd)
		ser_mes = self.vehicle.generate_serial_message()
		if ser_mes is not None:
			#print(ser_mes)
			self.ser.send_bytes(ser_mes)

class MBlock_UltiTank:

	def __init__(self):
		self.left_drive_state = 0
		self.right_drive_state = 0
		self.gripper_state = 0
		self.arm_state = 0

		self.voltage_val = 0

		self.vehicle_state_timer = Timer(0.05)
		self.vehicle_sensor_timer = Timer(0.02)
		self.vehicle_voltage_timer = Timer(.75)

	def start_vehicle_timers(self):
		self.vehicle_state_timer.start()
		self.vehicle_voltage_timer.start()
		#self.vehicle_sensor_timer.start()

	def update_vehicle_states(self, pay_queue):
		for item in pay_queue:
			if "left" in item:
				self.left_drive_state = item["left"]
			if "right" in item:
				self.right_drive_state = item["right"]
			if "arm" in item:
				self.arm_state = item["arm"]
			if "grip" in item:
				self.gripper_state = item["grip"]


	def signed_to_unsigned_byte(self, val):
		if val < 0:
			return val + 2**8
		else:
			return val


	def generate_serial_message(self):
		frame = [0x55]
		if self.vehicle_state_timer.expired():
			frame.append(0xFA)
			frame.append(self.signed_to_unsigned_byte(int(self.left_drive_state)))
			frame.append(self.signed_to_unsigned_byte(int(self.right_drive_state)))
			frame.append(self.signed_to_unsigned_byte(self.arm_state))
			frame.append(self.signed_to_unsigned_byte(self.gripper_state))
			self.vehicle_state_timer.start()
			bframe = bytes(frame)
			print(f'Sending payload {frame} as byte array ({bframe})')
			return bframe

		if self.vehicle_sensor_timer.expired():
			frame.append(0xFB)
			self.vehicle_sensor_timer.start()
			bframe = bytes(frame)
			print(f'Sending payload {frame} as byte array ({bframe})')
			return bframe

		if self.vehicle_voltage_timer.expired():
			frame.append(0xFB)
			frame.append(0x11)
			self.vehicle_voltage_timer.start()
			bframe = bytes(frame)
			print(f'Sending payload {frame} as byte array ({bframe})')
			return bframe

		return None


	def update(self):
		pass


def main():
	c = Robot_Controller()
	print("controller made")
	try:
		v = MBlock_UltiTank()
		c.assign_vehicle(v)
		print("vehicle assigned")
		status = c.start()
		print("controller started")
		#c.vehicle.start_vehicle_timers()
		
		# tt = Timer(10)
		# tt.start()
		# while not tt.expired():
		# 	print("iter")
		# 	c.run()
		# 	time.sleep(.1)

		runtime_flag = True
		tt = Timer(1)
		tt.start()
		while runtime_flag:
			try:
				c.run()
				time.sleep(.001)
				if tt.expired():
					print(c.ser.queue_in)
					tt.start()
			except KeyboardInterrupt:
				runtime_flag = False
			
		#time.sleep(5)
		#print(c.ns.get_queue())
		c.stop()
		#while True:
		#	print("loop")
		#	time.sleep(1)

	except KeyboardInterrupt:
		c.stop()

	except:
		print("error in main")
		c.stop()
		x = dsajkh()
		pass
	#netsock_class_test()

# def serial_class_test():
# 	ser = Serial_Comm()
# 	ser.connect(115200, port=10, prefix='COM')
# 	time.sleep(1)
# 	ser.start_receive_thread()
# 	nflag = True
# 	#time.sleep(2)
# 	thread_timer = Timer(10)
# 	thread_timer.start()
	
# 	while(nflag):
# 		try:
# 			if thread_timer.expired():
# 				nflag = False
# 			ser.send_bytes([0x55,0xFA,0x00,0x00,0x00,0x00])
# 			print("Bytes sent")
# 			time.sleep(.2)
# 			print(len(ser.queue_in))
# 			print(ser.queue_in)
# 			continue
# 		except:
# 			break

# 	ser.stop_threads()

# def netsock_class_test():
# 	ns = Network_Sock()
# 	thread_timer = Timer(10)
# 	thread_timer.start()
# 	while not ns.connect(server_ip, server_port) and not thread_timer.expired():
# 		time.sleep(.1)
# 	if ns.is_connected():
# 		print("starting socket thread")
# 		ns.start_receive_thread()
# 		thread_timer.start()
# 		while not thread_timer.expired():
# 			#print(ns.receive())
# 			time.sleep(.001)
# 			try:
# 				if ns.queue_count() > 0:
# 					print(ns.pop_latest_from_queue())
# 					ns.clear_queue()
# 				#print(ns.queue_in)
# 			except:
# 				print(ns.queue_in)
# 		ns.close()
# 	else:
# 		print("socket not started")

if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		sys.exit()
	except:
		sys.exit()