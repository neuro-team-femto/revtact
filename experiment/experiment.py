# coding=utf-8
import pandas as pd
import csv
import codecs
import datetime as dt
from psychopy import gui, core, visual, event
from fractions import Fraction
import numpy as np
import ni_reader as ni

########################################################################
### EXPERIMENT PARAMETERS
######################################################################

STIM_FILE = "stims/data_short.csv"
N_PRACTICE_BLOCKS = 1 #1
N_PRACTICE_TRIALS = 5 #1       # nb of trials per practice block
N_BLOCKS = 3 #1               # nb of trial blocks (possibly + 1, if repeat_last_block)
REPEAT_LAST_BLOCK = True # False  # if true, block (n_blocks) and block (n_blocks+1) are the same 
                            # some reverse-correlation experiments use a 'double-pass' procedure
                            # which present the same pair of data twice, in order to compute internal noise
N_TRIALS = 25 # 3               # per trial block
RECORD_FROM_CARD = True # False   # True to communicate with ni card


############################################################
## Management of trial and result files
#########################################################

def enblock(x, n_stims):
    # generator to cut a list of stims into blocks of n_stims
    # returns all complete blocks
    for i in range(len(x)//n_stims):
        start = n_stims*i
        end = n_stims*(i+1)
        yield x[start:end]

def generate_trial_files(subject_number=1,n_blocks=1,n_trials=100,practice=False, stim_file = "stims/data.csv"):
# generates n_block trial files per subject, and returns an array of their file_names
# each block contains n_trials trials
# each trial is composed of two textures, identified by their number
# trials are sampled from a set, described in a csv file
# returns an array of n_block file names
    
    stims = pd.read_csv(stim_file)

    first_half = stims.sample(n=n_blocks*n_trials, replace=True) # sample a random n_trials stims for interval 1
    second_half = stims.sample(n=n_blocks*n_trials,replace=True) # sample a random n_trials stims for interval 2

    for index,(stim1,stim2) in enumerate(zip(first_half.surface_number, second_half.surface_number)):
    # check for pairs composed of identical stims, and replace stim2 by random other
        if stim1 == stim2: 
            new_stim2 = stims[stims.surface_number!=stim2].sample(n=1).reset_index().loc[0,'surface_number']
            second_half.loc[index,'surface_number'] = new_stim2

    # write trials by blocks of n_trials
    block_count = 0 
    trial_files = []
    for block_stims in enblock(list(zip(first_half.surface_number, second_half.surface_number)),n_trials):
        trial_file = 'trials/'+date.strftime('%y%m%d_%H.%M')+'_trials_subj' + str(subject_number) + '_' \
                                          + ('PRACTICE' if practice else str(block_count))+'.csv'
        print ("generate trial file "+trial_file)
        trial_files.append(trial_file)
        with open(trial_file, 'w+', newline='') as file :
            # each trial is stored as a row in a csv file, with format: stimA, stimB
            # write header
            writer = csv.writer(file)
            writer.writerow(["stimulus_1","stimulus_2"])
            # write each trial in block
            for trial_stims in block_stims:
                writer.writerow(trial_stims)
        # break when enough blocks
        block_count += 1
        if block_count >= n_blocks:
            break
    return trial_files

def read_trials(trial_file):
# read all trials in a block of trial, stored as a CSV trial file
    with open(trial_file, 'r') as fid:
        reader = csv.reader(fid)
        trials = list(reader)
    return trials[1::] #trim header

def get_stim_info(texture_id, stim_file = "stims/data_short.csv"):
# read texture information stored in data file
# returns diameter, opening, spacing

    stims = pd.read_csv(stim_file)
    diameter = float(stims.loc[stims.surface_number==texture_id,'diameter'])
    opening = float(stims.loc[stims.surface_number==texture_id,'opening'])
    spacing = float(stims.loc[stims.surface_number==texture_id,'spacing'])
    return diameter, opening, spacing

def generate_result_file(subject_number):

    result_file = 'results/'+date.strftime('%y%m%d_%H.%M')+'_results_subj'+str(subject_number)+'.csv'
    # results are stored one line per texture in each pair/trial, i.e. a trial is stored in 2 lines
    result_headers = ['subj','trial','block','practice', 'sex','age','date','data_file','texture_id','stim_order','diameter','opening','spacing','response','rt']

    with open(result_file, 'w+') as file:
        writer = csv.writer(file)
        writer.writerow(result_headers)
    return result_file

###################################################################
## GUI
###################################################################

def show_text_and_wait(file_name = None, message = None, color = 'white'):
    event.clearEvents()
    core.wait(0.2)

    if message is None:
        with codecs.open (file_name, 'r', 'utf-8') as file :
        #with open (file_name, 'r') as file :
            message = file.read()
    text_object = visual.TextStim(win, text = message, color = color)
    text_object.height = 0.05
    text_object.draw()
    win.flip()
    
    # wait for key
    while True :
        if len(event.getKeys()) > 0: 
            core.wait(0.2)
            break
        event.clearEvents()
        core.wait(0.2)
        text_object.draw()
        win.flip()
        
def show_text(file_name = None, message = None, color = 'white'):
    event.clearEvents()
    core.wait(0.2)

    if message is None:
        with codecs.open (file_name, 'r', 'utf-8') as file :
        #with open (file_name, 'r') as file :
            message = file.read()
    text_object = visual.TextStim(win, text = message, color = color)
    text_object.height = 0.05
    text_object.draw()
    win.flip()






#########################################################################
### Run experiment
##########################################################################

# get participant nb, age, sex 
subject_info = {u'number':1, u'age':20, u'sex': u'f/m', u'handedness':'right'}
dlg = gui.DlgFromDict(subject_info, title=u'Tactile Reverse correlation')
if dlg.OK:
    subject_number = subject_info[u'number']
    subject_age = subject_info[u'age']
    subject_sex = subject_info[u'sex']  
    subject_handedness = subject_info[u'handedness'] 
else:
    core.quit() #the user hit cancel so exit
date = dt.datetime.now()
time = core.Clock()

if RECORD_FROM_CARD: 
    # create acquisition reader
    ni_reader=ni.NIReader('config/config_nireader_real.py') 
    # start acquisition
    ni_reader.start_acquisition(subject_number)

# create psychopy black window where to show instructions
win = visual.Window(np.array([1920,1080]),fullscr=False,color='black', units='norm')

# generate data files
result_file = generate_result_file(subject_number)
practice_file = generate_trial_files(subject_number, 
                                    n_blocks=N_PRACTICE_BLOCKS,
                                    n_trials=N_PRACTICE_TRIALS,
                                    practice=True,
                                    stim_file = STIM_FILE)
trial_files = generate_trial_files(subject_number,
                                    n_blocks=N_BLOCKS,
                                    n_trials=N_TRIALS,
                                    practice=False,
                                    stim_file = STIM_FILE)
if REPEAT_LAST_BLOCK:
    trial_files.append(trial_files[-1]) # todo: these trials should be tagged as double-pass
trial_files = practice_file + trial_files #each file is a block; first n_practice_blocks blocks are practice blocks. 

# start user interaction
show_text_and_wait(file_name="intro_1.txt")
show_text_and_wait(file_name="intro_2.txt")


practice_block = True if N_PRACTICE_BLOCKS > 0 else False
if practice_block: # inform participant if there are practice blocks
    show_text_and_wait(file_name="practice.txt") 
    
trial_count = 0
n_blocks = len(trial_files)
for block_count, trial_file in enumerate(trial_files):

    if practice_block & (block_count == N_PRACTICE_BLOCKS) :
        # inform end of practice at the end of the initial practice blocks
        show_text_and_wait(file_name="end_practice.txt")
        practice_block = False

    block_trials = read_trials(trial_file)
    
    for trial_count,trial in enumerate(block_trials) :

        print("block"+str(block_count)+": trial"+str(trial_count) + ' (practice: '+ str(practice_block)+')')

        # inform to position both surfaces and wait for start of recording
        stim_1 = trial[0]
        stim_2 = trial[1]
        show_text_and_wait(message = u"Block %d trial %d \n\n EN ATTENTE \n\n Positionner Texture %s - Texture %s \n\n\n"%(block_count,trial_count,stim_1,stim_2) +
        "Faire reset sur l'amplificateur (bouton rouge)\n\n\n Puis appuyez pour démarrer l'acquisition", 
        color = 'orange') 
        event.clearEvents()

        trial_data_file = 'results/'+ date.strftime('%y%m%d_%H.%M')+'_data_subj' + str(subject_number) \
                           + '_block' +str(block_count) \
                           + '_trial' +str(trial_count) \
                               + ('_PRACTICE' if practice_block else '') +'.csv'
        if RECORD_FROM_CARD:
            # log data in new result_file
            ni_reader.new_result_file(trial_data_file,\
                                    block=block_count,
                                    trial = trial_count,
                                    practice=practice_block)

        show_text(message= u"RECORDING \n\n Appuyer sur ESPACE pour stopper l'enregistrement,\n\n ou appuyer sur g/h pour enregistrer la réponse.", color = 'green')
        # Rappeler en attente de réponse: space ou g/h
        response_start = time.getTime()

        # wait for end of recording, or participant response
        while True :
            response_key = event.getKeys()
            if len(response_key) > 0: 

                # any key (incl. g/h): stop recording
                if RECORD_FROM_CARD:
                    ni_reader.new_result_file(None)
                    show_text(message = "(enregistrement terminé) \n\n Appuyer sur g/h pour enregistrer la réponse.", color = 'red')
                    # rappeler en attente de réponse g/h
                    event.clearEvents()
                    continue
                
                if response_key == ['g']: # response 1
                    response_choice = 0
                elif response_key == ['h']: # response 2
                    response_choice = 1
                else : # continue waiting for response
                    continue
                                
                response_time = time.getTime() - response_start
                show_text(message = "(réponse sauvée)", color = 'red')
                break
                
        event.clearEvents()        
        core.wait(0.2)

        # log response
        row = [subject_number, trial_count, block_count, practice_block, subject_sex, subject_age, date, trial_data_file]
        with open(result_file, 'a') as file :
            writer = csv.writer(file,lineterminator='\n')
            for stim_order,stim in enumerate(trial):
                diameter, opening, spacing = get_stim_info(texture_id = stim, 
                                                            stim_file = STIM_FILE)
                print('Texture %s %f,%f,%f'%(stim,diameter, opening, spacing))
                result = row + [stim, stim_order, diameter, opening, spacing] \
                                 + [response_choice==stim_order, round(response_time,3)]
                writer.writerow(result) #store a line for each x,y pair in the stim

        
    # pause at the end of subsequent blocks
    if ((block_count >= N_PRACTICE_BLOCKS) and (block_count < n_blocks-1)):
        show_text_and_wait(message = u"Vous avez complété " \
                                + str(Fraction(block_count-N_PRACTICE_BLOCKS+1, n_blocks-N_PRACTICE_BLOCKS)) \
                                + u" de l'expérience.\n Vous pouvez faire une pause si vous le souhaitez, puis appuyer sur une touche pour continuer.")


#End of experiment
if RECORD_FROM_CARD:
    ni_reader.stop_acquisition()

show_text_and_wait("end.txt")

win.close()
core.quit()
sys.exit()
