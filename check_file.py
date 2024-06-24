import numpy as np, os, time, sys
import matplotlib.pyplot as plt

def wait_modification(npz_file, created=None):
    if created==None: 
        created  = os.path.getctime(npz_file)
    modified = False
    while modified == False:
        created_now  = os.path.getctime(npz_file)
        if created_now == created:
            time.sleep(30)
            created = created_now
        if created_now != created:
            print("File modified at: ", created)
            modified = True

def analyze_data(npz_file, A=None, B=None, j_A=10, j_B=100, auto_window = False):
    
    data  = np.load(npz_file)
    N_entries = waveforms.shape[0]
    waveforms = data['waveforms']*1.e3

    area     = np.zeros(N_entries)
    height   = np.zeros(N_entries)
    position = np.zeros(N_entries)

    if A == None: A = 0
    if B == None: B = 1024
    
    if auto_window == False: print(f"Integration window: {A} Sa to {B} Sa.")
    if auto_window == True : print(f"Integration window: j_max-{j_A} to j_max+{j_B}.")
    
    for i in range(0, N_entries):
        baseline = np.average(waveforms[i][0:30])
        waveforms[i] = waveforms[i]-baseline
        j_max = np.argmax(-1.*waveforms[i])
        position[i] = j_max
        height[i]   = -1.*waveforms[i][j_max]
        if auto_window == True:
            A = j_max - j_A
            B = j_max + j_B
            if A  <= 0:   A = 0
            if B  > 1024: B = 1024
        area[i]     = -1.*np.sum(waveforms[i][A:B])
        if i%1000 == 0: progress.value += 1000
 
    return {"area":area, "height":height, "position":position}

def plot_update(npz_file):

    pulse_information = analyze_data(npz_file)
    fig, (ax0) = plt.subplots(nrows=2, ncols=1, sharey=False, sharex=False, figsize=(8,10)) 

def main():
    npz_file = sys.argv[1]
    cycle = True
    while cycle == True:
        wait_modification(npz_file)