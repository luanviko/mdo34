import pyvisa as visa, numpy as np, uproot, progressbar, sys
import matplotlib.pyplot as plt

def display_waveform(x, y, xscale = None, xlabel=None, ylabel=None, xrange=None, yrange=None, title=None):
    fig, (ax0) = plt.subplots(nrows=1, ncols=1, sharey=False, sharex=False, figsize=(8,5))

    ax0.plot(x, y, "black")
    if xrange == None: ax0.set_xlim(x[0], x[-1])
    
    if xrange != None: ax0.set_xlim(xrange)
    if yrange != None: ax0.set_ylim(yrange)
    if xlabel != None: ax0.set_xlabel(xlabel)
    if ylabel != None: ax0.set_ylabel(ylabel)
    if title  != None: ax0.set_title(title)
    
    plt.show()

def to_root(file_name, data):
    # Save data dictionary to a tree in a root file
    # @params: _file_name_ with path to root file and _data_ dict.
    print(f"Saving to: {file_name}.root")
    with uproot.recreate(file_name+".root") as output_file:
        output_file["pulse_information"] = data

def to_npz(file_name, data):
    # Save data dictionary to an npz file
    # @params: _file_name_ with path to npz file and _data_ dict.   
    # print(f"Saving to: {file_name}.npz")
    np.savez_compressed(file_name, **data)


resource_manager = visa.ResourceManager()
# instruments = resource_manager.list_resources()
# print(instruments)

scope = resource_manager.open_resource('USB0::0x0699::0x052C::SGVJ0002263::INSTR')
scope_id = scope.query('*IDN?')
print(scope_id)

status = scope.write(':DATA:SOURCE CH1')
print(f"Status: {status}")

status = scope.write(':DATA:START  1')
print(f"Status: {status}")

status = scope.write(':DATA:STOP   800')
print(f"Status: {status}")

status = scope.write(':DATA:ENC   ASCii')
print(f"Status: {status}")

NR_pt  = int(scope.query(':WFMOutpre:NR_pt?'))
XUNit  = scope.query(':WFMOutpre:XUNit?')
XZEro  = float(scope.query(':WFMOutpre:XZEro?'))
XINcr  = float(scope.query(':WFMOutpre:XINcr?'))
YUNit  = scope.query(':WFMOutpre:YUNit?')  
YZEro  = float(scope.query(':WFMOutpre:YZEro?'))  
YMUlt  = float(scope.query(':WFMOutpre:YMUlt?'))
BYT_nr = int(scope.query(':WFMOutpre:BYT_nr?'))
print(f"Units: {XUNit}, {YUNit}.")

N = int(sys.argv[2]) 
waveforms = np.zeros((N,800), dtype=float)

visa_status = scope.write('ACQ:SEQ:NUMSEQ 1')


x   = np.arange(0, 800, 1)
x_s = np.asarray([XZEro + XINcr*xi for xi in x])

run_number = sys.argv[1]
widgets=[f'Run {run_number}. Channel 0. Preprocessing: ', progressbar.Percentage(), progressbar.Bar('\u2587', '|', '|'), ' ', progressbar.Timer()]

bar = progressbar.ProgressBar(widgets=widgets, maxval=N).start()
i = 0
while i  < N:

    try:
        visa_status = scope.write('ACQ:STATE RUN')
        curve = scope.query('CURVE?')
        curve = curve.replace('\n','')
        waveform = np.asarray([float(element) for element in curve.split(',')])

        y_V = np.asarray([YZEro + YMUlt*yi for yi in waveform])

        for j in range(0, len(y_V)):
            waveforms[i][j] = y_V[j]

        bar.update(i+1)

        if i>1 and i%100 == 0:
            data = {'waveforms':waveforms, 'x_s':x_s}
            to_npz(f"./run-{run_number}.temp", data)

        i += 1 
    
    except:
        print("Unable to read this time.")

data = {'waveforms':waveforms, 'x_s':x_s}

print("\n")
final_file = f"./run-{run_number}"
to_npz(final_file, data)