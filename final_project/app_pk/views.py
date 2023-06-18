from django.http import JsonResponse
import pandas as pd
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt


def load_data_pk(cate='產品', topk=3):

    if cate == '公司':
        df_data_pk = pd.read_csv('app_pk/dataset/pk_3c_corp.csv', sep='|')
    elif cate == '產品':
        df_data_pk = pd.read_csv('app_pk/dataset/pk_3c_prod.csv', sep='|')

    global data
    data = {}

    for k, v in zip(df_data_pk.name, df_data_pk.value):
        data[k] = eval(v)[0:topk]
    
    del df_data_pk


def home(request):
    return render(request, 'app_pk/home.html')


@csrf_exempt
def api_get_pk_data(request):
    cate = request.POST.get('cate')
    topk = request.POST.get('topk')
    topk = int(topk)

    load_data_pk(cate, topk)
    return JsonResponse(data)


print('app_pk--3C產業聲量大PK--載入成功!')
