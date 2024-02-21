from django.shortcuts import render,redirect
from django.http import HttpResponse
from userapp.models import *
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from ast import While
import time
from yahoo_fin import stock_info as si
import pandas as pd
from django.forms.models import model_to_dict
import requests


def index(request):
    return render(request,'home.html')

def unique(all):
    #returns a dict with unique stock symbol and their value set to 0
    dic = {}
    for name, stocks in all.items():
        for stock, price in stocks.items():
                if stock not in dic.keys():
                    dic[stock] = [0,0]
    return dic

def updateprices(dic):
    count = 0
    flag = 0
    key1 = 'MT3MM1LR97FPMG0I'
    key2 = 'W5TIYAA37K16PDOI'
    key3 = '1MD1ELEQ4CWDKGNS'
    key = key1
    for stock, price in dic.items():
        if count != 0 and count%4 == 0 and flag == 0:
            key = key2
            flag = 1
        if count != 0 and count%4 == 0 and flag == 1:
            key = key1
            flag = 2
        if count != 0 and count%4 == 0 and flag == 2:
            key = key3
            flag = 0
            time.sleep(60)
        symbol = stock
        url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={key}'
        response = requests.get(url)
        data = response.json()
        data = dict(data)
        price = "$"+str(data['Global Quote']['05. price'])
        change = str(data['Global Quote']['10. change percent'])
        dic[stock] = [price,change]
        count = count + 1
    return dic

def put(unique, all):
    for name, stocks in all.items():
        for stock, prices in stocks.items():
            for key, value in unique.items():
                if key == stock:
                    stocks[stock] = value
    return all

def updatestocks(old,new):
    for key, value in old.items():
        for newkey, newval in new.items():
            if key == newkey:
                old[key] = newval
    return old

def dict_to_str(dic):
    string = ""
    for key, value in dic.items():
        string = string + ";" + str(key)
        for val in value:
            string = string  + "," + str(val)
    return string

    
def updateusers(all):
    result = " enterer updateusers"
    for obj in stock_picks.objects.all():
        for name, newstocks in all.items():
            result = result + " ** " + str(name) + " <->" + str(obj.name)
            if obj.name == name:
                result = result + "\n\n>> found" + str(obj.name)
                oldstring = obj.symbols
                result = result + " with oldstring: " + oldstring
                oldstocks = str_to_dict(oldstring)
                newstocks = updatestocks(oldstocks,newstocks)
                newstring = dict_to_str(newstocks)
                result = result + " -> converted to: " + newstring
                obj.symbols = newstring
                obj.save()
    return result

@login_required(login_url='log_in')
def users(request):
    if request.user.is_superuser:
        all = {}
        for obj in stock_picks.objects.all():
            info = model_to_dict(obj)
            name = obj.name
            stocks = info['symbols']
            set = str_to_dict(stocks)
            all[name] = set
        uniqueD = unique(all) 
        if request.method == "POST":
            uniqueD = updateprices(uniqueD)
            all = put(uniqueD,all)
        result = updateusers(all)
        return render(request, 'users.html', {'all':all, 'unique':uniqueD, 'result':result})
    else:
        return HttpResponse('''<html><body style="text-align:center; background-color:#17252A">
        <h3 style="color:white; font-family:system-ui; text-decorations: none;"><br><br>
        This page is accessible only to staff.</h3></body></html>''')
        
def str_to_dict(stocks):
    stocks = stocks.split(";")
    set = {}
    for x in range(len(stocks)):       
        stock = stocks[x].split(",")
        if stock[0] != "":
            set[stock[0]] = [stock[1],stock[2]]
    return set

@login_required(login_url='log_in')
def stocks(request):
    stock_picks_list = stock_picks.objects.all().filter(name=request.user.id)
    #the function above returned a query set thus we need to iterate it
    for stock_pick in stock_picks_list:
        info = model_to_dict(stock_pick)
        #model_to_dict returns dictionary form of the object

    stocks = info['symbols']
    set = str_to_dict(stocks)

    return render(request, 'stocks.html', {'set':set})

def updatesingleprice(request,symbol):
    key = 'MT3MM1LR97FPMG0I'
    url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={key}'
    response = requests.get(url)
    data = response.json()
    data = dict(data)
    x = list(data.keys())
    if(x[0] == 'Global Quote'):
        dic = {}
        price = "$"+str(data['Global Quote']['05. price'])
        change = str(data['Global Quote']['10. change percent'])
        dic[symbol] = [price,change]
        return dic
    else:
        return False

@login_required(login_url='log_in')
def market(request):
    if request.method == "POST":
        sym = request.POST['sym'].upper()
        tickers = pd.DataFrame({"tickers": si.tickers_sp500()})
        if sym in tickers["tickers"].values:
            dic = { sym: [0,0] }
            dic = updatesingleprice(request,sym)
            if(dic != False):
                string = dict_to_str(dic)
                for obj in stock_picks.objects.filter(name=request.user.id):
                    if sym not in obj.symbols:
                        obj.symbols = obj.symbols + string
                        obj.save()
                        messages.success(request,sym+" is a valid ticker symbol and is added to your stocklist.")
                    else:
                        messages.error(request,sym+" is already present in your stocklist")
            else:
                messages.error(request,"You have exceeded the limit of adding 5 stocks per minute. Please try again after another minute.")
        else:
            messages.error(request,sym+" is a an invalid ticker symbol.")
    return render(request,'market.html')

@login_required(login_url='log_in')
def profile(request):
    return render(request,'profile.html')

@login_required(login_url='log_in')
def editProfile(request):
    if request.method=='POST':
        name = request.POST['name']
        email = request.POST['email']
        password = request.POST['password']
        request.user.username = email
        request.user.email = email
        request.user.set_password(password)
        name = name.split(' ')
        request.user.first_name=name[0].strip()
        request.user.last_name=name[1].strip()
        request.user.save()
        msg = "Profile Updated Successfully"
    return render(request,'profile.html',{'msg':msg})

@login_required(login_url='log_in')
def contact(request):
    return render(request,'contact.html')

def log_in(request):
    if request.method == "POST":
        username = request.POST['email']
        password = request.POST['password']
        user = authenticate(request,username = username,password = password)
        if user is not None:
            login(request,user)
            request.session['username'] = username
            return redirect('stocks')
        else:
            messages.error(request,'Invalid credentials.')
    return render(request,'log_in.html')

def signup(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        if(not name or not email or not password ):
            messages.error(request, 'Fill all the fields')
        elif(name.startswith(('0','1','2','3','4','5','6','7','8','9'))):
            messages.error(request, 'Your username should not start with a number.')
        elif(len(password)<8):
            messages.error(request, 'Password should contain 8 or more characters.')
        else:
            try:
                user = User.objects.create(username = email,email = email)
            except:
                messages.error(request,'A user with this profile already exists.')
            else:
                user.set_password(password)
                name = name.split(' ')
                user.first_name=name[0].strip()
                user.last_name=name[1].strip()
                user.save()
                messages.success(request,'Signup successful.')
                setup = stock_picks(name = User.objects.get(username = email))
                setup.save()
                time.sleep(1.5)
                return redirect('log_in')
            #return redirect('login')
        #messages.info(request, '')
        #messages.warning(request, '')
        #messages.error(request, '')
    return render(request,'signup.html')

def feedback(request):
    return HttpResponse('''<body style="background-color:black"><h4 style="color:white">Feedback Page<h4></body>''')

@login_required(login_url='log_in')
def main(request):
    return render(request,'stocks.html')

def log_out(request):
    try:
        logout(request)
        del request.session['username']
    except:
        pass
    return redirect('home')