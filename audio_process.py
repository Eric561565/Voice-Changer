import librosa
from glob import glob
import os
import librosa
import numpy as np
import soundfile as sf
from scipy import signal
from scipy.fft import fft

def volume(data, sca, dtype):
    volume_scalar = 10 ** (sca / 10)
    data_scaled = (data * volume_scalar).astype(dtype)
    return data_scaled

def explosive_prevent(data):
    max = np.max(np.abs(data))
    if max > 1:
        data /= (max)
    return data

def vibration(data, vibra_coef, vibra_index, CHUNK, sin_wave, dtype):
    vib_amp, vib_freq, vib_en = vibra_coef
    if vib_en:
        data = (data * (1 + vib_amp * sin_wave[CHUNK * vibra_index : CHUNK * (vibra_index + 1)])).astype(dtype)
        return data
    return data


def mysin(vibra_coef, RATE):
    vib_amp, vib_freq, vib_en = vibra_coef
    time = np.arange(RATE)
    omega = 2 * np.pi * vib_freq / RATE
    sin_wave = np.sin(omega * time)
    return sin_wave


##### windowing function
def apply_window(input_data):
    # Apply Hann window
    window = np.hanning(len(input_data) + 1)[:-1]
    output_data = input_data * window
    return output_data

#####
def lpc_pitchshift(audioInput, sr, CHUNK, shift_amount, formant_shift_amount):
# index for the big frame
    #frameLengthSamples = CHUNK // 2
    #hopSize = frameLengthSamples // 2
    #numFrames = (len(audioInput) // hopSize) - 1

    # set output array
    audioOutput = np.zeros_like(audioInput, dtype = np.float32)

    # index for the small frame
    frameLengthSamples2 = 2048*2 #CHUNK // 2
    hopSize2 = frameLengthSamples2 // 2
    numFrames2 = (CHUNK*2 // hopSize2) - 1

    # pitch shift amount
    shiftAmount = shift_amount

    # Loop through small frames to get the excitation and OLA
    excitat = np.zeros([CHUNK*2])

    # For LPC
    p = 50                              # LPC coefficient order
    emphCoef = 0.99                      # Pre-emphasis coefficient
    A = np.zeros([numFrames2, p+1], dtype = np.float32)      # LPC coefficient matrix

    if formant_shift_amount != 0:
        shiftedInput = librosa.effects.pitch_shift(audioInput, sr=sr, n_steps=formant_shift_amount)
        ####
        #shiftedInput = signal.lfilter([1, -emphCoef], 1, shiftedInput)
        A_shift = np.zeros([numFrames2, p+1], dtype = np.float32)

    for frameNum2 in range(1, numFrames2 + 1):
        frameStart2 = (frameNum2 - 1) * hopSize2
        frameEnd2 = frameStart2 + frameLengthSamples2

        frame2 = audioInput[frameStart2:frameEnd2]
            
        # Pre-emphasis
        frame2 = signal.lfilter([1, -emphCoef], 1, frame2)

        # Get LPC coefficients
        A[frameNum2 - 1, :] = librosa.lpc(frame2, order=p)

        # get coefficients of shifted formant
        if formant_shift_amount != 0:
            frame2Shifted = shiftedInput[frameStart2:frameEnd2]
            frame2Shifted = signal.lfilter([1, -emphCoef], 1, frame2Shifted)
            A_shift[frameNum2 - 1, :] = librosa.lpc(frame2Shifted, order=p)

        # Get excitation
        frame2 = signal.lfilter(A[frameNum2 - 1, :], 1, frame2)

        # Apply window (assuming apply_window is a function you have defined)
        frame2 = apply_window(frame2)

        # Overlap and add
        excitat[frameStart2:frameEnd2] += frame2

    # shift the pitch
    excitat = librosa.effects.pitch_shift(excitat, sr=sr, n_steps=shiftAmount)

    # Looping through small frames to do LPC filtering
    #filteredFrame = np.zeros([CHUNK], dtype = np.float32)

    for frameNum2 in range(1, numFrames2 + 1):
        frameStart2 = (frameNum2 - 1) * hopSize2
        frameEnd2 = frameStart2 + frameLengthSamples2

        # Get the small frame of excitation
        frame_ex = excitat[frameStart2:frameEnd2]

        # Re-apply the original LPC coefficients
        if formant_shift_amount == 0:
            frame2 = signal.lfilter([1], A[frameNum2 - 1, :], frame_ex)
        else:
            frame2 = signal.lfilter([1], A_shift[frameNum2 - 1, :], frame_ex)

        # De-emphasis
        frame2 = signal.lfilter([1], [1, -emphCoef], frame2)

        # Apply window (assuming apply_window is a function you have defined)
        frame2 = apply_window(frame2)

        # Overlap and add
        audioOutput[frameStart2:frameEnd2] += frame2

    return audioOutput

def lpc(prevFrame, currentFrame, nextFrame, RATE, CHUNK, pitch, formant):
    vol_thresh = 0.02
    # two windows for overlap and add
    frame1 = apply_window(np.concatenate((prevFrame,currentFrame), axis = 0)) + 0.000001
    frame2 = apply_window(np.concatenate((currentFrame,nextFrame), axis = 0)) + 0.000001
    # pitch up both frame
    if np.max(frame1) > vol_thresh:
        frame1 = lpc_pitchshift(frame1, RATE, CHUNK, pitch, formant)
    else:
        frame1[:] = 0
    if np.max(frame2) > vol_thresh:
        frame2 = lpc_pitchshift(frame2, RATE, CHUNK, pitch, formant)
    else:
        frame2[:] = 0

    outputFrame = np.zeros(CHUNK * 3)
    # Copy frame1 to the beginning of the output frame
    outputFrame[:CHUNK * 2] += frame1

    # Add frame2 to the end of the output frame
    outputFrame[-CHUNK * 2:] += frame2

    # normalize amplitude due to weird pitch shift in lpc
    if formant > 0:
        outputFrame = outputFrame * formant**0.5
    elif formant < 0:
        outputFrame = outputFrame / (np.abs(formant)**1.2)
    

    return outputFrame[CHUNK: -CHUNK]

def funda_freq(RATE, CHUNK, data_output):
    frequencies = np.fft.fftfreq(CHUNK, d=1.0/RATE)
    fft_values = fft(data_output)

    # 取得正半軸（正頻率）部分
    positive_frequencies = frequencies[:CHUNK//2]
    positive_fft_values = 2.0/CHUNK * np.abs(fft_values[:CHUNK//2])

    # 找到能量最高的頻率（基頻頻率）
    fundamental_frequency_index = np.argmax(positive_fft_values)
    fundamental_frequency = positive_frequencies[fundamental_frequency_index]

    return fundamental_frequency