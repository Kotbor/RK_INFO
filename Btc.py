import requests

host='http://10.98.26.6:8090'

xml = '''<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://schemas.xmlsoap.org/wsdl/" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:tns="http://tempuri.org/" xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/" xmlns:mime="http://schemas.xmlsoap.org/wsdl/mime/" xmlns:ns1="urn:OrionProIntf" xmlns:ns2="http://www.borland.com/namespaces/Types" name="IOrionProservice" targetNamespace="http://tempuri.org/">
<operation name="GetServiceInfo">
<operation xmlns="http://schemas.xmlsoap.org/wsdl/soap/" soapAction="urn:OrionProIntf-IOrionPro#GetServiceInfo" style="rpc"/>
<input>
<body xmlns="http://schemas.xmlsoap.org/wsdl/soap/" use="encoded" encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" namespace="urn:OrionProIntf-IOrionPro"/>
</input>
<output>
<body xmlns="http://schemas.xmlsoap.org/wsdl/soap/" use="encoded" encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" namespace="urn:OrionProIntf-IOrionPro"/>
</output>
</operation>
'''

headers = {'Content-Type': 'application/soap+xml', 'Accept-Encoding': 'identity'}

MenuItem1 = requests.post(host, verify=False, data=xml).text
print (MenuItem1)