import pyaudio
import numpy as np
import tkinter as tk
from audio_process import volume
from audio_process import vibration
from audio_process import mysin
from audio_process import lpc
from audio_process import explosive_prevent
from audio_process import funda_freq
import threading

audio = pyaudio.PyAudio()
quit = False

RATE = 44100
CHUNK = 2048 * 4

### default value
# delay: 用來處理回音，以秒為單位
delay_coef = 0.3
# volume: 放大與縮小聲音，以dB為單位
volume_coef = 0
# vibration: vibra_amp: 顫音效果([0, 1])、vibra_freq: 顫音週期、vibra_en: 顫音開啟
vibra_amp = 0.5
vibra_freq = 6
vibra_en = 0
vibra_coef = [vibra_amp, vibra_freq, vibra_en]
# pitch: 調整音高，單位為1個半音
pitch_coef = 0
formant_coef = 0

# just initialize global var
dbt_en = 0
bot_dbt_on = None
bot_dbt_off = None
bot_vib_on = None
bot_vib_off = None
input_db = 0.0
fundamental_frequency = 0
stream_off = False

def update_vol(vol_value):
    # 更新vol
    global volume_coef
    volume_coef = int(vol_value)
    print(f"Parameter value updated to: {volume_coef}")

def update_pitch(pitch_value):
    # 更新pitch
    global pitch_coef
    pitch_coef = int(pitch_value)
    print(f"Parameter value updated to: {pitch_coef}")

def update_formant(formant_value):
    # 更新formant
    global formant_coef
    formant_coef = int(formant_value)
    print(f"Parameter value updated to: {formant_coef}")

def turn_on_dbt():
    global dbt_en
    global bot_dbt_on
    global bot_dbt_off
    dbt_en = 1
    bot_dbt_on.config(foreground='red')
    bot_dbt_off.config(foreground='black')
    print(f"Turn on double note.")

def turn_off_dbt():
    global dbt_en
    global bot_dbt_on
    global bot_dbt_off
    dbt_en = 0
    bot_dbt_on.config(foreground='black')
    bot_dbt_off.config(foreground='red')
    print(f"Turn off double note.")

def turn_on_vib():
    global vibra_en
    global bot_vib_on
    global bot_vib_off
    vibra_en = 1
    bot_vib_on.config(foreground='red')
    bot_vib_off.config(foreground='black')
    print(f"Turn on vibration.")

def turn_off_vib():
    global vibra_en
    global bot_vib_on
    global bot_vib_off
    vibra_en = 0
    bot_vib_on.config(foreground='black')
    bot_vib_off.config(foreground='red')
    print(f"Turn off vibration.")

# 開啟GUI 調整器視窗
def update_parameter():
    global bot_dbt_on
    global bot_dbt_off
    global bot_vib_on
    global bot_vib_off
    global fundamental_frequency
    # generate root
    root = tk.Tk()
    root.geometry("600x400+400+300")
    root.title("Voice Effect Controller")

    # generate grid
    f = tk.Frame(root, width=800, height=500, borderwidth=20)
    f.grid(row=0,column=0)
    # Set row height and column width for the frame
    f.grid_rowconfigure(0, minsize=80)  
    f.grid_rowconfigure(1, minsize=50)  
    f.grid_rowconfigure(2, minsize=50) 
    f.grid_rowconfigure(3, minsize=50) 
    f.grid_rowconfigure(4, minsize=50) 
    f.grid_rowconfigure(5, minsize=50) 
    f.grid_columnconfigure(0, minsize=60)  
    f.grid_columnconfigure(1, minsize=100)
    f.grid_columnconfigure(2, minsize=50)  
    f.grid_columnconfigure(3, minsize=20)  
    f.grid_columnconfigure(4, minsize=60)  
    f.grid_columnconfigure(5, minsize=20)  
    # title
    title_str = tk.StringVar()
    title_str.set('Voice Effect Controller')
    title = tk.Label(f, textvariable=title_str, font=('Courier', 30))
    title.grid(row=0,column=0,columnspan=6)

    # volume
    vol_str = tk.StringVar()
    vol_str.set('volume')
    l_vol = tk.Label(f, textvariable=vol_str, justify=tk.LEFT, font=('Courier', 12))
    l_vol.grid(row=1, column=0)

    slider = tk.Scale(f, from_=-10, to=10, orient=tk.HORIZONTAL, length=150, command=update_vol)
    slider.grid(row=1,column=1, columnspan=2, sticky="n")

    # db
    vol_db_str = tk.StringVar()
    vol_db_str.set('Input Volume(dB): ')
    db_title = tk.Label(f, textvariable=vol_db_str, justify=tk.LEFT, font=('Courier', 12))
    db_title.grid(row=1, column=4, sticky="e")

    decibel_str = tk.StringVar()
    decibel_str.set("{:8.2f}".format(input_db))
    db_vol = tk.Label(f, textvariable=decibel_str, justify=tk.LEFT, font=('Courier', 12), background='black', foreground='white')
    db_vol.grid(row=1, column=5, sticky="w")

    # 實時更新decibel
    def update_db():
        global input_db
        nonlocal decibel_str
        decibel_str.set("{:8.2f}".format(input_db))
        root.after(200, update_db)
    update_db()

    # pitch
    pitch_str = tk.StringVar()
    pitch_str.set('pitch')
    l_pitch = tk.Label(f, textvariable=pitch_str, justify=tk.LEFT, font=('Courier', 12))
    l_pitch.grid(row=2, column=0)

    slider = tk.Scale(f, from_=-15, to=15, orient=tk.HORIZONTAL, length=150, command=update_pitch)
    slider.grid(row=2,column=1, columnspan=2, sticky="n")

    # fundamental frequency
    ff_str = tk.StringVar()
    ff_str.set('Fund. Freq.(Hz): ')
    ff_title = tk.Label(f, textvariable=ff_str, justify=tk.LEFT, font=('Courier', 12))
    ff_title.grid(row=2, column=4, sticky="e")

    ff_n_str = tk.StringVar()
    ff_n_str.set("{:8.2f}".format(fundamental_frequency))
    ff_n = tk.Label(f, textvariable=ff_n_str, justify=tk.LEFT, font=('Courier', 12), background='black', foreground='white')
    ff_n.grid(row=2, column=5, sticky="w")

    # 實時更新fundamental frequency
    def update_fundamental_frequency():
        global fundamental_frequency
        nonlocal ff_n_str
        ff_n_str.set("{:8.2f}".format(fundamental_frequency))
        root.after(200, update_fundamental_frequency)
    update_fundamental_frequency()

    # formant
    formant_str = tk.StringVar()
    formant_str.set('formant')
    l_formant = tk.Label(f, textvariable=formant_str, justify=tk.LEFT, font=('Courier', 12))
    l_formant.grid(row=3, column=0)

    slider = tk.Scale(f, from_=-15, to=15, orient=tk.HORIZONTAL, length=150, command=update_formant)
    slider.grid(row=3,column=1, columnspan=2, sticky="n")

    # dbt
    dbt_str = tk.StringVar()
    dbt_str.set('dbt')
    l_dbt = tk.Label(f, textvariable=dbt_str, justify=tk.LEFT, font=('Courier', 12))
    l_dbt.grid(row=4, column=0)

    bot_dbt_on = tk.Button(f, text = 'On', foreground='black', command=turn_on_dbt)
    bot_dbt_on.grid(row=4,column=1)

    bot_dbt_off = tk.Button(f, text = 'Off', foreground='red', command=turn_off_dbt)
    bot_dbt_off.grid(row=4,column=2)
    
    # vib
    vib_str = tk.StringVar()
    vib_str.set('tremolo')
    l_vib = tk.Label(f, textvariable=vib_str, justify=tk.LEFT, font=('Courier', 12))
    l_vib.grid(row=5, column=0)

    bot_vib_on = tk.Button(f, text = 'On', foreground='black', command=turn_on_vib)
    bot_vib_on.grid(row=5,column=1)

    bot_vib_off = tk.Button(f, text = 'Off', foreground='red', command=turn_off_vib)
    bot_vib_off.grid(row=5,column=2)

    # quit bottom
    def Quit():
        root.destroy()
        global quit
        quit = True
    bot_quit = tk.Button(f, text = 'Quit', command=Quit)
    bot_quit.grid(row=5,column=5,sticky="w")

    root.mainloop()
    global quit
    quit = True
    
# 開啟音訊流（錄音和播放）
def record_and_play(RATE, CHUNK, format_num = np.float32):
    FORMAT = pyaudio.paFloat32
    global pitch_coef
    global formant_coef
    global volume_coef
    global vibra_coef
    global dbt_en
    global quit
    global vibra_en
    global vibra_amp
    global vibra_freq
    global input_db
    global fundamental_frequency
    global stream_off
    
    stream_in = audio.open(format = FORMAT, channels = 1,
                           rate = RATE, input = True,
                           frames_per_buffer = CHUNK)

    stream_out = audio.open(format = FORMAT, channels = 1,
                            rate = RATE, output = True,
                            frames_per_buffer = CHUNK)
    
    currentFrame = np.zeros(CHUNK)
    prevFrame = np.zeros(CHUNK)
    nextFrame = np.zeros(CHUNK)
    
    print("錄音和播放開始...")
    
    vibra_index = 0
    sin_wave = mysin(vibra_coef, RATE)
    energy_background = 0

    while quit == False:
        data = stream_in.read(CHUNK)
        # update prevFrame
        prevFrame = currentFrame.copy()
        # update currentFrame
        currentFrame = nextFrame.copy()
        # 將音訊數據轉換為 NumPy 陣列
        nextFrame = np.frombuffer(data, format_num)

        # calculate input energy
        energy_data = np.sum(np.square(nextFrame))
        
        if energy_background == 0:
            energy_background = energy_data
        
        if energy_data < energy_background:
            energy_background = energy_data
        
        #print(energy_background)
        #print(energy_data)
        input_db = 10 * np.log10(energy_data / CHUNK)

        # Select only the middle frame for output
        data_pitched = lpc(prevFrame, currentFrame, nextFrame, RATE, CHUNK, pitch_coef, formant_coef)
        
        # 調整音量
        data_scaled = volume(data_pitched, volume_coef, format_num)
        data_scaled_ori = volume(currentFrame, volume_coef, format_num)

        # 顫音
        vibra_coef = [vibra_amp, vibra_freq, vibra_en]
        if vibra_en == 1:
            data_vibrato = vibration(data_scaled, vibra_coef, vibra_index, CHUNK, sin_wave, format_num)
        else:
            data_vibrato = data_scaled

        if (vibra_index < RATE / CHUNK - 2):
            vibra_index = vibra_index + 1
        else:
            vibra_index = 1

        # 雙音
        if dbt_en == 1:
            data_double = (data_scaled_ori + data_vibrato) / 2
        else:
            data_double = data_vibrato
        
        # 防爆
        data_output = explosive_prevent(data_double)
        
        # 基頻
        fundamental_frequency = funda_freq(RATE, CHUNK, data_output)
        #print("基頻頻率：", fundamental_frequency, "Hz")
        
        # output
        stream_out.write(data_output.tobytes())
    else:
        print("錄音和播放結束...")

        stream_in.stop_stream()
        stream_in.close()
        stream_out.stop_stream()
        stream_out.close()
        stream_off = True

if __name__ == "__main__":
    # 以threading 創建record and play
    th = threading.Thread(target=record_and_play, args=(RATE, CHUNK))
    th.start()
    update_parameter()
    if stream_off:
        audio.terminate()
