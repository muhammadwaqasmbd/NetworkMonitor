import json
import re

from django.http import HttpResponsePermanentRedirect, HttpResponse
from django.shortcuts import render
import matplotlib.pyplot as plt
import io
import urllib, base64
import pandas as pd
import seaborn as sns
import datetime
import os
import numpy as np
from tempfile import NamedTemporaryFile
import shutil
import csv
from .forms import DeviceForm, TimeForm, HistoricForm, DeviceFilterForm


def home(request):
    print("In home")
    if request.method == 'POST':
        print("In 1st post")
        if request.POST and not request.is_ajax():
            print("In update device form")
            form = DeviceForm(request.POST)
            updateDevice(form)
    data = {}
    devices = []
    df = pd.read_csv("/home/muhammadwaqas/PycharmProjects/NetworkScanner/device/data/data.csv")
    if request.method == 'POST':
        print("In 2nd post")
        if request.POST and request.is_ajax():
            print("In time")
            form = TimeForm(request.POST)
            df = getLastMinutesRecords(df,form)
        else:
            df = getLastFiveMinutesRecords(df)
            devices = getLegendDevices(df)
    else:
        df = getLastFiveMinutesRecords(df)
        devices = getLegendDevices(df)

    uri = getLivePlot(df)
    data['plot'] = uri
    data['devices'] = devices
    print(data['devices'])
    if request.is_ajax():
        return HttpResponse(json.dumps({'data': data}), content_type="application/json")
    else:
        return render(request,'home.html',{'data':data})

def filteredLive(request):
    data = {}
    uri = getFilteredLivePlot()
    data['plot'] = uri
    return render(request,'home.html',{'data':data})

def historic(request):
    uri = ''
    data = {}
    if request.method == 'POST':
        print("In historic")
        form = HistoricForm(request.POST)
        uri = gethistoricFilteredplot(form)
    else:
        uri = gethistoricplot()
    data['plot'] = uri
    return render(request,'historic.html',{'data':data})

def device(request):
    data = {}
    df = pd.read_csv("/home/muhammadwaqas/PycharmProjects/NetworkScanner/device/data/data.csv")
    uri = getdeviceplot(df)
    bytes = ''
    ips = ''
    traffic = []
    if request.method == 'POST':
        print("In post")
        form = DeviceFilterForm(request.POST)
        uri = getdeviceFilteredplot(form,df)
        ips = getFilteredUniqueIps(form, df)
        bytes = getFilteredBytes(form,df)
        traffic = getFilteredTraffic(form, df)
    else:
        uri = getdeviceplot(df)
        ips = getUniqueIps(df);
        bytes = getBytes(df)
        traffic = getTraffic(df)

    data['plot'] = uri
    data['devices'] = getLegendDevices(df);
    data['ips'] = ips;
    data['bytes'] = bytes;
    data['traffic'] = traffic;
    if request.is_ajax():
        return HttpResponse(json.dumps({'data': data}), content_type="application/json")
    else:
        return render(request,'device.html',{'data':data})

def getTraffic(df):
    print("in traffic")
    df['count'] = df.groupby(['packets_length'])['packets_length'].transform('count')
    print(df)
    df = df.groupby(['destination_ip','destination_country'])['packets_length','count'].agg('sum').reset_index()

    print(df)
    df = df.apply(list)
    print(df)
    traffic = []
    for index, row in df.iterrows():
        rowDict = {}
        rowDict['ip'] = row['destination_ip']
        rowDict['country'] = row['destination_country']
        rowDict['count'] = row['count']
        rowDict['bytes'] = row['packets_length']
        traffic.append(rowDict)

    print(traffic)
    return traffic

def getFilteredTraffic(form,df):
    if form.data['startdate'] and form.data['enddate']:
        df = getRecordsByDate(df,form)
    if form.data['device']:
        device = form['device'].value()
        df = df.loc[df['source_mac'] == device]
    print(df)
    traffic = []
    if len(df.index) > 0:
        print("in traffic")
        df['count'] = df.groupby(['packets_length'])['packets_length'].transform('count')
        print(df)
        df = df.groupby(['destination_ip', 'destination_country'])['packets_length', 'count'].agg('sum').reset_index()
        print(df)
        df = df.apply(list)
        print(df)
        for index, row in df.iterrows():
            rowDict = {}
            rowDict['ip'] = row['destination_ip']
            rowDict['country'] = row['destination_country']
            rowDict['count'] = row['count']
            rowDict['bytes'] = row['packets_length']
            traffic.append(rowDict)

        print(traffic)
    return traffic

def getUniqueIps(df):
    return str(len(list(set(df['destination_ip']))))+" unique IPs contacted"

def getFilteredUniqueIps(form,df):
    if form.data['startdate'] and form.data['enddate']:
        df = getRecordsByDate(df,form)
    if form.data['device']:
        device = form['device'].value()
        df = df.loc[df['source_mac'] == device]
    return str(len(list(set(df['destination_ip']))))+" unique IPs contacted"

def getBytes(df):
    bytes = df['packets_length'].sum()
    if bytes > 1000:
        bytes = str(int(round(bytes/1000))) + " K"
    else:
        bytes = str(bytes)
    return bytes

def getFilteredBytes(form,df):
    if form.data['startdate'] and form.data['enddate']:
        df = getRecordsByDate(df,form)
    if form.data['device']:
        device = form['device'].value()
        df = df.loc[df['source_mac'] == device]
    bytes = df['packets_length'].sum()
    if bytes > 1000:
        bytes = str(int(round(bytes / 1000))) + " K"
    else:
        bytes = str(bytes)
    return bytes

def getLivePlot(df):
    plt.clf();
    g = sns.lineplot(x=df.index, y='packets_length', hue='device', data=df)
    g.set(xticklabels=[])
    plt.xlabel("")
    plt.ylabel("Packets")
    labels = getLegendLabels(df)
    plt.legend(title='Devices', labels=labels, loc='best', ncol=1, fancybox=True, shadow=True)
    fig = plt.gcf()
    fig.set_size_inches(12, 5)
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    string = base64.b64encode(buf.read())
    uri = urllib.parse.quote(string)
    return uri

def updateDevice(form):
    print("In update device")
    device = form['device'].value()
    mac = form['mac'].value()
    print(device)
    print(mac)
    data = [mac,device]
    with open(r'/home/muhammadwaqas/PycharmProjects/NetworkScanner/device/data/devices.csv', 'a') as f:
        writer = csv.writer(f)
        writer.writerow(data)
    df = pd.read_csv("/home/muhammadwaqas/PycharmProjects/NetworkScanner/device/data/data.csv")
    df.loc[df["source_mac"] == mac, "device"] = device
    df.to_csv("/home/muhammadwaqas/PycharmProjects/NetworkScanner/device/data/data.csv", index=False)

def getFilteredLivePlot():
    plt.clf();
    df = pd.read_csv("/home/muhammadwaqas/PycharmProjects/NetworkScanner/device/data/data.csv")
    print(df.head())
    g = sns.lineplot(x='datetime', y='packets_length', hue='device', data=df)
    g.set(xticklabels=[])
    plt.xlabel("")
    plt.ylabel("Packets")
    plt.legend(title='Devices', loc='best', ncol=1, fancybox=True, shadow=True)
    fig = plt.gcf()
    fig.set_size_inches(12, 5)
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    string = base64.b64encode(buf.read())
    uri = urllib.parse.quote(string)
    return uri

def gethistoricplot():
    plt.clf();
    df = pd.read_csv("/home/muhammadwaqas/PycharmProjects/NetworkScanner/device/data/data.csv")
    print(df.head())

    historic_records = df.groupby('device')['protocol'].value_counts()
    print(historic_records.unstack())
    g = historic_records.unstack().plot(kind='bar', stacked=True,legend=True)
    plt.legend(title='Protocols',  loc='best', ncol=1, fancybox=True, shadow=True)

    plt.xticks(
        rotation = 0,
        verticalalignment='top',
        size = 10
    )
    plt.xlabel("")
    if len(df.index) > 1000:
        ylabels = ['{:,.2f}'.format(x) + 'K' for x in g.get_yticks() / 1000]
        g.set_yticklabels(ylabels)
    fig = plt.gcf()
    fig.set_size_inches(12, 5)
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    string = base64.b64encode(buf.read())
    uri = urllib.parse.quote(string)
    return uri

def gethistoricFilteredplot(form):
    print("in gethistoricFilteredplot")
    plt.clf();
    uri = ''
    df = pd.read_csv("/home/muhammadwaqas/PycharmProjects/NetworkScanner/device/data/data.csv")
    print(df.head())
    if form.data['startdate'] and form.data['enddate']:
        df = getRecordsByDate(df,form)
    type = form['type'].value()
    if len(df.index) > 0:
        historic_records = df.groupby('device')['protocol'].value_counts();
        if type =="protocol":
            historic_records = df.groupby('device')['protocol'].value_counts()
            plt.legend(title='Protocols', loc='best', ncol=1, fancybox=True, shadow=True)
        elif type =="country":
            historic_records = df.groupby('device')['destination_country'].value_counts()
            plt.legend(title='Countries', loc='best', ncol=1, fancybox=True, shadow=True)
        print(historic_records.unstack())
        g = historic_records.unstack().plot(kind='bar', stacked=True,legend=True)
        plt.xticks(
            rotation = 0,
            verticalalignment='top',
            size = 10
        )
        plt.xlabel("")
        if len(df.index) > 1000:
            ylabels = ['{:,.2f}'.format(x) + 'K' for x in g.get_yticks() / 1000]
            g.set_yticklabels(ylabels)
        fig = plt.gcf()
        fig.set_size_inches(12, 5)
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        string = base64.b64encode(buf.read())
        uri = urllib.parse.quote(string)
    return uri

def getdeviceplot(df):
    plt.clf();
    print(df.head())
    groupedvalues = df.groupby('protocol').sum().reset_index()
    groupedvalues['packets_length'] = groupedvalues['packets_length']/df['packets_length'].sum()*100
    print(groupedvalues)
    pal = sns.color_palette("Greens_d", len(groupedvalues))
    g = sns.barplot(x='protocol', y='packets_length', hue="protocol",data=groupedvalues)
    plt.ylabel("")
    g.get_yaxis().set_visible(False)
    xlabels = getUniqueDevices(df)
    for p in g.patches:
        width, height = p.get_width(), p.get_height()
        x, y = p.get_xy()
        g.annotate('{:.0%}'.format(height/100), (x, y + height + 0.01))
    plt.xlabel(xlabels)
    fig = plt.gcf()
    fig.set_size_inches(4, 5)
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    string = base64.b64encode(buf.read())
    uri = urllib.parse.quote(string)
    return uri

def getdeviceFilteredplot(form,df):
    plt.clf();
    uri = ''
    fullDF = pd.read_csv("/home/muhammadwaqas/PycharmProjects/NetworkScanner/device/data/data.csv")
    if form.data['startdate'] and form.data['enddate']:
        df = getRecordsByDate(df,form)
    device = ""
    if form.data['device']:
        device = form['device'].value()
        print(device)
        df = df.loc[df['source_mac'] == device]
        print(df)
    if len(df.index) > 0:
        groupedvalues = df.groupby('protocol').sum().reset_index()
        groupedvalues['packets_length'] = groupedvalues['packets_length'] / fullDF['packets_length'].sum() * 100
        print(groupedvalues)
        pal = sns.color_palette("Greens_d", len(groupedvalues))
        g = sns.barplot(x='protocol', y='packets_length', hue="protocol", data=groupedvalues)
        plt.ylabel("")
        g.get_yaxis().set_visible(False)
        xlabels = getUniqueDevices(df)
        for p in g.patches:
            width, height = p.get_width(), p.get_height()
            x, y = p.get_xy()
            g.annotate('{:.0%}'.format(height / 100), (x, y + height + 0.01))
        plt.xlabel(xlabels)
        fig = plt.gcf()
        fig.set_size_inches(4, 5)
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        string = base64.b64encode(buf.read())
        uri = urllib.parse.quote(string)
    return uri

def getLastFiveMinutesRecords(df):
    df = df.set_index(pd.DatetimeIndex(df['datetime']))
    df.drop('datetime', axis=1, inplace=True)
    currentDate = datetime.datetime.utcnow()+datetime.timedelta(hours=5);
    print("Current Date: ", currentDate);
    previousdate = currentDate - datetime.timedelta(minutes=30000000);
    print("Previous Date: ", previousdate)
    print(currentDate - previousdate)
    mask = (df.index >= previousdate) & (df.index<= currentDate)
    df = df[mask]
    return df

def getLastMinutesRecords(df,form):
    minute = int(form['time'].value())
    print("minutes: ",minute)
    df = df.set_index(pd.DatetimeIndex(df['datetime']))
    df.drop('datetime', axis=1, inplace=True)
    currentDate = datetime.datetime.utcnow()+datetime.timedelta(hours=5);
    print("Current Date: ", currentDate);
    previousdate = currentDate - datetime.timedelta(minutes=30000000);
    print("Previous Date: ", previousdate)
    print(currentDate - previousdate)
    mask = (df.index >= previousdate) & (df.index<= currentDate)
    df = df[mask]
    return df

def getRecordsByDate(df,form):
    startdate = datetime.datetime.strptime(form['startdate'].value(),'%Y-%m-%d')
    enddate = datetime.datetime.strptime(form['enddate'].value(),'%Y-%m-%d')
    print(startdate)
    print(enddate)
    df = df.set_index(pd.DatetimeIndex(df['datetime']))
    df.drop('datetime', axis=1, inplace=True)
    #currentDate = datetime.datetime.utcnow()+datetime.timedelta(hours=5);
    mask = (df.index >= startdate) & (df.index<= enddate)
    df = df[mask]
    return df

def getLegendDevices(df):
    macList = list(set(df['source_mac']))
    print("mac: ",macList)
    devices = {}
    for mac in macList:
        devices[mac] = df.loc[df["source_mac"] == mac, "device"].iloc[1]
    print("devices: ",devices);
    return devices

def getLegendLabels(df):
    macList = list(set(df['source_mac']))
    print("mac: ",macList)
    devices = []
    for mac in macList:
        label = df.loc[df["source_mac"] == mac, "device"].iloc[1] + " \n" + str(mac)
        devices.append(label)
    return devices

def getUniqueDevices(df):
    protocolList = list(set(df['protocol']))
    print("protocolList: ", protocolList)
    protocols = ''
    df['packets_length'] = df['packets_length'].apply(pd.to_numeric)
    for protocol in protocolList:
        packets = df.loc[df["protocol"] == protocol, "packets_length"].sum();
        protocols = protocols + str(protocol)+ ": "+str(packets)+" bytes\n"
    return protocols
