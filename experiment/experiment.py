# coding=utf-8
import pandas as pd
import csv
import codecs
import datetime as dt
from psychopy import gui, core, monitors, visual, event
from fractions import Fraction
import numpy as np

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

def generate_trial_files(subject_number=1,n_blocks=1,n_trials=100,practice=False):
# generates n_block trial files per subject
# each block contains n_trials trials
# each trial is composed of two textures, identified by their number
# trials are sampled from a set, described in a csv file
# returns an array of n_block file names
    stim_file = "stims/data.csv"
    stims = pd.read_csv(stim_file)

    first_half = stims.sample(n=n_blocks*n_trials, replace=True) # sample a random n_trials stims for interval 1
    second_half = stims.sample(n=n_blocks*n_trials,replace=True) # sample a random n_trials stims for interval 2
    # trials consist of two random files, one from the first half, and one from the second half of the stimulus list
    # write trials by blocks of n_trials
    block_count = 0 
    trial_files = []
    for block_stims in enblock(list(zip(first_half.surface_number, second_half.surface_number)),n_trials):
        trial_file = 'trials/trials_subj' + str(subject_number) + '_' \
                                          + ('PRACTICE' if practice else str(block_count))\
                                          + '_' + date.strftime('%y%m%d_%H.%M')+'.csv'
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

def get_stim_info(texture_id):
# read texture information stored in data file
# returns diameter, opening, spacing

    stim_file = "stims/data.csv"
    stims = pd.read_csv(stim_file)
    diameter = float(stims.loc[stims.surface_number==texture_id,'diameter'])
    opening = float(stims.loc[stims.surface_number==texture_id,'opening'])
    spacing = float(stims.loc[stims.surface_number==texture_id,'spacing'])
    return diameter, opening, spacing

def generate_result_file(subject_number):

    result_file = 'results/results_Subj'+str(subject_number)+'_'+date.strftime('%y%m%d_%H.%M')+'.csv'
    # results are stored one line per texture in each pair/trial, i.e. a trial is stored in 2 lines
    result_headers = ['subj','trial','block','practice', 'sex','age','date','texture_id','stim_order','diameter','opening','spacing','response','rt']

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

#def update_trial_gui():
#    for response_label in response_labels: response_label.draw()
#    for response_checkbox in response_checkboxes: response_checkbox.draw()
#    win.flip()



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

# create psychopy black window where to show instructions
win = visual.Window(np.array([1920,1080]),fullscr=False,color='black', units='norm')


# Response GUI
#response_options = ['[g] texture 1', '[h] texture 2']
#response_keys = ['g', 'h']
#label_size = 0.07
#response_labels = []
#reponse_ypos = -0.7
#reponse_xpos = -0.6
#label_spacing = abs(-0.8 - reponse_ypos)/(len(response_options)+1)
#for index, response_option in enumerate(response_options):
#    y = reponse_ypos - label_spacing * index
#    response_labels.append(visual.TextStim(win, units = 'norm', text=response_option, alignHoriz='left', height=label_size, color='black', pos=(reponse_xpos,y-0.2)))
#    reponse_xpos=reponse_xpos+1

# generate data files
result_file = generate_result_file(subject_number)

# generate trial files: 1 practice block per actor, then (n_blocks + (repeat_last_block==True)?1:0) blocks of n_stims trials
n_practice_blocks = 1 # there are as many practice blocks as there are actors
n_practice_trials = 4 # nb of trials per practice block (i.e. per actor)
n_blocks = 2 # nb of trial blocks (possibly + 1, if repeat_last_block)
repeat_last_block = True # if true, block (n_blocks) and block (n_blocks+1) are the same
n_trials = 50  # per trial block

practice_file = generate_trial_files(subject_number, n_blocks=n_practice_blocks, n_trials=n_practice_trials, practice=True)
trial_files = generate_trial_files(subject_number, n_blocks,n_trials)
if repeat_last_block:
    trial_files.append(trial_files[-1])
trial_files = practice_file + trial_files #each file is a block; first n_practice_blocks blocks are practice blocks. 

show_text_and_wait(file_name="intro_1.txt")
show_text_and_wait(file_name="practice.txt") # instructions for the n_practice_blocks first blocks of stimuli

trial_count = 0
n_blocks = len(trial_files)
practice_block = True
    
for block_count, trial_file in enumerate(trial_files):

    # inform end of practice at the end of the initial practice blocks
    if block_count == n_practice_blocks :
        show_text_and_wait(file_name="end_practice.txt")
        practice_block = False

    block_trials = read_trials(trial_file)
    print(block_trials)
    for trial_count,trial in enumerate(block_trials) :

        stim_1 = trial[0]
        stim_2 = trial[1]

        show_text_and_wait(message = u"Block %d trial %d \n\n EN ATTENTE \n\n Positionner Texture %s - Texture %s \n\n\n Puis appuyez pour démarrer l'acquisition"%(block_count,trial_count,stim_1,stim_2), 
        color = 'orange') 

        event.clearEvents()

        # record audio)
        #audio_recorder.start()   

        # notify recording
        show_text(message= "RECORDING", color = 'green')

        # send start_trial marker
        #if(SEND_MARKERS):
        #    send_marker(stim_tracker, MARKER_CODES['trial_started_%s'%condition])
    
        response_start = time.getTime()

        # wait on event key
        while True :
            response_key = event.getKeys()

            if len(response_key) > 0: 

                if response_key == ['g']: #response 1
                    response_choice = 0
                elif response_key == ['h']: #response 2
                    response_choice = 1
                else : # any other key: stop recording
                    # audio_recorder.stop()
                    show_text(message = "(recording stopped)", color = 'red')
                    event.clearEvents()
                    continue
            
                response_time = time.getTime() - response_start
                #core.wait(0.2)
                show_text(message = "(saving response)", color = 'red')
                break
                
        event.clearEvents()        
        core.wait(0.2)

        
        # log response
        row = [subject_number, trial_count, block_count, practice_block, subject_sex, subject_age, date]
        with open(result_file, 'a') as file :
            writer = csv.writer(file,lineterminator='\n')
            for stim_order,stim in enumerate(trial):
                diameter, opening, spacing = get_stim_info(stim)
                print('Texture %s %f,%f,%f'%(stim,diameter, opening, spacing))
                result = row + [stim, stim_order, diameter, opening, spacing] \
                                 + [response_choice==stim_order, round(response_time,3)]
                writer.writerow(result) #store a line for each x,y pair in the stim

        print("block"+str(block_count)+": trial"+str(trial_count) + ' (practice: '+ str(practice_block)+')')

    # pause at the end of subsequent blocks
    if ((block_count >= n_practice_blocks) and (block_count < n_blocks-1)):
        show_text_and_wait(message = u"Vous avez complété " \
                                + str(Fraction(block_count-n_practice_blocks+1, n_blocks-n_practice_blocks)) \
                                + u" de l'expérience.\n Vous pouvez faire une pause si vous le souhaitez, puis appuyer sur une touche pour continuer.")
        #show_text("pause1.txt")
        #core.wait(5)
       #show_text_and_wait("pause0.txt")


#End of experiment
show_text_and_wait("end.txt")

# Close Python
win.close()
core.quit()
sys.exit()
