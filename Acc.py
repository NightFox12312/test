import os
import sys
from datetime import datetime
import time
from ta.momentum import stochrsi_d, stochrsi_k, stoch, stoch_signal, rsi, awesome_oscillator
from ta.trend import ema_indicator, macd_signal, macd, sma_indicator, adx, sma_indicator, cci
from ta.volatility import average_true_range, bollinger_pband, bollinger_hband, bollinger_lband, bollinger_mavg
from ta.volume import ease_of_movement, on_balance_volume, force_index, money_flow_index
from ta.momentum import tsi
from ta.trend import stc
import numpy as np
import pandas as pd
from collections import Counter
import taew
import copy

def ElliottWave_label_upward(data):
    v = data
    j = range(len(data))
    x = []
    # finding the high point and low point
    for i in range(1, len(v) - 1):
        if (v[i] <= v[i + 1] and v[i - 1] >= v[i]) or (v[i] >= v[i + 1] and v[i - 1] <= v[i]):
            # finding peaks and valleys and then place in a new matrix
            x.append(v[i])

    listofCandidateWave = []
    for i in range(len(x)):
        for j in range(len(x)):
            if x[i] < x[j]:
                wave = {
                    'x': [x[i], x[j]],
                }
                listofCandidateWave.append(wave)

    # print(len(listofCandidateWave))
    # print('successfully filter out candidate wave')

    listofCandidateWave12 = []

    for i in range(len(listofCandidateWave)):
        startSearchIndex = 0
        timeInterval = (listofCandidateWave[i]['x'][1] - listofCandidateWave[i]['x'][0]) * 0.4011
        for j in range(startSearchIndex, len(x)):
            if x[j] < listofCandidateWave[i]['x'][1] and x[j] > listofCandidateWave[i]['x'][0]:
                currWave = copy.deepcopy(listofCandidateWave[i])
                currWave['x'].append(x[j])
                listofCandidateWave12.append(currWave)

    # print(len(listofCandidateWave12))
    # print('successfully filter out candidate wave 12')
    listofCandidateWave123 = []
    for i in range(len(listofCandidateWave12)):
        startSearchIndex = 0
        timeInterval = (listofCandidateWave12[i]['x'][1] - listofCandidateWave12[i]['x'][0]) * 1.6989
        for j in range(startSearchIndex, len(x)):
            if x[j] > listofCandidateWave12[i]['x'][2] and x[j] > listofCandidateWave12[i]['x'][1]:
                currWave = copy.deepcopy(listofCandidateWave12[i])
                currWave['x'].append(x[j])
                listofCandidateWave123.append(currWave)

    print(len(listofCandidateWave123))
    print('successfully filter out candidate wave123')

    return listofCandidateWave123

def ElliottWave_label_downward(data):
    v = data
    j = range(len(data))
    x = []
    # finding the high point and low point
    for i in range(1, len(v) - 1):
        if (v[i] <= v[i + 1] and v[i - 1] >= v[i]) or (v[i] >= v[i + 1] and v[i - 1] <= v[i]):
            # finding peaks and valleys and then place in a new matrix
            x.append(v[i])

    listofCandidateWave = []
    for i in range(len(x)):
        for j in range(len(x)):
            if x[i] > x[j]:
                wave = {
                    'x': [x[i], x[j]],
                }
                listofCandidateWave.append(wave)

    listofCandidateWave12 = []

    for i in range(len(listofCandidateWave)):
        startSearchIndex = 0
        timeInterval = (listofCandidateWave[i]['x'][1] - listofCandidateWave[i]['x'][0]) * 0.4011
        for j in range(startSearchIndex, len(x)):
            if x[j] > listofCandidateWave[i]['x'][1] and x[j] < listofCandidateWave[i]['x'][0]:
                currWave = copy.deepcopy(listofCandidateWave[i])
                currWave['x'].append(x[j])
                listofCandidateWave12.append(currWave)

    listofCandidateWave123 = []
    for i in range(len(listofCandidateWave12)):
        startSearchIndex = 0
        timeInterval = (listofCandidateWave12[i]['x'][1] - listofCandidateWave12[i]['x'][0]) * 1.6989
        for j in range(startSearchIndex, len(x)):
            if x[j] < listofCandidateWave12[i]['x'][2] and x[j] > listofCandidateWave12[i]['x'][1]:
                currWave = copy.deepcopy(listofCandidateWave12[i])
                currWave['x'].append(x[j])
                listofCandidateWave123.append(currWave)

    print(len(listofCandidateWave123))
    print('successfully filter out candidate wave123')

    return listofCandidateWave123
# from roboflow import Roboflow
# rf = Roboflow(api_key="jCGFD1ucfkLsbCS5eZgr")
# project = rf.workspace("benhvien").project("truong-okgz6")
# dataset = project.version(2).download("darknet")