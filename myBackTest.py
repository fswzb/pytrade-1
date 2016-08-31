
# -*- coding:utf-8 -*-
import tradeStrategy as tds
import sendEmail as se
import tradeTime as tt
import tushare as ts
import pdSql as pds
import sys
from pydoc import describe

def get_stop_trade_symbol():
    today_df = ts.get_today_all()
    today_df = today_df[today_df.amount>0]
    today_df_high_open = today_df[today_df.open>today_df.settlement*1.005]
    all_trade_code = today_df['code'].values.tolist()
    all_a_code = pds.get_all_code(hist_dir="C:/中国银河证券海王星/T0002/export/")
    #all_a_code = pds.get_all_code(hist_dir="C:/hist/day/data/")
    all_stop_codes = list(set(all_a_code).difference(set(all_trade_code)))
    return all_stop_codes


def get_stopped_stocks(given_stocks=[],except_stocks=[]):
    import easyquotation
    quotation =easyquotation.use('qq')
    stop_stocks = []
    if given_stocks:
        this_quotation = quotation.stocks(given_stocks)
    else:
        this_quotation = quotation.all
    for stock_code in (this_quotation.keys()):
        if this_quotation[stock_code]:
            #print(this_quotation[stock_code])
            if this_quotation[stock_code]['ask1']==0 and this_quotation[stock_code]['volume']==0:
                stop_stocks.append(stock_code)
            else:
                pass
    all_stocks = list(this_quotation.keys())
    exist_codes = tds.get_all_code(hist_dir='C:/hist/day/data/')
    all_codes = list(set(all_stocks).intersection(set(exist_codes)))
    if except_stocks:
        all_codes = list(set(all_codes).difference(set(except_stocks)))
    stop_stocks = list(set(stop_stocks).intersection(set(exist_codes)))
    #print('stop_stocks=', stop_stocks)
    #print(len(stop_stocks))
    #print('all_stocks=',all_stocks)
    #print(len(all_stocks))
    return stop_stocks,all_stocks

def get_exit_data(symbols,last_date_str):
    refer_index = ['sh','cyb']
    symbols = symbols +refer_index
    temp_datas = {}
    for symbol in symbols:
        dest_df=pds.pd.read_csv('C:/hist/day/data/%s.csv' % symbol)
        print(dest_df)
    #dest_df = get_raw_hist_df(code_str=symbol)
        if dest_df.empty:
            pass
        else:
            dest_df_last_date = dest_df.tail(1).iloc[0]['date']
            if dest_df_last_date==last_date_str:
                exit_price = dest_df.tail(3)
    return

#get_exit_data(symbols=['000029'],last_date_str='2016/08/23')
#get_stopped_stocks()

def back_test(k_num=0,given_codes=[],except_stocks=['000029'], type='stock', source='easyhistory'):
    """
高于三天收盘最大值时买入，低于三天最低价的最小值时卖出： 33策略
    """
    """
    :param k_num: string type or int type: mean counts of history if int type; mean start date of history if date str
    :param given_codes: str type, 
    :param except_stocks: list type, 
    :param type: str type, force update K data from YH
    :return: source: history data from web if 'easyhistory',  history data from YH if 'YH'
    """
    addition_name = ''
    if type == 'index':
        addition_name = type
    all_codes = []
    all_stop_codes = []
    all_stop_codes,all_stocks = get_stopped_stocks(given_codes,except_stocks)
    all_codes = list(set(all_stocks).difference(set(all_stop_codes)))
    if given_codes:
        all_codes = list(set(given_codes).difference(set(all_stop_codes)))
    else:
        pass
    if except_stocks:
        all_codes = list(set(all_codes).difference(set(except_stocks)))
    #all_codes = ['300128', '002288', '002156', '300126','300162','002717','002799','300515','300516','600519',
    #            '000418','002673','600060','600887','000810','600115','600567','600199','000596','000538','002274','600036','600030','601398']
    column_list = ['count', 'mean', 'std', 'max', 'min', '25%','50%','75%','cum_prf',
                   'fuli_prf','last_trade_date','last_trade_price','min_hold_count',
                   'max_hold_count','avrg_hold_count','this_hold_count','exit','enter',
                   'position','max_amount_rate','max_amount_distance','break_in', 
                   'break_in_count','break_in_date', 'break_in_distance','success_rate']
    all_result_df = tds.pd.DataFrame({}, columns=column_list)
    i=0
    trend_column_list = ['count', 'mean','chg_fuli', 'std', 'min', '25%', '50%', '75%', 'max', 'c_state',
                        'c_mean', 'pos_mean', 'ft_rate', 'presure', 'holding', 'close','cont_num','amount_rate','ma_amount_rate']
    all_trend_result_df = tds.pd.DataFrame({}, columns=trend_column_list)
    all_temp_hist_df = tds.pd.DataFrame({}, columns=[])
    ma_num = 20
    for stock_symbol in all_codes:
        if stock_symbol=='000029':
            continue
        print(i,stock_symbol)
        s_stock=tds.Stockhistory(stock_symbol,'D',test_num=k_num,source=source)
        if True:
        #try:
            result_df = s_stock.form_temp_df(stock_symbol)
            test_result = s_stock.regression_test()
            recent_trend = s_stock.get_recent_trend(num=ma_num,column='close')
            temp_hist_df = s_stock.temp_hist_df.set_index('date')
            #temp_hist_df.to_csv('C:/hist/day/temp/%s.csv' % stock_symbol)
            temp_hist_df_tail = temp_hist_df.tail(1)
            temp_hist_df_tail['code'] = stock_symbol
            all_temp_hist_df= all_temp_hist_df.append(temp_hist_df_tail)
            #print(test_result)
            #print(recent_trend)
            i = i+1
            if test_result.empty:
                pass
            else: 
                test_result_df = tds.pd.DataFrame(test_result.to_dict(), columns=column_list, index=[stock_symbol])
                all_result_df = all_result_df.append(test_result_df,ignore_index=False)
            if recent_trend.empty:
                pass
            else:
                trend_result_df = tds.pd.DataFrame(recent_trend.to_dict(), columns=trend_column_list, index=[stock_symbol])
                all_trend_result_df = all_trend_result_df.append(trend_result_df,ignore_index=False)
        #except:
        #    print('Regression test exception for stock: %s' % stock_symbol)
        
        
    #print(result_df.tail(20))
    #all_result_df = all_result_df.sort_index(axis=0, by='sum', ascending=False)
    
    all_result_df = all_result_df.sort_values(axis=0, by='cum_prf', ascending=False)
    all_trend_result_df = all_trend_result_df.sort_values(axis=0, by='chg_fuli', ascending=False)
    result_summary = all_result_df.describe()
    stock_basic_df=ts.get_stock_basics()
    basic_code = stock_basic_df['name'].to_dict()
    basic_code_keys = basic_code.keys()
    result_codes = all_result_df.index.values.tolist()
    result_codes_dict = {}
    on_trade_dict = {}
    valid_dict = {}
    for code in result_codes:
        if code in basic_code_keys:
            result_codes_dict[code] = basic_code[code]
        else:
            result_codes_dict[code] = 'NA'
        if code in all_stop_codes:
            on_trade_dict[code] = 1
        else:
            on_trade_dict[code] = 0
        if code in except_stocks:
            valid_dict[code] = 1
        else:
            valid_dict[code] = 0
    #print(result_codes_dict)
    #print(tds.pd.DataFrame(result_codes_dict, columns=['name'], index=list(result_codes_dict.keys())))
    #all_result_df['name'] = result_codes_dict
    all_result_df['name'] = tds.Series(result_codes_dict,index=all_result_df.index)
    all_trend_result_df['name'] = tds.Series(result_codes_dict,index=all_trend_result_df.index)
    all_result_df['stopped'] = tds.Series(on_trade_dict,index=all_result_df.index)
    all_trend_result_df['stopped'] = tds.Series(on_trade_dict,index=all_trend_result_df.index)
    all_result_df['invalid'] = tds.Series(valid_dict, index=all_result_df.index)
    all_trend_result_df['invalid'] = tds.Series(valid_dict, index=all_trend_result_df.index)
    all_result_df['max_r'] = all_result_df['max']/all_result_df['cum_prf']
    ma_c_name = '%s日趋势数' % ma_num
    trend_column_chiness = {'count':ma_c_name, 'mean': '平均涨幅','chg_fuli': '复利涨幅', 'std': '标准差', 'min': '最小涨幅', '25%': '25%', '50%': '50%', '75%': '75%', 'max': '最大涨幅', 'c_state': '收盘价状态',
                        'c_mean': '平均收盘价', 'pos_mean': '平均仓位', 'ft_rate': '低点反弹率', 'presure': '压力', 'holding': '支撑', 'close': '收盘价','cont_num': '连涨天数', 'name': '名字', 'stopped': '停牌','invalid': '除外',
                        'amount_rate':'量比','ma_amount_rate':'短长量比'}
    print(all_trend_result_df)
    all_trend_result_df_chinese = all_trend_result_df.rename(index=str, columns=trend_column_chiness)
    print(all_result_df)
    print(all_result_df.describe())
    if isinstance(k_num, str):
        k_num = k_num.replace('/','').replace('-','')
    latest_date_str = pds.tt.get_latest_trade_date(date_format='%Y/%m/%d')
    latest_date_str = latest_date_str.replace('/','').replace('-','')
    #print('latest_date_str=',latest_date_str)
    all_result_df.to_csv('./temp/regression_test_' + addition_name +'%s.csv' % latest_date_str)
    if all_result_df.empty:
        pass
    else:
        consider_df = all_result_df[(all_result_df['max_amount_rate']>2.0) & (all_result_df['position']>0.35) & (all_result_df['stopped']==0) & (all_result_df['invalid']==0)]# & (all_result_df['last_trade_price'] ==0)]
        consider_df.to_csv('./temp/consider_' + addition_name +'%s.csv' % k_num )
        
        active_df = all_result_df[(all_result_df['max_r']<0.4)  & (all_result_df['name']!='NA') & # (all_result_df['min']>-0.08)  & (all_result_df['position']>0.35) &
                                  (all_result_df['max']>(3.9 *all_result_df['min'].abs())) & (all_result_df['invalid']==0) &(all_result_df['stopped']==0)]
        active_df['active_score'] = active_df['fuli_prf']/active_df['max_r']/active_df['std']*active_df['fuli_prf']/active_df['cum_prf']
        active_df = active_df.sort_values(axis=0, by='active_score', ascending=False)
        active_df.to_csv('./temp/active_' + addition_name +'%s.csv' % k_num )
        
        tupo_df = all_result_df[(all_result_df['break_in_distance']!=0) &(all_result_df['break_in_distance']<=20) & 
                                (all_result_df['position']>0.35) & (all_result_df['stopped']==0) & 
                                (all_result_df['invalid']==0) & (all_result_df['name']!='NA') & (all_result_df['last_trade_price']!=0)]# & (all_result_df['last_trade_price'] ==0)]
        tupo_df.to_csv('./temp/tupo_' + addition_name +'%s.csv' % latest_date_str )
        
    result_summary.to_csv('./temp/result_summary_' + addition_name +'%s.csv' % k_num )
    all_trend_result_df_chinese.to_csv('./temp/trend_result_%s' % ma_num + addition_name +'%s.csv' % latest_date_str)
    if not all_temp_hist_df.empty:
        all_temp_hist_df = all_temp_hist_df.set_index('code')
        all_temp_hist_df.to_csv('./temp/all_temp_' + addition_name +'%s.csv' % latest_date_str )
        reverse_df = all_temp_hist_df[(all_temp_hist_df['reverse']>0) & 
                                (all_temp_hist_df['position']>0.35)]#
        reverse_df.to_csv('./temp/reverse_df_' + addition_name +'%s.csv' % latest_date_str )
    
    return all_result_df


back_test(k_num='2015/08/30',given_codes=['000060','002494'],except_stocks=['000029'], type='stock', source='YH')