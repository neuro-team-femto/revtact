import numpy as np
import time
import csv
from datetime import datetime
import nidaqmx
from nidaqmx.stream_readers import AnalogMultiChannelReader
from nidaqmx import constants
import pickle
import os
import datetime as dt

class NIReader:
	
	def __init__(self,config_file): 

		# read parameters from config file
		self.parameters = {}
		exec(open(config_file).read(),self.parameters)
		pars=self.parameters['params']
		self.sampling_freq_in = pars['sampling_freq_in']  # in Hz
		self.buffer_in_size = pars['buffer_in_size'] # samples
		self.chans_in = pars['chans_in'] 
		self.chans_id = pars['chans_id'] 
		self.running = pars['running']
		self.dev = pars['dev']
		
		self.participant = 'unknown'

	def reading_task_callback(self,task_idx, event_type, num_samples, callback_data):  

		if self.running:
			
			# get buffer data
			buffer_in = np.zeros((self.chans_in, num_samples)) 
			self.stream_in.read_many_sample(buffer_in,
								 num_samples, 
								 timeout=constants.WAIT_INFINITELY)

			buffer_time = self.start_time + self.buffer_in_size*self.callback_counter*1000/self.sampling_freq_in # start time of the ith buffer, in ms
				
			# write in file
			with open(self.result_file, 'a') as file :
				writer = csv.writer(file,lineterminator='\n')
				for n_sample in range(num_samples):
					time_in_buffer = n_sample*1000/self.sampling_freq_in # time offset of the n_sample sample in current buffer
					result = [buffer_time + time_in_buffer] # time stamp of current sample
					for channel_buffer in buffer_in: 
						result += [channel_buffer[n_sample]] # each channel of the current sample
					writer.writerow(result + [self.participant,self.block,self.trial,self.practice])

			self.callback_counter+=1

		return 0  

	def start_acquisition(self,subject_number,block_number,trial_number,practice):
		
		date = dt.datetime.now()

		# store acquisition metadata 
		self.participant = subject_number
		self.block = block_number
		self.trial = trial_number
		self.practice = practice

		# set up the task
		self.task_in = nidaqmx.Task()
		self.task_in.ai_channels.add_ai_voltage_chan(self.dev)  # has to match with chans_in
		self.task_in.timing.cfg_samp_clk_timing(rate=self.sampling_freq_in, 
									   sample_mode=constants.AcquisitionType.CONTINUOUS,
									   samps_per_chan=self.buffer_in_size)
		self.stream_in = AnalogMultiChannelReader(self.task_in.in_stream)
		self.task_in.register_every_n_samples_acquired_into_buffer_event(self.buffer_in_size,
																 self.reading_task_callback)

		# create result file name
		self.result_file = 'results/data_subj' + str(self.participant) \
							+ '_block' +str(self.block) \
							+ '_trial' +str(self.trial) \
							+ ('_PRACTICE' if self.practice else '') \
							+ '_' + date.strftime('%y%m%d_%H.%M')+'.csv'
		with open(self.result_file, 'a') as file :
				writer = csv.writer(file,lineterminator='\n')
				header = ['time'] + self.chans_id + ['participant','block','trial','practice']
				writer.writerow(header)

		# start acquisition
		print("Acquisition starting")
		self.running = True
		self.start_time=time.time()
		self.callback_counter = 0
		self.task_in.start()

		return self.result_file

	def stop_acquisition(self):
		self.running = False
		self.task_in.close()
		print("Acquisition stopped")

