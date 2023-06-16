from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

from datetime import datetime, timedelta
import pandas as pd
import math
import re
from collections import Counter

def load_df_data():
    global  df
    df = pd.read_csv('app_custom_keyword/dataset/cna_dataset_processed.csv', sep='|')

load_df_data() 

def home(request):
    return render(request, 'app_custom_keyword/home.html')

@csrf_exempt
def api_get_top_userkey(request):
    userkey = request.POST.get('userkey')
    cate = request.POST.get('cate')
    cond = request.POST.get('cond')
    weeks = int(request.POST.get('weeks'))
    key = userkey.split()
    
    global  df_query 

    # filter dataframe
    df_query = filter_dataFrame(key, cond, cate,weeks)
    #print(len(df_query))

    # get line chart data
    key_time_freq = get_keyword_time_based_freq(df_query)

    if len(df_query) != 0:  # df_query is not empty
        newslinks = get_title_link_topk(df_query, k=25)
        related_words, clouddata = get_related_word_clouddata(df_query)
        same_paragraph = get_same_para(df_query, key, cond, k=30) # multiple keywords

    else:
        newslinks = []
        related_words = []
        same_paragraph = []
        clouddata = []


    # sentiment
    df_query = filter_df_via_content(key, cond, cate, weeks)
    
    sentiCount, sentiPercnt = get_article_sentiment(df_query)

    if weeks <= 4:
        freq_type = 'D'
    else:
        freq_type = 'W'

    line_data_pos = get_daily_basis_sentiment_count(df_query, sentiment_type='pos', freq_type=freq_type)
    line_data_neg = get_daily_basis_sentiment_count(df_query, sentiment_type='neg', freq_type=freq_type)

    response = {
        'key_time_freq': key_time_freq, 
        'newslinks': newslinks,
        'related_words': related_words,
        'same_paragraph': same_paragraph,
        'clouddata':clouddata,
        'sentiCount': sentiCount,
        'data_pos':line_data_pos,
        'data_neg':line_data_neg,
    }

    return JsonResponse(response)

def filter_dataFrame(user_keywords, cond, cate, weeks):

    # end date: the date of the latest record of news
    end_date = df.date.max()
    
    # start date
    start_date = (datetime.strptime(end_date, '%Y-%m-%d').date() - timedelta(weeks=weeks)).strftime('%Y-%m-%d')

    # proceed filtering
    if (cate == "全部") & (cond == 'and'):
        query_df = df[(df.date >= start_date) & (df.date <= end_date) 
            & df.tokens_v2.apply(lambda text: all((qk in text) for qk in user_keywords))]
    elif (cate == "全部") & (cond == 'or'):
        query_df = df[(df['date'] >= start_date) & (df['date'] <= end_date) 
            & df.tokens_v2.apply(lambda text: any((qk in text) for qk in user_keywords))]
    elif (cond == 'and'):
        query_df = df[(df.category == cate) 
            & (df.date >= start_date) & (df.date <= end_date) 
            & df.tokens_v2.apply(lambda text: all((qk in text) for qk in user_keywords))]
    elif (cond == 'or'):
        query_df = df[(df.category == cate) 
            & (df['date'] >= start_date) & (df['date'] <= end_date) 
            & df.tokens_v2.apply(lambda text: any((qk in text) for qk in user_keywords))]
    return query_df

news_categories = ['全部','政治', '科技', '運動', '證卷', '產經', '娛樂', '生活', '國際', '社會', '文化', '兩岸']

def count_keyword(query_df, user_keywords):
    cate_occurence={}
    cate_freq={}

    for cate in news_categories:
        cate_occurence[cate]=0
        cate_freq[cate]=0

    for idx, row in query_df.iterrows():
        # count number of news
        cate_occurence[row.category] += 1
        cate_occurence['全部'] += 1
        
        tokens = eval(row.tokens_v2)
        freq =  len([word for word in tokens if (word in user_keywords)])
        cate_freq[row.category] += freq
        cate_freq['全部'] += freq
        
    return cate_freq, cate_occurence

def get_keyword_time_based_freq(df_query):
    date_samples = df_query.date
    query_freq = pd.DataFrame({'date_index': pd.to_datetime(date_samples), 'freq': [1 for _ in range(len(df_query))]})
    data = query_freq.groupby(pd.Grouper(key='date_index', freq='D')).sum()
    time_data = []
    for i, idx in enumerate(data.index):
        row = {'x': idx.strftime('%Y-%m-%d'), 'y': int(data.iloc[i].freq)}
        time_data.append(row)
    return time_data

def filter_dataFrame_fullText(user_keywords, cond, cate, weeks):

    # end date: the date of the latest record of news
    end_date = df.date.max()

    # start date
    start_date = (datetime.strptime(end_date, '%Y-%m-%d').date() -
                  timedelta(weeks=weeks)).strftime('%Y-%m-%d')

    # (1) proceed filtering: a duration of a period of time
    # 期間條件
    period_condition = (df.date >= start_date) & (df.date <= end_date)

    # (2) proceed filtering: news category
    # 新聞類別條件
    if (cate == "全部"):
        condition = period_condition  # "全部"類別不必過濾新聞種類
    else:
        # category新聞類別條件
        condition = period_condition & (df.category == cate)

    # (3) proceed filtering: news category
    if (cond == 'and'):
        condition = condition & df.content.apply(lambda text: all(
            (qk in text) for qk in user_keywords))  # 寫法:all()
    elif (cond == 'or'):
        condition = condition & df.content.apply(lambda text: any(
            (qk in text) for qk in user_keywords))  # 寫法:any()
    # condiction is a list of True or False boolean value
    df_query = df[condition]

    return df_query


# get titles and links from k pieces of news 
def get_title_link_topk(df_query, k=25):
    items = []
    for i in range( len(df_query[0:k]) ): # show only 10 news
        category = df_query.iloc[i]['category']
        title = df_query.iloc[i]['title']
        link = df_query.iloc[i]['link']
        photo_link = df_query.iloc[i]['photo_link']

        if pd.isna(photo_link):
            photo_link=''
        
        item_info = {
            'category': category, 
            'title': title, 
            'link': link, 
            'photo_link': photo_link
        }

        items.append(item_info)
    return items 

def get_related_word_clouddata(df_query):

    # prepare wf pairs 
    counter=Counter()
    for idx in range(len(df_query)):
        pair_dict = dict(eval(df_query.iloc[idx].top_key_freq))
        counter += Counter(pair_dict)
    wf_pairs = counter.most_common(20) #return list format

    # cloud chart data
    min_ = wf_pairs[-1][1]  # the last line is smaller
    max_ = wf_pairs[0][1]

    textSizeMin = 20
    textSizeMax = 120

    clouddata = [{'text': w, 'size': int(textSizeMin + (f - min_) / (max_ - min_) * (textSizeMax - textSizeMin))}
                 for w, f in wf_pairs]

    return   wf_pairs, clouddata 


def cut_paragraph(text):
    paragraphs = text.split('。') 
    paragraphs = list(filter(None, paragraphs))
    return paragraphs


def get_same_para(df_query, user_keywords, cond, k=30):
    same_para = []
    for text in df_query.content:
        #print(text)
        paragraphs = cut_paragraph(text)
        for para in paragraphs:
            para += "。"
            if cond == 'and':
                if all([re.search(kw, para) for kw in user_keywords]):
                    same_para.append(para)
            elif cond == 'or':
                if any([re.search(kw, para) for kw in user_keywords]):
                    same_para.append(para)
    return same_para[0:k]


def get_article_sentiment(df_query):
    sentiCount = {'Positive': 0, 'Negative': 0, 'Neutral': 0}
    sentiPercnt = {'Positive': 0, 'Negative': 0, 'Neutral': 0}
    numberOfArticle = len(df_query)
    for senti in df_query.sentiment:
        # determine sentimental polarity
        if float(senti) >= 0.6:
            sentiCount['Positive'] += 1
        elif float(senti) <= 0.4:
            sentiCount['Negative'] += 1
        else:
            sentiCount['Neutral'] += 1
    for polar in sentiCount :
        try:
            sentiPercnt[polar]=int(sentiCount[polar]/numberOfArticle*100)
        except:
            sentiPercnt[polar] = 0 # 若分母 numberOfArticle=0會報錯
    return sentiCount, sentiPercnt


def get_daily_basis_sentiment_count(df_query, sentiment_type='pos', freq_type='D'):

    if sentiment_type == 'pos':
        lambda_function = lambda senti: 1 if senti >= 0.6 else 0 #大於0.6為正向 
    elif sentiment_type == 'neg':
        lambda_function = lambda senti: 1 if senti <= 0.4 else 0 #小於0.4為負向
    elif sentiment_type == 'neutral':
        lambda_function = lambda senti: 1 if senti > 0.4 & senti < 0.4 else 0 #介於中間為中立
    else:
        return None 
        
    freq_df = pd.DataFrame({'date_index': pd.to_datetime(df_query.date),
                             'frequency': [lambda_function(senti) for senti in df_query.sentiment]})
    # Group rows by the date to the daily number of articles. 加總合併同一天新聞，篇數就被計算好了
    freq_df_group = freq_df.groupby(pd.Grouper(key='date_index',freq=freq_type)).sum()
    
    freq_df_group.reset_index(inplace=True)
    
    # x,y，用於畫趨勢線圖
    xy_line_data = [{'x':date.strftime('%Y-%m-%d'),'y':freq} for date, freq in zip(freq_df_group.date_index,freq_df_group.frequency)]
    return xy_line_data

def filter_df_via_content(query_keywords, cond, cate, weeks):

    # end date: the date of the latest record of news
    end_date = df.date.max()
    
    # start date
    start_date_delta = (datetime.strptime(end_date, '%Y-%m-%d').date() - timedelta(weeks=weeks)).strftime('%Y-%m-%d')
    start_date_min = df.date.min()

    start_date = max(start_date_delta,   start_date_min)


    # (1) proceed filtering: a duration of a period of time
    period_condition = (df.date >= start_date) & (df.date <= end_date) 
    
    # (2) proceed filtering: news category
    if (cate == "全部"):
        condition = period_condition  # "全部"類別不必過濾新聞種類
    else:
        # 過濾category新聞類別條件
        condition = period_condition & (df.category == cate)

    if (cond == 'and'):
        # query keywords condition使用者輸入關鍵字條件and
        condition = condition & df.content.apply(lambda text: all((qk in text) for qk in query_keywords)) #寫法:all()
    elif (cond == 'or'):
        # query keywords condition使用者輸入關鍵字條件
        condition = condition & df.content.apply(lambda text: any((qk in text) for qk in query_keywords)) #寫法:any()
    df_query = df[condition]

    return df_query

print("app_custom_keyword was loaded!")
