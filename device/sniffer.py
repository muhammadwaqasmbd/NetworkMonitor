import netifaces
import pyshark
import geoip2.database
import IP2Location
import csv
import datetime
from urllib.request import Request, urlopen
from json import load
from scapy import *
import socket as s
import pandas as pd
interface = netifaces.interfaces()
print(interface)
for i in interface:
    print(i + ": " + str(netifaces.ifaddresses(i)))

reader = geoip2.database.Reader('./data/IP/City.mmdb')

IP2LocObj = IP2Location.IP2Location()
database = IP2Location.IP2Location("data/IP2/data.BIN")

def is_not_blank(s):
    return bool(s and s.strip())

def getCountry1(ip):
    try:
        response = database.get_all(ip)
        response = response.country_long
    except:
        response = "Unknown"
    if not response:
        response = "Unknown"
    return response

def getCountry2(ip):
    try:
        response = reader.city(ip)
        response = response.country.name
    except:
        response = "Unknown"
    if not response :
        response = "Unknown"
    return response

def getCountry3(ip):
    headers = {
        'authority': 'www.geoplugin.net',
        'pragma': 'no-cache',
        'cache-control': 'no-cache',
        'dnt': '1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'sec-fetch-site': 'none',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-dest': 'document',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    }
    url = Request(
        'http://www.geoplugin.net/json.gp?ip='+ip,
        headers=headers)
    res = urlopen(url)
    data = load(res)
    if data['geoplugin_countryName'] == None :
        return 'Unknown'
        data['geoplugin_countryName']
    return data['geoplugin_countryName']

def arpInformation():
    arpInfo = [re.findall('^[\w\?\.]+|(?<=\s)\([\d\.]+\)|(?<=at\s)[\w\:]+', i) for i in os.popen('arp -a')]
    arpInfo = [dict(zip(['HOST', 'IP2', 'MAC'], i)) for i in arpInfo]
    arpInfo = [{**i, **{'IP2': i['IP2'][1:-1]}} for i in arpInfo]
    return arpInfo

arpInfo = arpInformation()
print(arpInfo)

devicesDF = pd.read_csv("/home/muhammadwaqas/PycharmProjects/NetworkScanner/device/data/devices.csv")

capture = pyshark.LiveCapture(interface='wlp3s0', use_json=True, include_raw=True, custom_parameters = {'-N': 'm'})
capturedInfo = []

for packet in capture.sniff_continuously():
    capDict = {}
    try:
        if '192.168.' in packet.ip.src:
            country = getCountry1(packet.ip.dst)
            if is_not_blank(country) or country == "Unknown-Country":
                country = getCountry2(packet.ip.dst)
            device = ""
            try:
                mac = str(packet.eth.src)
                device = devicesDF.loc[devicesDF["mac"] == mac, "device"].iloc[0]
            except:
                device = "Unknown-Device"

            if device == "" or device == "Unknown-Device":
                try:
                    device = s.gethostbyaddr(packet.ip.src)[0]
                except:
                    device = "Unknown-Device"
            protocol = packet.transport_layer
            source_ip = packet.ip.src
            source_port = packet[packet.transport_layer].srcport
            source_mac = packet.eth.src
            destination_ip = packet.ip.dst
            destination_port = packet[packet.transport_layer].dstport
            destination_mac = packet.eth.dst
            destination_country = country
            packets_length = packet.length
            vendor = 'Unknown-Vendor'
            if is_not_blank(str(packet.eth._all_fields['eth.src_tree']['eth.src.oui_resolved'])):
                vendor = packet.eth._all_fields['eth.src_tree']['eth.src.oui_resolved']
            capturedInfo.append(capDict)
            data = [protocol,device, vendor, source_ip, source_port, source_mac,destination_ip,destination_port,destination_mac,destination_country,packets_length, datetime.datetime.now()]
            with open(r'data/data.csv', 'a') as f:
                writer = csv.writer(f)
                writer.writerow(data)
            print('%s %s %s %s %s:%s %s --> %s --> %s:%s %s %s' % ("Protocol : "+str(protocol), ", Device : "+str(device), ", Vendor : "+str(vendor),
                                                                   ", Source IP & Port : "+str(source_ip), str(source_port), ", Source MAC : "+str(source_mac),
                                                                   ", Packets : "+str(packets_length),", Destination IP : "+str(destination_ip),
                                                                   str(destination_port),", Destination MAC : "+str(destination_mac), ", Country : "+str(destination_country),
                                                                   ", Date Time : "+str(datetime.datetime.now())))
    except Exception as e:
        print(e)

print(capturedInfo)
capture.close()

