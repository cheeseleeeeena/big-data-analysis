from django.shortcuts import render
import pandas as pd
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def home(request):
    return render(request, 'app_top_corps/home.html')


# load data
def load_data_topCorps():
    # read df
    df_topCorps = pd.read_csv(
        'app_top_corps/dataset/bnext_top_corporates.csv')
    # refresh data
    global data
    
    data = {}
    for idx, row in df_topCorps.iterrows():
        data[row['category']] = eval(row['top_corps'])


# Load data first when starting server.
load_data_topCorps()


@csrf_exempt
def api_get_topCorps(request):

    cate = request.POST.get('news_category')
    topk = request.POST.get('topk')
    topk = int(topk)

    response_data = get_category_topCorps(cate, topk)

    response = {'data': response_data}

    return JsonResponse(response, content_type='application/json')


def get_category_topCorps(cate, topk):
    wf_pairs = data[cate][0:topk]

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
            "category": cate,
            "labels": words,
            "values": freqs
        },
        "data_cloud": cloud_data}

    return response_data


print("app_top_corps--熱門科技公司分析--載入成功!")
