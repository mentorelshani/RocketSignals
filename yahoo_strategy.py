import yfinance as yf
import pandas as pd


import csv

# open input file
file = open("input_ticker.csv")

# open output file
file2 = open("results.csv", 'w')
file3 = open("results_winning.csv", 'w')

csvreader = csv.reader(file)
writer = csv.writer(file2)
writer_win = csv.writer(file3)
header = ["ticker", "present_period", "win_made", "lost_made", "giveup_made", "win_percentage", "profit", "capital"]
writer.writerow(header)
writer_win.writerow(header)

# define time period of analysis
period_array = ['1y', '5y', '10y', '20y']

# start cycle for each Ticker in input file
for row in csvreader:
    # start cycle for each time period in period_array
    for present_period in period_array:

        # print name of stock
        print("\n", row[0] , "stocks for", present_period)

        # download data from yf
        ticker= row
        data = yf.download(ticker, group_by="Ticker", period=present_period)
        download_success = [r for r in data['Close'] if r > 0]
        if (not(download_success)): break

        # convert df to array
        open_pr2 = (data.iloc[:, 0])
        open_pr = open_pr2.to_numpy()
        high_pr2 = (data.iloc[:, 1])
        high_pr = high_pr2.to_numpy()
        low_pr2 = (data.iloc[:, 2])
        low_pr = low_pr2.to_numpy()
        close_pr2 = (data.iloc[:, 3])
        close_pr = close_pr2.to_numpy()


        # initialize variables
        n_row = len(open_pr)
        i = 0
        buy = False
        uptrend = 0
        take_profit = 0
        stop_loss = 0
        strong_up = False
        win_made = 0
        lost_made = 0
        giveup_made = 0
        strong_market = False
        delta = [0]*n_row
        ATR = [0]*n_row
        MA20 = [0]*n_row
        MA50 = [0]*n_row
        MA200 = [0]*n_row
        Keltner_low = [0]*n_row
        Keltner_high= [0] * n_row
        i_cl = 0
        i_op = 0
        profit = 0
        quantity = 0
        buy_pr = 0
        capital = 1000

        # start cycle for data (day candlestick)
        while i < n_row:

            # compute ATR
            delta1 = high_pr[i] - low_pr[i]
            if i > 0:
                delta2 = abs(high_pr[i] - close_pr[i-1])
                delta3 = abs(low_pr[i] - close_pr[i-1])
                delta[i] = max(delta1, delta2, delta3)
            else:
                delta[i] = delta1

            if i > 12:
                j = 0
                while j < 14:
                    ATR[i] += delta[i - j]
                    j += 1
                ATR[i] = ATR[i] / 14

            # compute Moving Averages & Keltner channels
            if i > 18:
                j = 0
                while j < 20:
                    MA20[i] += float(close_pr[i - j])
                    j += 1
                MA20[i] = MA20[i] / 20
                Keltner_low[i] = MA20[i] - 2.5 * ATR[i]
                Keltner_high[i] = MA20[i] + 2.5 * ATR[i]
            if i > 48:
                MA50[i] = MA20[i] * 20
                while j < 50:
                    MA50[i] += float(close_pr[i - j])
                    j += 1
                MA50[i] = MA50[i] / 50

            win = 0
            # Our strategy

            # exit conditions
            if buy:
                # too many days -> exit from trade
                if (i - i_op) > 20:
                    win = -2
                    buy = False
                    strong_up = False
                    uptrend = 0
                    #print("You give up")
                    #print(data.iloc[i])
                    giveup_made += 1
                    i_cl = i
                    profit = profit + quantity * (close_pr[i] - MA20[i_op])
                # take loss
                elif low_pr[i] < stop_loss:
                    win = -1
                    buy = False
                    strong_up = False
                    uptrend = 0
                    #print("You loose")
                    #print(data.iloc[i])
                    lost_made += 1
                    i_cl = i
                    profit = profit + quantity * (stop_loss - MA20[i_op])
                # take profit
                elif high_pr[i] > take_profit:
                    win = 1
                    buy = False
                    strong_up = False
                    uptrend = 0
                    #print("You win")
                    #print(data.iloc[i])
                    win_made += 1
                    i_cl = i
                    profit = profit + quantity * (take_profit - MA20[i_op])

            # decide if I should buy -> core strategy to modify
            elif i > 30:
                long = 1
                st_good = 1
                strong_market = False
                j = 1
                while st_good == 1:
                    if ((low_pr[i-j] < MA20[i-j]) or j > 29 or (i-j) < i_cl):
                        st_good = 0
                        if (j < 10):
                            long = 0
                    if high_pr[i-j] > Keltner_high[i-j]:
                        strong_market = True
                        #print("strong_market")
                    j = j + 1

                # buy it
                if strong_market and long and low_pr[i] < MA20[i]:
                    buy = True
                    #print(buy)
                    #print("You are buying")
                    #print(data.iloc[i])
                    buy_price = MA20[i]
                    quantity = int(capital/buy_price)
                    #print(quantity)
                    i_op = i
                    take_profit = MA20[i] + 2 * ATR[i]
                    stop_loss = MA20[i] - 2 * ATR[i]


            #print(data.iloc[i])
            #print(MA20[i])
            #print(ATR[i])
            i = i + 1

        # compute winning and losses
        if(win_made > 0) : win_percentage = win_made/(lost_made+win_made+giveup_made)
        else: win_percentage = 0
        print("number of win made", win_made )
        print("number of lost made", lost_made )
        print("number of give up", giveup_made )
        print("ratio %", win_percentage)
        print("the profit is ", profit, " out of ", capital)

        # write results on file
        results = [ticker, present_period, win_made, lost_made, giveup_made, win_percentage, profit, capital]
        writer.writerow(results)

        if win_percentage > 0.6:
            writer_win.writerow(results)

#close files
file.close()
file2.close()
file3.close()