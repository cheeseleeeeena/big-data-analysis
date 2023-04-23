from django.shortcuts import render
from django.http import JsonResponse
import pandas as pd
from django.views.decorators.csrf import csrf_exempt


def home(request):
    return render(request, 'app_top_keyword_horoscope/home.html')


# CREATE DATAFRAME FROM CSV
df_topkey = pd.read_csv('app_top_keyword_horoscope/dataset/horoscope_topkey.csv', sep='|')

# EXTRACT DATA FROM DATAFRAME
data = {}
for idx, yearly_topkeys in df_topkey.iterrows():
    data[yearly_topkeys['horoscope']] = eval(yearly_topkeys['top_keys'])

# DELETE DATAFRAME
del df_topkey

'''
horoscopes = ['水瓶座', '雙魚座', '牡羊座', '金牛座', '雙子座', '巨蟹座', '獅子座', '處女座', '天秤座', '天蠍座',
              '射手座', '摩羯座']
years = ['2021', '2022']
months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
idx_to_horoscope = {str(i): item for i, item in enumerate(horoscopes)}
idx_to_year = {str(i): item for i, item in enumerate(years)}
idx_to_month = {str(i): item for i, item in enumerate(months)}
'''

@csrf_exempt
def api_get_topword(request):
    horoscope = request.POST.get('horoscope')
    year = request.POST.get('year')
    month = request.POST.get('month')
    topk = int(request.POST.get('topk'))
    print(horoscope, year, month, topk)

    response_data = get_horoscope_topword(horoscope, year, month, topk)
    response = {'data': response_data}
    print(response)
    return JsonResponse(response)


def get_horoscope_topword(horoscope, year, month, topk=15):
    wf_pairs = data[horoscope][year][month][0:topk]

    if not wf_pairs:
        return []

    words = [w for w, f in wf_pairs]
    freqs = [f for w, f in wf_pairs]

    # Prepare cloud chart data
    # the minimum and maximum frequency of top words
    min_ = wf_pairs[-1][1]  # the last line is smaller
    max_ = wf_pairs[0][1]  # the first frequency value is larger

    textSizeMin = 10
    textSizeMax = 90

    if (min_ != max_):
        max_min_range = max_ - min_

    else:
        max_min_range = len(wf_pairs)
        min_ = min_ - 1

    # cloud chart data
    # using proportional scaling
    cloud_data = [{'text': w, 'size': int(textSizeMin + (f - min_) / max_min_range * (textSizeMax - textSizeMin))} for
                  w, f in wf_pairs]

    response_data = {
        "wf_pairs": wf_pairs,
        "data_barchart": {
            "category": month,
            "labels": words,
            "values": freqs
        },
        "data_cloud": cloud_data}
    return response_data


print("app_top_keyword_horoscope--熱門關鍵字載入成功!")
