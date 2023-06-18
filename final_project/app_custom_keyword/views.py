from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

from datetime import datetime, timedelta
import pandas as pd
import re
from collections import Counter


def load_df_data():
    global df
    df = pd.read_csv('app_custom_keyword/dataset/bnext_preprocessed_665.csv', sep=',')


load_df_data()
news_categories = ['5G通訊', 'AI與大數據', '物聯網', '區塊鏈', '半導體與電子產業', '資訊安全', '雲端運算', '全部']


def home(request):
    return render(request, 'app_custom_keyword/home_test.html')


@csrf_exempt
def api_get_top_userkey(request):
    userkey = request.POST.get('userkey')
    cate = request.POST.get('cate')
    cond = request.POST.get('cond')
    weeks = int(request.POST.get('weeks'))
    key = userkey.split()

    global df_query

    # filter dataframe
    df_query = filter_data_v2(key, cond, cate, weeks)
    print(len(df_query))

    # get line chart data

    key_time_freq = get_keyword_time_based_freq(df_query)
    print(key_time_freq)

    # get frequency and occurrence data
    kw_freq, kw_occurrence = count_keyword(df_query, key)
    print(kw_freq[cate], kw_occurrence[cate])

    if len(df_query) != 0:  # df_query is not empty
        newslinks = get_title_link_topk(df_query, k=30)
        related_words, clouddata = get_related_word_clouddata(df_query)
        same_paragraph = get_same_para(df_query, key, cond, k=30)  # multiple keywords
        num_articles = len(df_query)  # total number of articles (stories, items)
    else:
        newslinks = []
        related_words = []
        same_paragraph = []
        clouddata = []
        num_articles = 0


    # sentiment
    sentiCount, sentiPercnt = get_article_sentiment(df_query)

    if weeks <= 4:
        freq_type = 'D'
    else:
        freq_type = 'W'

    line_data_pos = get_daily_basis_sentiment_count(df_query, sentiment_type='pos', freq_type=freq_type)
    line_data_neg = get_daily_basis_sentiment_count(df_query, sentiment_type='neg', freq_type=freq_type)


    response = {
        'kw_freq': kw_freq[cate],
        'kw_occurrence': kw_occurrence[cate],
        'key_time_freq': key_time_freq,
        'newslinks': newslinks,
        'related_words': related_words,
        'same_paragraph': same_paragraph,
        'clouddata': clouddata,
        'num_articles': num_articles,
        'sentiCount': sentiCount,
        'data_pos': line_data_pos,
        'data_neg': line_data_neg,
    }
    return JsonResponse(response)


def filter_data(user_keywords, cond, cate, weeks):
    # end date: the date of the latest record of news
    end_date = df.date.max()

    # start date
    start_date_delta = (datetime.strptime(end_date, '%Y-%m-%d').date() - timedelta(weeks=weeks)).strftime('%Y-%m-%d')
    start_date_min = df.date.min()

    start_date = max(start_date_delta, start_date_min)

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
        condition = condition & df.content.apply(lambda text: all((qk in text) for qk in user_keywords))  # 寫法:all()
    elif (cond == 'or'):
        # query keywords condition使用者輸入關鍵字條件
        condition = condition & df.content.apply(lambda text: any((qk in text) for qk in user_keywords))  # 寫法:any()
    df_query = df[condition]

    return df_query


def filter_data_v2(user_keywords, cond, cate, weeks):
    if (cate != "全部"):
        df_filtered_cate = df[df.category == cate]
    else:
        df_filtered_cate = df

    # end date: the date of the latest record of news
    end_date = df_filtered_cate.date.max()

    # start date
    start_date_delta = (datetime.strptime(end_date, '%Y-%m-%d').date() - timedelta(weeks=weeks)).strftime('%Y-%m-%d')
    start_date_min = df_filtered_cate.date.min()

    start_date = max(start_date_delta, start_date_min)

    # (1) proceed filtering: a duration of a period of time
    period_condition = (df_filtered_cate.date >= start_date) & (df_filtered_cate.date <= end_date)

    if (cond == 'and'):
        # query keywords condition使用者輸入關鍵字條件and
        condition = period_condition & df_filtered_cate.content.apply(
            lambda text: all((qk in text) for qk in user_keywords))  # 寫法:all()
    elif (cond == 'or'):
        # query keywords condition使用者輸入關鍵字條件
        condition = period_condition & df_filtered_cate.content.apply(
            lambda text: any((qk in text) for qk in user_keywords))  # 寫法:any()
    df_query = df_filtered_cate[condition]

    return df_query


def count_keyword(query_df, user_keywords):
    cate_occurrence = {}
    cate_freq = {}

    for cate in news_categories:
        cate_occurrence[cate] = 0
        cate_freq[cate] = 0

    for idx, row in query_df.iterrows():
        # count number of news
        cate_occurrence[row.category] += 1
        cate_occurrence['全部'] += 1

        tokens = eval(row.tokens_v2)
        freq = len([word for word in tokens if (word in user_keywords)])
        cate_freq[row.category] += freq
        cate_freq['全部'] += freq

    return cate_freq, cate_occurrence


def get_keyword_time_based_freq(dataframe):

    date_samples = dataframe.date

    query_freq = pd.DataFrame({'date_index': pd.to_datetime(date_samples), 'freq': [1 for _ in range(len(dataframe))]})
    data = query_freq.groupby(pd.Grouper(key='date_index', freq='D')).sum()
    time_data = []
    for i, idx in enumerate(data.index):
        row = {'x': idx.strftime('%Y-%m-%d'), 'y': int(data.iloc[i].freq)}
        time_data.append(row)

    return time_data


# get titles and links from k pieces of news 
def get_title_link_topk(df_query, k=20):
    items = []
    for i in range(len(df_query[0:k])):  # show only k news
        category = df_query.iloc[i]['category']
        title = df_query.iloc[i]['title']
        link = df_query.iloc[i]['link']

        item_info = {
            'category': category,
            'title': title,
            'link': link,
        }

        items.append(item_info)
    return items


def get_related_word_clouddata(df_query):
    # wf_pairs = get_related_words(df_query)
    # prepare wf pairs
    counter = Counter()
    for idx in range(len(df_query)):
        pair_dict = dict(eval(df_query.iloc[idx].top_key_freq))
        counter += Counter(pair_dict)
    wf_pairs = counter.most_common(10)  # return list format

    # cloud chart data
    # the minimum and maximum frequency of top words
    min_ = wf_pairs[-1][1]  # the last line is smaller
    max_ = wf_pairs[0][1]
    # text size based on the value of word frequency for drawing cloud chart
    textSizeMin = 20
    textSizeMax = 120
    # Scaling frequency value into an interval of from 20 to 120.
    clouddata = [{'text': w, 'size': int(textSizeMin + (f - min_) / (max_ - min_) * (textSizeMax - textSizeMin))}
                 for w, f in wf_pairs]

    return wf_pairs, clouddata


def cut_paragraph(text):
    text = re.sub('([。！？\?])([^”’』」])', r"\1\n\2", text)  # 单字符断句符
    text = re.sub('(\.{6})([^”’』」])', r"\1\n\2", text)  # 英文省略号
    text = re.sub('(\…{2})([^”’』」])', r"\1\n\2", text)  # 中文省略号
    text = re.sub('([。！？\?][”’』」])([^，。！？\?])', r'\1\n\2', text)
    # 如果雙引號前有終止符，那麼雙引號才是句子的終點，把分句符\n放到雙引號後，注意前面的幾句都小心保留了雙引號
    text = text.rstrip()  # 段尾如果有多余的\n就去掉它
    # 分号忽略不计，破折号、英文双引号等同样忽略
    return text.split("\n")


def get_same_para(df_query, user_keywords, cond, k=30):
    same_para = []
    for text in df_query.content:
        # print(text)
        paragraphs = cut_paragraph(text)
        for para in paragraphs:
            # 判斷每個段落文字是否包含該關鍵字，and or分開判斷
            if cond == 'and':
                if all([kw in para for kw in user_keywords]):
                    same_para.append(para)  # 符合條件的段落para保存起來
            elif cond == 'or':
                if any([kw in para for kw in user_keywords]):
                    same_para.append(para)  # 符合條件的段落para保存起來
    return same_para[0:k]


def get_article_sentiment(df_query):
    sentiCount = {'Positive': 0, 'Negative': 0, 'Neutral': 0}
    sentiPercnt = {'Positive': 0, 'Negative': 0, 'Neutral': 0}
    numberOfArticle = len(df_query)
    for senti in df_query.bert_sentiment:
        # determine sentimental polarity
        if float(senti) >= 0.75:
            sentiCount['Positive'] += 1
        elif float(senti) <= 0.5:
            sentiCount['Negative'] += 1
        else:
            sentiCount['Neutral'] += 1
    for polar in sentiCount:
        try:
            sentiPercnt[polar] = int(sentiCount[polar] / numberOfArticle * 100)
        except:
            sentiPercnt[polar] = 0  # 若分母 numberOfArticle=0會報錯
    return sentiCount, sentiPercnt


def get_daily_basis_sentiment_count(df_query, sentiment_type='pos', freq_type='D'):
    if sentiment_type == 'pos':
        lambda_function = lambda senti: 1 if senti >= 0.75 else 0  # 大於0.6為正向
    elif sentiment_type == 'neg':
        lambda_function = lambda senti: 1 if senti <= 0.5 else 0  # 小於0.4為負向
    elif sentiment_type == 'neutral':
        lambda_function = lambda senti: 1 if senti > 0.5 & senti < 0.75 else 0  # 介於中間為中立
    else:
        return None

    freq_df = pd.DataFrame({'date_index': pd.to_datetime(df_query.date),
                            'frequency': [lambda_function(senti) for senti in df_query.bert_sentiment]})
    # Group rows by the date to the daily number of articles. 加總合併同一天新聞，篇數就被計算好了
    freq_df_group = freq_df.groupby(pd.Grouper(key='date_index', freq=freq_type)).sum()

    freq_df_group.reset_index(inplace=True)

    # x,y，用於畫趨勢線圖
    xy_line_data = [{'x': date.strftime('%Y-%m-%d'), 'y': freq} for date, freq in
                    zip(freq_df_group.date_index, freq_df_group.frequency)]
    return xy_line_data

"""
def filter_df_via_content(query_keywords, cond, cate, weeks):
    # end date: the date of the latest record of news
    end_date = df.date.max()

    # start date
    start_date_delta = (datetime.strptime(end_date, '%Y-%m-%d').date() - timedelta(weeks=weeks)).strftime('%Y-%m-%d')
    start_date_min = df.date.min()

    start_date = max(start_date_delta, start_date_min)

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
        condition = condition & df.content.apply(lambda text: all((qk in text) for qk in query_keywords))  # 寫法:all()
    elif (cond == 'or'):
        # query keywords condition使用者輸入關鍵字條件
        condition = condition & df.content.apply(lambda text: any((qk in text) for qk in query_keywords))  # 寫法:any()
    df_query = df[condition]

    return df_query
"""

print("app_custom_keyword--自訂關鍵詞分析--載入成功!")
