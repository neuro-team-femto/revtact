import numpy as np
import time
import csv
from datetime import datetime
import nidaqmx
from nidaqmx.stream_readers import AnalogMultiChannelReader
from nidaqmx import constants
import pickle
import os

class NIReader:
	def __init__(self,date,config_file): 
		self.parameters = {}
		exec(open(config_file).read(),self.parameters)
		pars=self.parameters['params']
		self.sampling_freq_in = pars['sampling_freq_in']  # in Hz
		self.buffer_in_size = pars['buffer_in_size'] # samples
		self.chans_in = pars['chans_in']  
		self.running = pars['running']
		self.date = date
		self.dev = pars['dev']
		self.participant = 'unknown'

	def set_participant(self, participant): 
		self.participant = participant

	def get_participant(self): 
		return self.participant

	def set_config_order(self,config):
		self.config = config

	def get_config_order(self):
		return self.config

	def reading_task_callback(self,task_idx, event_type, num_samples, callback_data):  # bufsize_callback is passed to num_samples
		
		if self.running:
			
			# get buffer data
			buffer_in = np.zeros((self.chans_in, num_samples)) 
			self.stream_in.read_many_sample(buffer_in,
								 num_samples, 
								 timeout=constants.WAIT_INFINITELY)
			buffer_time = self.current_time + self.buffer_in_size*self.callback_counter*1000/self.sampling_freq_in # start time of the ith buffer, in ms
				
			# write in file
			with open(self.result_file, 'a') as file :
				writer = csv.writer(file,lineterminator='\n')
				for n_sample in range(num_samples):
					time_in_buffer = n_sample*1000/self.sampling_freq_in # time offset of the n_sample sample in current buffer
					result = [buffer_time + time_in_buffer] # time stamp of current sample
					for channel_buffer in buffer_in: 
						result += [channel_buffer[n_sample]] # each channel of the current sample
					writer.writerow(result + [self.participant,self.config,self.order,self.condition_name+'_'+str(self.repeat)])

			self.callback_counter+=1

		return 0  

	def start_acquisition(self,start_time,participant,file,order):
		
		# Configure and setup the tasks
		self.set_participant(participant)
		self.file = file
		parameters = {}
		exec(open(file).read(),parameters)
		pars=parameters['params']
		self.condition_name = pars['condition_name']
		self.repeat = pars['n_repeats']
		self.order = order
		self.task_in = nidaqmx.Task()
		self.task_in.ai_channels.add_ai_voltage_chan(self.dev)  # has to match with chans_in
		self.task_in.timing.cfg_samp_clk_timing(rate=self.sampling_freq_in, 
									   sample_mode=constants.AcquisitionType.CONTINUOUS,
									   samps_per_chan=self.buffer_in_size)
		self.stream_in = AnalogMultiChannelReader(self.task_in.in_stream)
		self.task_in.register_every_n_samples_acquired_into_buffer_event(self.buffer_in_size,
																 self.reading_task_callback)

		self.result_file="data/treadmill_participant_"+self.participant+"_order_"+str(self.order)+'_'+str(self.date)+"_data.csv"
		with open(self.result_file, 'a') as file :
				writer = csv.writer(file,lineterminator='\n')
				header = ['time','x_left','y_left','z_left','x_right','y_right','z_right','participant','config_file','order','condition_name']
				writer.writerow(header)

		print("Acquisition starting")
		self.running = True
		self.current_time=time.time()-start_time
		self.callback_counter = 0
		self.task_in.start()

	def stop_acquisition(self):
		self.running = False
		self.task_in.close()
		print("Acquisition stopped")

