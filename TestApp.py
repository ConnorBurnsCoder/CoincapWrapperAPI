'''
Created on Apr 2, 2022

@author: Connor Burns
'''
import unittest
import app

class InlineClass(object):
    def __init__(self, dict):
        self.__dict__ = dict

class Test(unittest.TestCase):
    
    def testGetAssetNameList(self):
        msg = "GetAssetNameList failed"
        result = app.getAssetNameList()
        self.assertTrue(len(result["AssetNames"])>1, msg)
        self.assertTrue("Bitcoin" in result["AssetNames"], msg)
        
    def testGetAssetDetails(self):
        msg = "GetAssetDetails failed"
        result = app.getAssetDetails("bitcoin")
        self.assertEqual(len(result), 12, msg)
        self.assertEqual(result["explorer"], "https://blockchain.info/", msg)
        self.assertEqual(result["symbol"], "BTC", msg)
        
    def testConvertBalanceToUSD(self):
        msg = "ConvertBalanceToUSD failed"
        result = app.convertBalanceToUSD("bitcoin",2)
        self.assertTrue(result["BalanceInUSD"]>0, msg)
        
    def testAddCurrency(self):
        msg = "AddCurrency failed"
        result = app.addCurrency("bitcoin",5)
        self.assertEqual(result["Balance"],5, msg)
        result = app.addCurrency("bitcoin",5)
        self.assertEqual(result["Balance"],10, msg)
    
    

if __name__ == "__main__":
    unittest.main()