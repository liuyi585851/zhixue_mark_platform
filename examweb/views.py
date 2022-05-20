from email import message
from django.http.response import HttpResponse
from django.shortcuts import redirect, render
from . import models
from .forms import UserForm,MarkForm,DevForm
from zhixuewang import login as zlogin
from .zhixue import ZhixueScoreApi
from .zhixue import get_personMap_by_name
import time
import pickle
from .models import Exams,Ukeys,Recodes,Permissions,TraceIds
import json
import os
import uuid
import sys

# Create your views here.

def check_admin(username):
    result = models.Users.objects.filter(username=username).extra(where=["status='admin'"]),
    if result.count() == 0:
        return False
    else:
        return True

def check_permission(username,permission):
    if Permissions.objects.filter(username=username).exists():
        perm = Permissions.objects.filter(username=username)
        perm = perm.values(permission)[0][permission]
        if perm == True:
            return True
        else:
            return False
    else:
        return False

def get_one_person_scores(scores, person_name):
    return [one_subject_scores.find(lambda t: t.person.name == person_name) for one_subject_scores in scores]

def login(request):
    try:
        callback = request.session.get('refer',None)
    except:
        callback="/index/"
    if callback == None:
        callback= "/index/"
    
    if request.session.get('is_login',None):
        return redirect('/index/')

    if request.method == "POST":
        login_form = UserForm(request.POST)
        message = "请检查填写的内容!"
        if login_form.is_valid():
            username = login_form.cleaned_data['username']
            password = login_form.cleaned_data['password']
            try:
                zinfo = zlogin(username,password)
                z_list = str(zinfo).split()
                zhixueScoreApi = ZhixueScoreApi(username, password)
                elist = zhixueScoreApi.get_exams()
                con = 1
                t = []
                for exam in elist:
                    t.append((exam.name, exam.name))
                    con = con + 1
                    print(exam.name)
                print(z_list)
                request.session['exam'] = t
                request.session['name'] = z_list[5]
                request.session['class'] = z_list[3]
                request.session['school'] = z_list[1]
                request.session['is_login'] = True
                request.session['username'] = username
                request.session['password'] = password
                request.session['is_admin'] = check_admin(username)
                return redirect(callback)
            except Exception as msg:
                traceid = tracerequest(username,password,msg)
                trace = "事件编号:" + traceid
                message = "用户名或密码不正确!"
        return render(request,'login.html',locals())
    login_form = UserForm()
    return render(request,'login.html',locals())

def index(request):
    if not request.session.get('is_login',None):
        return render(request,'index.html',locals())
    request.session['is_admin'] = check_admin(request.session.get('username',None))
    username = request.session.get('username',None)
    can_change=check_permission(username,'view_everyone')
    if request.method == "POST":
        login_form = MarkForm(request.session.get('exam',None), request.POST) # 这里不能传递request post进去
        if not can_change:
            login_form.fields['name'].initial = request.session.get('name',None)
        login_form.fields['name'].widget.attrs['readonly'] = not can_change
        message = "请检查填写的内容!"
        if login_form.is_valid():
            valid = False
            message = None
            name = login_form.cleaned_data['name']
            exam = login_form.cleaned_data['choice']
            username = request.session.get('username',None)
            password = request.session.get('password',None)
            if not can_change:
                if name != request.session.get('name',None):
                    alert = "您的账号仅允许查询本人成绩"
                    return render(request,'index.html',locals())
            zhixueScoreApi = ZhixueScoreApi(username,password)
            if Exams.objects.filter(examname=exam).exists():
                scores = pickle.load(open(os.path.join(os.path.abspath('.'),"exams",exam+'.pkl'),'rb'))
                catime = Exams.objects.filter(examname=exam)
                catime = catime.values('latest')[0]['latest']
                is_cache = True
            else:
                scores = zhixueScoreApi.get_scores(zhixueScoreApi.get_exams().find_by_name(exam))
                Exams.objects.create(examname=exam,latest=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
                fi = open(os.path.join(os.path.abspath('.'),"exams",exam+'.pkl'),'wb')
                pickle.dump(scores,fi)
                fi.close()
                is_cache = False
            mark = get_one_person_scores(scores,name)
            personScoreMap =get_personMap_by_name(scores)
            is_cross = mark[0].exam_extraRank.rank
            if name in personScoreMap:
                valid = True
            else:
                valid = False
            if valid:
                recoderequest(username,request.session.get('name',None),request.session.get('class',None),name,exam,request.session.get('school',None))
                return render(request,'mark.html',locals())
            else:
                alert = "没有姓名为 "+name+" 的考生"
                return render(request,'index.html',locals())
        return render(request,'index.html',locals())
    login_form = MarkForm(choices=request.session.get('exam',None))
    if not can_change:
        login_form.fields['name'].initial = request.session.get('name',None)
    login_form.fields['name'].widget.attrs['readonly'] = not can_change
    return render(request,'index.html',locals())

def logout(request):
    if not request.session.get('is_login',None):
        return redirect("/index/")
    request.session.flush()
    return redirect("/index/")

def about(request):
    if request.session.get('is_login',None):
        request.session['is_admin'] = check_admin(request.session.get('username',None))
    request.session['refer'] = '/about/'
    return render(request,'about.html')

def admin(request):
    request.session['refer'] = '/admin/'
    if not request.session.get('is_login',None):
        return render(request,'admin.html')
    else:
        username = request.session.get('username',None)
        request.session['is_admin'] = check_admin(username)
        return render(request,'aaindex.html')

def aindex(request):
    return render(request,'aindex.html')

def keygen(request):
    if request.method == 'GET':
        return redirect('/index/')
    examname = request.POST.get('examname',0)
    uid = str(uuid.uuid4())
    key = ''.join(uid.split('-'))
    if Ukeys.objects.filter(examname=examname).exists():
        keys = Ukeys.objects.filter(examname=examname).order_by('-id')
        exptime = int(keys.values('expiredtime')[0]['expiredtime'])
        gtime = int(keys.values('gentime')[0]['gentime'])
        gentime = int(time.time())
        if exptime > gentime or gentime - gtime < 300:
            key = keys.values('key')[0]['key']
        else:
            gentime = int(time.time())
            Ukeys.objects.create(examname=examname,key=key,gentime=gentime,expiredtime=(gentime+300))
    else:
        gentime = int(time.time())
        Ukeys.objects.create(examname=examname,key=key,gentime=gentime,expiredtime=(gentime+300))
    return_param = {}
    return_param['status'] = 200
    return_param['key'] = key
    return HttpResponse(json.dumps(return_param))

def update(request):
    key = request.GET.get('key',0)
    tkey = Ukeys.objects.filter(key=key)
    if key==0 or not tkey.exists():
        return redirect('/index/')
    exptime = int(tkey.values('expiredtime')[0]['expiredtime'])
    ntime = int(time.time())
    if ntime > exptime or exptime == str(0):
        is_ok = False
        message = "您的操作超时或系统已在5分钟内执行过缓存更新，请耐心等待"
    else:
        username = request.session.get('username',None)
        password = request.session.get('password',None)
        zhixueScoreApi = ZhixueScoreApi(username,password)
        exam = tkey.values('examname')[0]['examname']
        scores = zhixueScoreApi.get_scores(zhixueScoreApi.get_exams().find_by_name(exam))
        Exams.objects.filter(examname=exam).update(latest=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        fi = open(os.path.join(os.path.abspath('.'),"exams",exam+'.pkl'),'wb')
        pickle.dump(scores,fi)
        fi.close()
        tkey.update(expiredtime='0')
        is_ok = True
        examname = tkey.values('examname')[0]['examname']
    return render(request,'update.html',locals())

def question(request):
    return render(request,'question.html')

def recoderequest(username,name,classname,cname,exam,school):
    uid = str(uuid.uuid4())
    tid = ''.join(uid.split('-'))
    Recodes.objects.create(traceid=tid,username=username,school=school,name=name,classname=classname,cname=cname,exam=exam,time=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    return tid

def tracerequest(username,password,msg):
    uid = str(uuid.uuid4())
    tid = ''.join(uid.split('-'))
    TraceIds.objects.create(traceid=tid,username=username,password=password,time=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),message=msg)
    return tid

def page_error(request):
    error = sys.exc_info()
    context = {
        'error':error
    }
    return render(request,'500.html',context=context)