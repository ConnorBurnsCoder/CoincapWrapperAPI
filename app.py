'''
Created on Apr 2, 2022

@author: Connor Burns
'''
import requests
from collections import defaultdict
from fuzzywuzzy import process,fuzz
from flask import Flask,abort
app = Flask(__name__)

def __getURL(extension):
    return "http://api.coincap.io/v2/{}".format(extension)

def __verifyResponseSucceeded(response):
    if not (response.ok and "data" in response.json()):
        abort(400)
        
def __convertToFloat(num):
    try:
        return float(num)
    except ValueError:
        abort(400)

class CryptoWallet:
    def __init__(self):
        self.walletDict = defaultdict(float)
        self.validCurrencyIds, self.validCurrencyNameIndex = CryptoWallet.__getAssetIdListAndNameIndex()
        CryptoWallet.similarityThreshold = 80
    
    @staticmethod
    def __getAssetIdListAndNameIndex():
        response = requests.request("GET", "http://api.coincap.io/v2/assets", headers={}, data={})
        assetIdList = []
        assetNameIndex = {}
        responseData = response.json()["data"]
        for asset in responseData:
            assetIdList.append(asset["id"])
            assetNameIndex[asset["name"]]=asset["id"]
        return assetIdList,assetNameIndex
        
    def __tryMatchCurrencyName(self,currencyName):
        selection= process.extractOne(currencyName, self.validCurrencyNameIndex.keys(), scorer=fuzz.token_sort_ratio)
        if selection[1] < CryptoWallet.similarityThreshold:
            return -1
        return selection[0]
    
    def __tryMatchCurrencyIdByName(self,currencyName):
        #returns Currency ID if one could be matched, otherwise return -1
        if currencyName not in self.validCurrencyNameIndex.keys():
            currencyName=self.__tryMatchCurrencyName(currencyName)
            if currencyName==-1:
                return -1
        return self.validCurrencyNameIndex[currencyName]
    
    def addCurrency(self,currencyId,amount):
        #returns -1 if not a valid Id, returns the current currency total if the ID is valid
        if currencyId not in self.validCurrencyIds:
            return -1
        self.walletDict[currencyId]+=amount
        return self.walletDict[currencyId]
    
    def addCurrencyByName(self,currencyName,amount):
        #returns -1 if currencyName could not be matched to a valid name, returns the current currency total if the ID is valid
        currencyId = self.__tryMatchCurrencyIdByName(currencyName)
        if(currencyId==-1):
            return -1
        self.walletDict[currencyId]+=amount
        return self.walletDict[currencyId]
    
    def setCurrency(self,currencyId,amount):
        #returns -1 if not a valid Id, returns the current currency total if the ID is valid
        if currencyId not in self.validCurrencyIds:
            return -1
        self.walletDict[currencyId]=amount
        return self.walletDict[currencyId]
    
    def setCurrencyByName(self,currencyName,amount):
        #returns -1 if currencyName could not be matched to a valid name, returns the current currency total if the ID is valid
        currencyId = self.__tryMatchCurrencyIdByName(currencyName)
        if(currencyId==-1):
            return -1
        self.walletDict[currencyId]=amount
        return self.walletDict[currencyId]
        
    def getCurrencyBalance(self,currencyId):
        return self.walletDict[currencyId]
    
    def getCurrencyBalanceByName(self,currencyName):
        currencyId = self.__tryMatchCurrencyIdByName(currencyName)
        if(currencyId==-1):
            return -1
        return self.walletDict[currencyId]
    
    def getCurrencyBalanceInUSD(self,currencyId):
        return convertBalanceToUSD(currencyId,self.walletDict[currencyId])
    
    def getTotalBalanceInUSD(self):
        totalBalanceUSD=0.0
        for currencyId in self.walletDict.keys():
            currencyBalanceUSD=self.getCurrencyBalanceInUSD(currencyId)["BalanceInUSD"]
            totalBalanceUSD+=currencyBalanceUSD
        return totalBalanceUSD

wallet = CryptoWallet()

@app.errorhandler(400)
def currencyIdDoesNotExist(error):
    return error, 400

@app.route('/GetAssetNames')
def getAssetNameList():
    response = requests.request("GET", __getURL("assets"), headers={}, data={})
    __verifyResponseSucceeded(response)
    assetList = []
    responseData = response.json()["data"]
    for asset in responseData:
        assetList.append(asset["name"])
    return {"AssetNames": assetList}

@app.route('/GetAssetDetails/<currencyId>')
def getAssetDetails(currencyId):
    response = requests.request("GET", __getURL("assets/{}".format(currencyId)), headers={}, data={})
    __verifyResponseSucceeded(response)
    return response.json()["data"]

@app.route('/GetUSDConversionRate/<currencyId>')
def getUSDConversionRate(currencyId):
    response = requests.request("GET", __getURL("rates/{}".format(currencyId)), headers={}, data={})
    __verifyResponseSucceeded(response)
    return response.json()["data"]["rateUsd"]

@app.route('/GetBalanceConvertedToUSD/<currencyId>/<balance>')
def convertBalanceToUSD(currencyId,balance):
    rate = getUSDConversionRate(currencyId)
    return {"BalanceInUSD": __convertToFloat(balance)*float(rate)}

@app.route('/AddCurrency/<currencyId>/<amount>')
def addCurrency(currencyId,amount):
    newBalance = wallet.addCurrency(currencyId,__convertToFloat(amount))
    if(newBalance==-1):
        abort(400)
    return {"Balance": newBalance}

@app.route('/AddCurrencyByName/<currencyName>/<amount>')
def addCurrencyByName(currencyName,amount):
    newBalance = wallet.addCurrencyByName(currencyName,__convertToFloat(amount))
    if(newBalance==-1):
        abort(400)
    return {"Balance": newBalance}

@app.route('/SetCurrency/<currencyId>/<amount>')
def setCurrency(currencyId,amount):
    newBalance = wallet.setCurrency(currencyId,__convertToFloat(amount))
    if(newBalance==-1):
        abort(400)
    return {"Balance": newBalance}

@app.route('/SetCurrencyByName/<currencyName>/<amount>')
def setCurrencyByName(currencyName,amount):
    newBalance = wallet.setCurrencyByName(currencyName,__convertToFloat(amount))
    if(newBalance==-1):
        abort(400)
    return {"Balance": newBalance}
    
@app.route('/GetCurrencyBalance/<currencyId>')
def getCurrencyBalance(currencyId):
    balance = wallet.getCurrencyBalance(currencyId)
    if(balance==-1):
        abort(400)
    return {"Balance": balance}

@app.route('/GetCurrencyBalanceByName/<currencyName>')
def getCurrencyBalanceByName(currencyName):
    balance = wallet.getCurrencyBalanceByName(currencyName)
    if(balance==-1):
        abort(400)
    return {"Balance": balance}

@app.route('/GetCurrencyBalanceInUSD/<currencyId>')
def getCurrencyBalanceInUSD(currencyId):
    return wallet.getCurrencyBalanceInUSD(currencyId)
    
@app.route('/GetTotalBalanceInUSD/')
def getTotalBalanceInUSD():
    return {"TotalBalanceInUSD": wallet.getTotalBalanceInUSD()}
    
@app.route('/GetWalletContents/')
def getWalletContents():
    return wallet.walletDict

@app.route('/')
def homePage():
    links = []
    for rule in app.url_map.iter_rules():
        if(rule.endpoint!="homePage" and rule.endpoint!="static"):
            links.append(rule.endpoint)
    return {"Welcome to My CoinCap.IO API Use the following routes to navigate": links}