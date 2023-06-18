from django.shortcuts import render
from django.http import JsonResponse
import pandas as pd
from django.views.decorators.csrf import csrf_exempt


def home(request):
    return render(request, 'app_top_keywords/home.html')


# read df
df_topkey = pd.read_csv('app_top_keywords/dataset/bnext_top_keywords.csv', sep=',')

# prepare data
data = {}
for idx, row in df_topkey.iterrows():
    data[row['category']] = eval(row['top_keys'])

# We don't use it anymore, so delete it to save memory.
del df_topkey


@csrf_exempt
def api_get_cate_topword(request):
    cate = request.POST.get('news_category')
    topk = request.POST.get('topk')
    topk = int(topk)
    print(cate, topk)

    response_data = get_category_topword(cate, topk)

    response = {'data': response_data}

    print(response)
    return JsonResponse(response, content_type='application/json')


def get_category_topword(cate, topk=10):
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


print("app_top_keywords--熱門關鍵詞分析--載入成功!")
