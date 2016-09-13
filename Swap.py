import pySwap

class  CSwap(object):
    """docstring for  CSwap"""
    def __init__(self, name,intCount,strCount):
        super( CSwap, self).__init__()
        self.Core =  pySwap.new(name,intCount,strCount)
        
    def __del__(self):
        pySwap.free(self.Core)        

    def getFloat(self,index):
        return pySwap.GetDoubleVal(self.Core,index )        

    def getString(self,index):
        return pySwap.GetStringVal(self.Core,index )    

    def setFloat(self,index,value):
        pySwap.SetDoubleVal(self.Core,index,value )

    def setString(self,index,value):
        pySwap.SetDoubleVal(self.Core,index,value )


 