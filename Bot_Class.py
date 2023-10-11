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
import TradingStrats as TS
from collections import Counter
import taew
import copy
import Acc


class Bot:
    def __init__(self, symbol: str, Open: [float], Close: [float], High: [float], Low: [float], Volume: [float], Date: [str], OP: int, CP: int, index: int, tick: float,
                 strategy: str, TP_SL_choice: str, SL_mult: float, TP_mult: float, backtesting=0):
        self.symbol = symbol
        self.Date = Date

        # Remove extra candle if present
        shortest = len(Open)
        if shortest > len(Close):
            shortest = len(Close)
        if shortest > len(High):
            shortest = len(High)
        if shortest > len(Low):
            shortest = len(Low)
        if shortest > len(Volume):
            shortest = len(Volume)
        self.Open = Open[:shortest]
        self.Close = Close[:shortest]
        self.High = High[:shortest]
        self.Low = Low[:shortest]
        self.Volume = Volume[:shortest]
        self.resistance_level = 0
        self.support_level = 0

        self.OP = OP
        self.CP = CP
        self.ATR = []
        self.index = index
        self.add_hist_complete = 0
        self.new_data = 0
        self.generate_heikin_ashi = True
        self.Open_H = []
        self.Close_H = []
        self.High_H = []
        self.Low_H = []
        self.tick_size = tick
        self.socket_failed = False
        self.backtesting = backtesting
        self.use_close_pos = False
        self.strategy = strategy
        self.TP_SL_choice = TP_SL_choice
        self.SL_mult = SL_mult
        self.TP_mult = TP_mult
        self.indicators = {}
        self.using_heikin_ashi = False
        self.current_index = -1  ## -1 for live Bot to always reference the most recent candle, will update in Backtester
        self.take_profit_val, self.stop_loss_val = [], []
        self.take_profit_val1, self.stop_loss_val1 = [], []
        self.peaks, self.troughs = [], []
        self.highest_swing = -1
        self.lowest_swing = -1
        self.elliott_wave_label_upward = -1
        self.elliott_wave_label_downward = -1
        # self.Close_peaks = []  ##Store peak values
        # self.location_peaks = []  ##store current_index of peak value , used for debugging
        # self.Close_troughs = []  ##store trough values
        # self.location_troughs = []  ##store current_index of peak trough , used for debugging

        if backtesting:
            self.update_indicators()
            self.update_TP_SL()



    def update_indicators(self):
        ## Calculate indicators
        if self.strategy == 'StochRSIMACD':
            Close = pd.Series(self.Close)
            High = pd.Series(self.High)
            Low = pd.Series(self.Low)
            self.indicators = {"fastd": {"values": list(stoch(close=Close, high=High, low=Low)),
                                         "plotting_axis": 3},
                               "fastk": {"values": list(stoch_signal(close=Close, high=High, low=Low)),
                                         "plotting_axis": 3},
                               "RSI": {"values": list(rsi(Close)),
                                       "plotting_axis": 4},
                               "MACD": {"values": list(macd(Close)),
                                        "plotting_axis": 5},
                               "macdsignal": {"values": list(macd_signal(Close)),
                                              "plotting_axis": 5}
            }
        elif self.strategy == 'tripleEMAStochasticRSIATR':
            Close = pd.Series(self.Close)
            self.indicators = { "EMA_L": {"values": list(ema_indicator(Close, window=50)),
                                          "plotting_axis": 1},
                                "EMA_M": {"values": list(ema_indicator(Close, window=14)),
                                          "plotting_axis": 1},
                                "EMA_S": {"values": list(ema_indicator(Close, window=8)),
                                          "plotting_axis": 1},
                                "fastd": {"values": list(stochrsi_d(Close)),
                                          "plotting_axis": 3},
                                "fastk": {"values": list(stochrsi_k(Close)),
                                          "plotting_axis": 3}
            }
        elif self.strategy == 'tripleEMA':
            Close = pd.Series(self.Close)
            self.indicators = {"EMA_L": {"values": list(ema_indicator(Close, window=50)),
                                         "plotting_axis": 1},
                               "EMA_M": {"values": list(ema_indicator(Close, window=20)),
                                         "plotting_axis": 1},
                               "EMA_S": {"values": list(ema_indicator(Close, window=5)),
                                         "plotting_axis": 1}
            }

        elif self.strategy == 'breakout':
            Close = pd.Series(self.Close)
            Volume = pd.Series(self.Volume)
            High = pd.Series(self.High)
            Low = pd.Series(self.Low)
            highest_swing = self.highest_swing
            lowest_swing = self.lowest_swing


            # self.elliott_wave_label_upward = Acc.ElliottWave_label_upward(Close)
            # self.elliott_wave_label_downward = Acc.ElliottWave_label_downward(Close)

            for i in range(1, len(High) - 1):
                if High[i] > High[i - 1] and High[i] > High[i + 1] and (highest_swing == -1 or High[i] > High[highest_swing]):
                    self.highest_swing = i
                if Low[i] < Low[i - 1] and Low[i] < Low[i + 1] and (lowest_swing == -1 or Low[i] < Low[lowest_swing]):
                    self.lowest_swing = i

            self.indicators ={"max Close % change": {"values": Close.rolling(10).max(),
                                            "plotting_axis": 3},
                              "min Close % change": {"values": Close.rolling(10).min(),
                                            "plotting_axis": 3},
                              "max Volume": {"values": Volume.rolling(10).max(),
                                          "plotting_axis": 2},
                                "fastd": {"values": list(stoch(close=Close, high=High, low=Low)),
                                            "plotting_axis": 3},
                                "fastk": {"values": list(stoch_signal(close=Close, high=High, low=Low)),
                                            "plotting_axis": 3},
                                "RSI": {"values": list(rsi(Close)),
                                        "plotting_axis": 4},
                                "MACD": {"values": list(macd(Close)),
                                        "plotting_axis": 5},
                                "macdsignal": {"values": list(macd_signal(Close)),
                                                "plotting_axis": 5}
            }
        elif self.strategy == 'stochBB':
            Close = pd.Series(self.Close)
            self.indicators = {"fastd": {"values": list(stochrsi_d(Close)),
                                         "plotting_axis": 3},
                               "fastk": {"values": list(stochrsi_k(Close)),
                                         "plotting_axis": 3},
                               "percent_B": {"values": list(bollinger_pband(Close)),
                                             "plotting_axis": 4}
            }
        elif self.strategy == 'goldenCross':
            Close = pd.Series(self.Close)
            self.indicators = {"EMA_L": {"values": list(ema_indicator(Close, window=100)),
                                         "plotting_axis": 1},
                               "EMA_M": {"values": list(ema_indicator(Close, window=50)),
                                         "plotting_axis": 1},
                               "EMA_S": {"values": list(ema_indicator(Close, window=20)),
                                         "plotting_axis": 1},
                               "RSI": {"values": list(rsi(Close)),
                                       "plotting_axis": 3}
            }
        elif self.strategy == 'fibMACD':
            Close = pd.Series(self.Close)
            High = pd.Series(self.High)
            Low = pd.Series(self.Low)
            # print("current_index: ", len(self.current_index))
            period = 100  ##Record peaks and troughs in last period timesteps

            # Close_peaks = []  ##Store peak values
            # location_peaks = []  ##store current_index of peak value , used for debugging
            # Close_troughs = []  ##store trough values
            # location_troughs = []  ##store current_index of peak trough , used for debugging
            # print(len(High))
            #####################Find peaks & troughs in Close ##############################
            # for i in range(len(High) - period, len(High) - 2):
            #     if High[i] > High[i - 1] and High[i] > High[i + 1] and High[i] > High[i - 2] and High[i] > High[i + 2]:
            #         ##Weve found a peak:
            #         self.Close_peaks.append(High[i])
            #         self.location_peaks.append(i)
            #     elif Low[i] < Low[i - 1] and Low[i] < Low[i + 1] and Low[i] < Low[i - 2] and Low[i] < Low[i + 2]:
            #         ##Weve found a trough:
            #         self.Close_troughs.append(Low[i])
            #         self.location_troughs.append(i)

            self.indicators = {"MACD_signal": {"values": list(macd_signal(Close)),
                                               "plotting_axis": 3},
                               "MACD": {"values": list(macd(Close)),
                                        "plotting_axis": 3},
                               "EMA": {"values": list(sma_indicator(Close, window=200)),
                                       "plotting_axis": 1}
            }
        elif self.strategy == 'EMA_cross':
            Close = pd.Series(self.Close)
            self.indicators = {"EMA_S": {"values": list(ema_indicator(Close, window=5)),
                                         "plotting_axis": 1},
                               "EMA_L": {"values": list(ema_indicator(Close, window=20)),
                                        "plotting_axis": 1}
            }
        elif self.strategy == 'heikin_ashi_ema2':
            self.use_close_pos = True
            self.using_heikin_ashi = True ## for graphing heikin ashi candles
            Close = pd.Series(self.Close)
            self.indicators = {"fastd": {"values":list(stochrsi_d(Close)),
                                         "plotting_axis": 3},
                               "fastk": {"values": list(stochrsi_k(Close)),
                                         "plotting_axis": 3},
                               "EMA": {"values": list(ema_indicator(Close, window=200)),
                                       "plotting_axis": 1}
            }
        elif self.strategy == 'heikin_ashi_ema':
            self.use_close_pos = True
            self.using_heikin_ashi = True ## for graphing heikin ashi candles
            Close = pd.Series(self.Close)
            self.indicators = {"fastd": {"values": list(stochrsi_d(Close)),
                                         "plotting_axis": 3},
                               "fastk": {"values": list(stochrsi_k(Close)),
                                         "plotting_axis": 3},
                               "EMA": {"values": list(ema_indicator(Close, window=200)),
                                     "plotting_axis": 1}
            }
        elif self.strategy == 'ema_crossover':
            Close = pd.Series(self.Close)
            self.indicators = {"ema_short": {"values": list(ema_indicator(Close, window=20)),
                                         "plotting_axis": 1},
                               "ema_long": {"values": list(ema_indicator(Close, window=50)),
                                         "plotting_axis": 1},
                               }
        elif self.strategy == 'TripleScreenTradingSystem':
            Close = pd.Series(self.Close)
            Volume = pd.Series(self.Volume)
            self.indicators = {
                "SMA": {"values": list(sma_indicator(Close, window=200)), "plotting_axis": 1},
                "MACD": {"values": list(macd(Close)), "plotting_axis": 3},
                "EMA": {"values": list(sma_indicator(Close, window=200)), "plotting_axis": 1},
                "RSI": {"values": list(rsi(Close)), "plotting_axis": 4},
                "Bollinger Hband": {"values": list(bollinger_hband(Close)), "plotting_axis": 5},
                "Bollinger Lband": {"values": list(bollinger_lband(Close)), "plotting_axis": 6},
                "Force Index": {"values": list(force_index(Close, Volume)), "plotting_axis": 7},
                "macdsignal": {"values": list(macd_signal(Close)), "plotting_axis": 5}
            }

        elif self.strategy == 'EnhancedTripleScreenTradingSystem':
            Close = pd.Series(self.Close)
            Volume = pd.Series(self.Volume)
            High = pd.Series(self.High)
            Low = pd.Series(self.Low)
            self.indicators = {
                "SMA": {"values": list(sma_indicator(Close, window=200)), "plotting_axis": 1},
                "MACD": {"values": list(macd(Close)), "plotting_axis": 3},
                "EMA": {"values": list(sma_indicator(Close, window=200)), "plotting_axis": 1},
                "RSI": {"values": list(rsi(Close)), "plotting_axis": 4},
                "Bollinger Hband": {"values": list(bollinger_hband(Close)), "plotting_axis": 5},
                "Bollinger Lband": {"values": list(bollinger_lband(Close)), "plotting_axis": 6},
                "Force Index": {"values": list(force_index(Close, Volume)), "plotting_axis": 7},
                "MFI": {"values": list(money_flow_index(High, Low, Close, Volume)), "plotting_axis": 8},
                "StochRSI K": {"values": list(stochrsi_k(Close)), "plotting_axis": 9},
                "StochRSI D": {"values": list(stochrsi_d(Close)), "plotting_axis": 10},
            }

        elif self.strategy == 'volume_profile_order_flow_strategy':
            Close = pd.Series(self.Close)
            Volume = pd.Series(self.Volume)
            High = pd.Series(self.High)
            Low = pd.Series(self.Low)
            self.indicators = {
                "SMA": {"values": list(sma_indicator(Close, window=200)), "plotting_axis": 1},
                "MACD": {"values": list(macd(Close)), "plotting_axis": 3},
                "EMA": {"values": list(sma_indicator(Close, window=200)), "plotting_axis": 1},
                "RSI": {"values": list(rsi(Close)), "plotting_axis": 4},
                "Bollinger Hband": {"values": list(bollinger_hband(Close)), "plotting_axis": 5},
                "Bollinger Lband": {"values": list(bollinger_lband(Close)), "plotting_axis": 6},
                "Force Index": {"values": list(force_index(Close, Volume)), "plotting_axis": 7},
                "MFI": {"values": list(money_flow_index(High, Low, Close, Volume)), "plotting_axis": 8},
                "StochRSI K": {"values": list(stochrsi_k(Close)), "plotting_axis": 9},
                "StochRSI D": {"values": list(stochrsi_d(Close)), "plotting_axis": 10},
                "macdsignal": {"values": list(macd_signal(Close)), "plotting_axis": 5}
            }


    def update_TP_SL(self):
        if self.TP_SL_choice == 'x Swing':
            ATR = list(average_true_range(pd.Series(self.High), pd.Series(self.Low), pd.Series(self.Close)))
            self.take_profit_val = [self.TP_mult * abs(ATR[i]) for i in range(len(ATR))]
            self.stop_loss_val = [self.SL_mult * abs(ATR[i]) for i in range(len(ATR))]
            
            self.peaks = [0 if (i < 3 or i > len(self.High) - 4) else self.High[i] if (self.High[i - 1] < self.High[i] > self.High[i + 1]) and (self.High[i - 2] < self.High[i] > self.High[i + 2])
                                                                                      and (self.High[i - 3] < self.High[i] > self.High[i + 3]) else 0 for i in range(len(self.High))]

            self.troughs = [0 if (i < 3 or i > len(self.Low) - 4) else self.Low[i] if (self.Low[i - 1] > self.Low[i] < self.Low[i + 1]) and (self.Low[i - 2] > self.Low[i] < self.Low[i + 2])
                                                                                      and (self.Low[i - 3] > self.Low[i] < self.Low[i + 3]) else 0 for i in range(len(self.Low))]

        if self.TP_SL_choice == 'en':
            High = pd.Series(self.High)
            Low = pd.Series(self.Low)
            highest_swing = self.highest_swing
            lowest_swing = self.lowest_swing

            for i in range(1, len(High) - 1):
                if High[i] > High[i - 1] and High[i] > High[i + 1] and (highest_swing == -1 or High[i] > High[highest_swing]):
                    self.highest_swing = i
                if Low[i] < Low[i - 1] and Low[i] < Low[i + 1] and (lowest_swing == -1 or Low[i] < Low[lowest_swing]):
                    self.lowest_swing = i

            
        ## Run Once in Backtester/ Run every candle in Live Bot
        if self.TP_SL_choice == '%':
            self.take_profit_val = [(self.TP_mult / 100) * self.Close[i] for i in range(len(self.Close))]
            self.stop_loss_val = [(self.SL_mult / 100) * self.Close[i] for i in range(len(self.Close))]

        if self.TP_SL_choice == 'x (ATR)':
            ATR = list(average_true_range(pd.Series(self.High), pd.Series(self.Low), pd.Series(self.Close)))
            # self.take_profit_val = [self.TP_mult * abs(ATR[i]) for i in range(len(ATR))]
            # self.stop_loss_val = [self.SL_mult * abs(ATR[i]) for i in range(len(ATR))]

        if self.TP_SL_choice == 'x (Swing High/Low) level 1':
            self.peaks = [0 if (i < 1 or i > len(self.High) - 2) else self.High[i] if (self.High[i - 1] < self.High[i] > self.High[i + 1]) else 0 for i in range(len(self.High))]

            self.troughs = [0 if (i < 1 or i > len(self.High) - 2) else self.Low[i] if (self.Low[i - 1] > self.Low[i] < self.Low[i + 1]) else 0 for i in range(len(self.Low))]

        if self.TP_SL_choice == 'x (Swing High/Low) level 2':
            self.peaks = [0 if (i < 2 or i > len(self.High) - 3) else self.High[i] if (self.High[i - 1] < self.High[i] > self.High[i + 1]) and (self.High[i - 2] < self.High[i] > self.High[i + 2])
                             else 0 for i in range(len(self.High))]

            self.troughs = [0 if (i < 2 or i > len(self.Low) - 3) else self.Low[i] if (self.Low[i - 1] > self.Low[i] < self.Low[i + 1]) and (self.Low[i - 2] > self.Low[i] < self.Low[i + 2])
                               else 0 for i in range(len(self.Low))]

        if self.TP_SL_choice == 'x (Swing High/Low) level 3':
            self.peaks = [0 if (i < 3 or i > len(self.High) - 4) else self.High[i] if (self.High[i - 1] < self.High[i] > self.High[i + 1]) and (self.High[i - 2] < self.High[i] > self.High[i + 2])
                                                                                      and (self.High[i - 3] < self.High[i] > self.High[i + 3]) else 0 for i in range(len(self.High))]

            self.troughs = [0 if (i < 3 or i > len(self.Low) - 4) else self.Low[i] if (self.Low[i - 1] > self.Low[i] < self.Low[i + 1]) and (self.Low[i - 2] > self.Low[i] < self.Low[i + 2])
                                                                                      and (self.Low[i - 3] > self.Low[i] < self.Low[i + 3]) else 0 for i in range(len(self.Low))]

        if self.TP_SL_choice == 'x (Swing Close) level 1':
            self.peaks = [0 if (i < 1 or i > len(self.Close) - 2) else self.Close[i] if (self.Close[i - 1] < self.Close[i] > self.Close[i + 1]) else 0 for i in range(len(self.Close))]

            self.troughs = [0 if (i < 1 or i > len(self.Close) - 2) else self.Close[i] if (self.Close[i - 1] > self.Close[i] < self.Close[i + 1]) else 0 for i in range(len(self.Close))]

        if self.TP_SL_choice == 'x (Swing Close) level 2':
            self.peaks = [0 if (i < 2 or i > len(self.Close) - 3) else self.Close[i] if (self.Close[i - 1] < self.Close[i] > self.Close[i + 1]) and
                                                                                        (self.Close[i - 2] < self.Close[i] > self.Close[i + 2]) else 0 for i in range(len(self.Close))]

            self.troughs = [0 if (i < 2 or i > len(self.Close) - 3) else self.Close[i] if (self.Close[i - 1] > self.Close[i] < self.Close[i + 1]) and
                                                                                          (self.Close[i - 2] > self.Close[i] < self.Close[i + 2]) else 0 for i in range(len(self.Close))]

        if self.TP_SL_choice == 'x (Swing Close) level 3':

            self.peaks = [0 if (i < 3 or i > len(self.Close) - 4) else self.Close[i] if (self.Close[i - 1] < self.Close[i] > self.Close[i + 1]) and
                                                                                        (self.Close[i - 2] < self.Close[i] > self.Close[i + 2]) and (self.Close[i - 3] < self.Close[i] > self.Close[i + 3])
                             else 0 for i in range(len(self.Close))]

            self.troughs = [0 if (i < 3 or i > len(self.Close) - 4) else self.Close[i] if (self.Close[i - 1] > self.Close[i] < self.Close[i + 1]) and
                                                                                          (self.Close[i - 2] > self.Close[i] < self.Close[i + 2]) and (self.Close[i - 3] > self.Close[i] < self.Close[i + 3])
                               else 0 for i in range(len(self.Close))]

    def add_hist(self, Date_temp: [float], Open_temp: [float], Close_temp: [float], High_temp: [float], Low_temp: [float], Volume_temp: [str]):
        if not self.backtesting:
            while 0 < len(self.Date):
                if self.Date[0] > Date_temp[-1]:
                    Date_temp.append(self.Date.pop(0))
                    Open_temp.append(self.Open.pop(0))
                    Close_temp.append(self.Close.pop(0))
                    High_temp.append(self.High.pop(0))
                    Low_temp.append(self.Low.pop(0))
                    Volume_temp.append(self.Volume.pop(0))
                else:
                    self.Date.pop(0)
                    self.Open.pop(0)
                    self.Close.pop(0)
                    self.High.pop(0)
                    self.Low.pop(0)
                    self.Volume.pop(0)
            self.Date = Date_temp
            self.Open = Open_temp
            self.Close = Close_temp
            self.High = High_temp
            self.Low = Low_temp
            self.Volume = Volume_temp
        if self.generate_heikin_ashi:
            ##Create Heikin Ashi bars
            for i in range(len(self.Close)):
                self.Close_H.append((self.Open[i] + self.Close[i] + self.Low[i] + self.High[i]) / 4)
                if i == 0:
                    self.Open_H.append((self.Close[i] + self.Open[i]) / 2)
                    self.High_H.append(self.High[i])
                    self.Low_H.append(self.Low[i])
                else:
                    self.Open_H.append((self.Open_H[i - 1] + self.Close_H[i - 2]) / 2)
                    self.High_H.append(max(self.High[i], self.Open_H[i], self.Close_H[i]))
                    self.Low_H.append(min(self.Low[i], self.Open_H[i], self.Close_H[i]))
        self.add_hist_complete = 1
        # for i in range(len(self.Date)):
        #    print(f"Date: {self.Date[i]}, Open_H: {self.Open_H[i]}, Close_H: {self.Close_H[i]}, High_H: {self.High_H[i]}, Low_H: {self.Low_H[i]}")

    def handle_socket_message(self, Data, Date=0, Close=0, Volume=0, Open=0, High=0, Low=0):
        try:
            if Data == -99:
                self.Date.append(Date)
                self.Close.append(Close)
                self.Volume.append(Volume)
                self.High.append(High)
                self.Low.append(Low)
                self.Open.append(Open)
                if self.add_hist_complete:
                    self.Date.pop(0)
                    self.Close.pop(0)
                    self.Volume.pop(0)
                    self.High.pop(0)
                    self.Low.pop(0)
                    self.Open.pop(0)
                    if self.generate_heikin_ashi:
                        self.Close_H.append((self.Open[-1] + self.Close[-1] + self.Low[-1] + self.High[-1]) / 4)
                        self.Open_H.append((self.Open_H[-1] + self.Close_H[-2]) / 2)
                        self.High_H.append(max(self.High[-1], self.Open_H[-1], self.Close_H[-1]))
                        self.Low_H.append(min(self.Low[-1], self.Open_H[-1], self.Close_H[-1]))
                        self.Open_H.pop(0)
                        self.Close_H.pop(0)
                        self.Low_H.pop(0)
                        self.High_H.pop(0)
                    self.new_data = 1
            elif Data['Date'] != -99:
                self.Date.append(Data['Date'])
                self.Close.append(Data['Close'])
                self.Volume.append(Data['Volume'])
                self.High.append(Data['High'])
                self.Low.append(Data['Low'])
                self.Open.append(Data['Open'])
                if self.add_hist_complete:
                    self.Date.pop(0)
                    self.Close.pop(0)
                    self.Volume.pop(0)
                    self.High.pop(0)
                    self.Low.pop(0)
                    self.Open.pop(0)
                    if self.generate_heikin_ashi:
                        self.Close_H.append((self.Open[-1] + self.Close[-1] + self.Low[-1] + self.High[-1]) / 4)
                        self.Open_H.append((self.Open_H[-1] + self.Close_H[-2]) / 2)
                        self.High_H.append(max(self.High[-1], self.Open_H[-1], self.Close_H[-1]))
                        self.Low_H.append(min(self.Low[-1], self.Open_H[-1], self.Close_H[-1]))
                        self.Open_H.pop(0)
                        self.Close_H.pop(0)
                        self.Low_H.pop(0)
                        self.High_H.pop(0)
                    self.new_data = 1
                self.update_indicators()
                self.update_TP_SL()
        # except Exception as e:
        #
        except Exception as e:
            print(f"Error in {self.symbol}.handle_socket_message(): ", e)
            self.socket_failed = True
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno) ## Can add this except statement in to code to figure out what line the error was thrown on
    def Make_decision(self):
        ##Initialize vars:
        Trade_Direction = -99  ## Short (0), Long (1)
        stop_loss_val = -99  ##the margin of increase/decrease that would stop us out/ be our take profit, NOT the price target.
        take_profit_val = -99  # That is worked out later by adding or subtracting:
        ## Strategies found in TradingStrats.py:
        if self.strategy == 'StochRSIMACD':
            Trade_Direction = TS.StochRSIMACD(Trade_Direction, self.indicators["fastd"]["values"], self.indicators["fastk"]["values"],
                                              self.indicators["RSI"]["values"], self.indicators["MACD"]["values"],
                                              self.indicators["macdsignal"]["values"], self.current_index)
        elif self.strategy == 'tripleEMAStochasticRSIATR':
            Trade_Direction = TS.tripleEMAStochasticRSIATR(self.Close, Trade_Direction, self.indicators["EMA_L"]["values"],
                                                           self.indicators["EMA_M"]["values"], self.indicators["EMA_S"]["values"],
                                                           self.indicators["fastd"]["values"], self.indicators["fastk"]["values"], self.current_index)
        elif self.strategy == 'tripleEMA':
            Trade_Direction = TS.tripleEMA(Trade_Direction,
                                           self.indicators["EMA_S"]["values"],
                                           self.indicators["EMA_M"]["values"], self.indicators["EMA_L"]["values"], self.current_index)
        elif self.strategy == 'breakout':
            Trade_Direction, fibonacci_levels1 = TS.breakout(Trade_Direction,-99,0, self.High, self.Low,
                                          self.Close, self.Volume, self.indicators["max Close % change"]["values"],
                                          self.indicators["min Close % change"]["values"], self.indicators["max Volume"]["values"],
                                          self.current_index, self.highest_swing, self.lowest_swing, self.elliott_wave_label_upward, self.elliott_wave_label_downward,
                                          self.indicators["fastd"]["values"], self.indicators["fastk"]["values"],
                                              self.indicators["RSI"]["values"], self.indicators["MACD"]["values"],
                                              self.indicators["macdsignal"]["values"], self.Open)

                                          
        elif self.strategy == 'stochBB':
            Trade_Direction = TS.stochBB(Trade_Direction, self.indicators["fastd"]["values"],
                                         self.indicators["fastk"]["values"], self.indicators["percent_B"]["values"], self.current_index)
        elif self.strategy == 'goldenCross':
            Trade_Direction = TS.goldenCross(Trade_Direction, self.Close, self.indicators["EMA_L"]["values"],
                                             self.indicators["EMA_M"]["values"], self.indicators["EMA_S"]["values"],
                                             self.indicators["RSI"]["values"], self.current_index)
        elif self.strategy == 'candle_wick':
            Trade_Direction = TS.candle_wick(Trade_Direction, self.Close, self.Open, self.High, self.Low, self.current_index)
        elif self.strategy == 'fibMACD':
            Trade_Direction = TS.fibMACD(Trade_Direction, self.Close, self.Open,
                                                                         self.High, self.Low, self.indicators["MACD_signal"]["values"],
                                                                         self.indicators["MACD"]["values"], self.indicators["EMA"]["values"],
                                                                         self.current_index,
                                                                         self.stop_loss_val, self.take_profit_val,
                                                                         self.highest_swing, self.lowest_swing)

        elif self.strategy == 'EMA_cross':
            Trade_Direction = TS.EMA_cross(Trade_Direction, self.indicators["EMA_S"]["values"],
                                           self.indicators["EMA_L"]["values"], self.current_index)
        elif self.strategy == 'heikin_ashi_ema2':
            Trade_Direction, _ = TS.heikin_ashi_ema2(self.Open_H, self.High_H, self.Low_H,
                                                     self.Close_H, Trade_Direction,
                                                     -99, 0, self.indicators["fastd"]["values"], self.indicators["fastk"]["values"],
                                                     self.indicators["EMA"]["values"], self.current_index)
        elif self.strategy == 'heikin_ashi_ema':
            Trade_Direction, _ = TS.heikin_ashi_ema(self.Open_H, self.Close_H, Trade_Direction, -99, 0,
                                                    self.indicators["fastd"]["values"],
                                                    self.indicators["fastk"]["values"],
                                                    self.indicators["EMA"]["values"], self.current_index)
        elif self.strategy == "ema_crossover":
            Trade_Direction = TS.ema_crossover(Trade_Direction, self.current_index,
                                               self.indicators["ema_short"]["values"],
                                               self.indicators["ema_long"]["values"])
            
        elif self.strategy == "TripleScreenTradingSystem":
            Trade_Direction = TS.TripleScreenTradingSystem(Trade_Direction,
                                                           self.indicators["MACD"]["values"],
                                                           self.indicators["RSI"]["values"],
                                                           self.indicators["SMA"]["values"],
                                                           self.indicators["EMA"]["values"],
                                                           self.indicators["Bollinger Hband"]["values"],
                                                           self.indicators["Bollinger Lband"]["values"],
                                                           self.indicators["Force Index"]["values"],
                                                           self.indicators["macdsignal"]["values"],
                                                           self.current_index)
        elif self.strategy == "EnhancedTripleScreenTradingSystem":
            Trade_Direction  = TS.EnhancedTripleScreenTradingSystem(Trade_Direction,self.High, self.Low,
                                                           self.Close,
                                                           self.indicators["RSI"]["values"],
                                                           self.indicators["StochRSI K"]["values"],
                                                           self.indicators["StochRSI D"]["values"],
                                                           self.indicators["SMA"]["values"],
                                                           self.indicators["EMA"]["values"],
                                                           self.indicators["Bollinger Hband"]["values"],
                                                           self.indicators["Bollinger Lband"]["values"],
                                                           self.indicators["Force Index"]["values"],
                                                           self.indicators["MFI"]["values"],
                                                           self.current_index)
        
        elif self.strategy == "volume_profile_order_flow_strategy":
            Trade_Direction = TS.volume_profile_order_flow_strategy(Trade_Direction,
                                                           self.indicators["MACD"]["values"],
                                                           self.indicators["RSI"]["values"],
                                                           self.indicators["StochRSI K"]["values"],
                                                           self.indicators["StochRSI D"]["values"],
                                                           self.indicators["macdsignal"]["values"],
                                                           self.current_index)

        ## Get TP/SL values if we enter a trade:
        if Trade_Direction != -99:
            stop_loss_val, take_profit_val = TS.SetSLTP(self.ATR,self.stop_loss_val, self.take_profit_val,self.stop_loss_val1, self.take_profit_val1, self.peaks,
                                                        self.troughs,
                                                        self.Close, self.High, self.Low, Trade_Direction, self.SL_mult,
                                                        self.TP_mult, self.TP_SL_choice,
                                                        self.current_index, self.resistance_level, self.support_level, self.highest_swing, self.lowest_swing, self.Open, fibonacci_levels1)
        return Trade_Direction, stop_loss_val, take_profit_val

    def check_close_pos(self, Trade_Direction):
        close_pos = 0
        if self.strategy == 'heikin_ashi_ema2':
            _, close_pos = TS.heikin_ashi_ema2(self.Open_H, self.High_H, self.Low_H,
                                               self.Close_H, -99, Trade_Direction,
                                                0, self.indicators["fastd"]["values"], self.indicators["fastk"]["values"],
                                               self.indicators["EMA"]["values"], self.current_index)
        elif self.strategy == 'heikin_ashi_ema':
            _, close_pos = TS.heikin_ashi_ema(self.Open_H, self.Close_H, -99, Trade_Direction, 0,
                                              self.indicators["fastd"]["values"], self.indicators["fastk"]["values"], self.indicators["EMA"]["values"], self.current_index)
            
        # elif self.strategy == 'breakout':
        #     _, close_pos = TS.breakout(Trade_Direction,-99,0, self.High, self.Low,
        #                                   self.Close, self.Volume, self.indicators["max Close % change"]["values"],
        #                                   self.indicators["min Close % change"]["values"], self.indicators["max Volume"]["values"],
        #                                   self.current_index)
        return close_pos
