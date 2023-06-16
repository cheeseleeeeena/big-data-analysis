from django.shortcuts import render
import pandas as pd
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def home(request):
    return render(request, 'app_top_corps/home.html')


# load data
def load_data_topPerson():
    # read df
    df_topPerson = pd.read_csv(
        'app_top_corps/dataset/news_top_person_by_category_via_ner.csv')
    # refresh data
    global data
    
    data = {}
    for idx, row in df_topPerson.iterrows():
        data[row['category']] = eval(row['top_keys'])


# Load data first when starting server.
load_data_topPerson()

# csrf_exempt is used for POST
# 單獨指定這一支程式忽略csrf驗證
@csrf_exempt
def api_get_topPerson(request):

    cate = request.POST.get('news_category')
    topk = request.POST.get('topk')
    topk = int(topk)
    #print(cate, topk)

    chart_data, wf_pairs = get_category_topPerson(cate, topk)
    clouddata = []
    for item in wf_pairs:
        clouddata.append({
        'text': item[0],
        'size': item[1]
    })
    # print(chart_data)
    response = {'chart_data':  chart_data,
                'wf_pairs': wf_pairs,
                'data_cloud': clouddata,
                }
    return JsonResponse(response)


def get_category_topPerson(cate, topk):
    wf_pairs = data[cate][0:topk]
    words = [w for w, f in wf_pairs]
    freqs = [f for w, f in wf_pairs]
    chart_data = {
        "category": cate,
        "labels": words,
        "values": freqs}
    return chart_data, wf_pairs  # chart_data is for charting


print("app_top_corps--類別熱門人物載入成功!")
