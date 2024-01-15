# Voice-Changer

這是一個實作變聲器的project

本project利用Linear predictive coding(LPC)方法實作

透過調整pitch和formant來達到變聲效果

並同時添加雙音和震音的效果器



使用方法

在python3.9.18的環境，安裝requirement.txt內的函式庫

並且執行main.py，即可看到GUI

GUI可調整volume, pitch, formant的參數，並且有雙音、震音的開關

右方顯示的是input聲音的大小(-inf~0dB)和基頻(Hz)
