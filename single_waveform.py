import pyvisa as visa, numpy as np, sys
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


# status = scope.write(':DATA:ENC   FAStest')
status = scope.write('WFMOutpre:ENCdg BINary')
print(f"Status: {status}")

status = scope.write('WFMOutpre:BIN_Fmt RI')
print(f"Status: {status}")

status = scope.write('WFMOutpre:BYT_Or MSB')
print(f"Status: {status}")

status = scope.write('DATA:WIDTH 2')
print(f"Status: {status}")

#
#  visa_status = scope.write('ACQ:SEQ:NUMSEQ 1')
# visa_status = scope.write('ACQ:STATE RUN')
# visa_status = scope.write('MEAS:MEAS1:SOURCE CH1')
# visa_status = scope.write('MEAS:MEAS1:TYPE AMP')
# measurements = scope.query(':MEASUrement:MEAS1?')
# print("Measurement:", measurements)

# measurements = scope.query(':MEASUrement:MEAS1:VALUE?')
# print("Measurement:", measurements)



# # visa_status = scope.write(':MEASUrement:IMMed:SOUrce1 CH1')
# # visa_status = scope.write(':MEASUrement:IMMed:TYPE FALL')
# # # measurements = scope.query(':MEASUrement:MEAS1:VALUE?')
# # measurements = scope.query(':MEASUrement:IMM:VALUE?')


curve = scope.query('CURVE?')
print(curve)
# print(int(curve,10))
print(curve[0:5])
print(int(curve[5:],2))

sys.exit(1)
curve = curve.replace('\n','')
waveform = np.asarray([float(element) for element in curve.split(',')])

x   = np.arange(0, len(waveform), 1)
x_s = np.asarray([XZEro + XINcr*xi for xi in x])
x_ns = x_s*1.e9
y_V = np.asarray([YZEro + YMUlt*yi for yi in waveform])
y_mV = y_V*1.3

# print(y_V)
# print(x_ns)
display_waveform(x_ns, y_mV)


# CH0:YUNits V
# CH0:XUNits s