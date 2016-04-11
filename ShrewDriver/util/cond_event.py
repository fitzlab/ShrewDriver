from __future__ import division
import sys
sys.path.append("..")

class CondEvent():
    # The CondEvent class defines a causal relationship that you can use to make reactive objects.
    
    # An instance of this class contains references to at least two functions.
    
    # "causes" is a boolean function, or a list of boolean functions.
    # "effects" is a function, or list of functions, to be called when causes are all True.
    
    # If causes is "None" or an empty list, the effects will be executed every time.
    
    # If a cause is a tuple, the rightmost function will be evaluated first,
    # then its result will be fed into the next rightmost, and so on. The most obvious 
    # use is to negate a function, see negation example below.

    # If you are a design patterns person, you can think of this as the Command pattern, implemented
    # with functions instead of classes. Same idea, less code.
    # You can also think of this as a lightweight event system. 
    # The SimPy package is a fancier implementation -- could be interesting someday.
    
    def __init__(self, causes, effects, name=""):
        #causes is a function or a list of functions
        if type(causes) is list:
            self.causes = causes
        else:
            self.causes = [causes]
            
        
        #effects is a function or list of functions
        if type(effects) == type([]):  
            self.effects = effects
        else:
            self.effects = [effects]
        
        #the name parameter is optional but very useful for debugging, managing a collection of CondEvents, etc.
        #It is recommended that you give each action a name.
        self.name = name
        
    def attempt(self):
        #see if our causes are ready
        for cause in self.causes:
            if type(cause) is tuple:
                #apply functions right to left
                result = cause[len(cause)-1]()
                for i in range(len(cause)-2, -1, -1):
                    result = cause[i](result)
                if not result:
                    return False
            elif not cause():
                return False
        
        #all causes passed, so do effects
        for result in self.effects:
            result()
        return True
    
    def doFcn(self, fcn, arg):
        fcn(arg)
    
# Fun shorthand for negation
import operator
aint = operator.not_


if __name__ == "__main__":
    
    #syntax example -- negation
    broke = lambda:True
    
    def fixIt():
        print "Fixing it..."
        
    def dontFixIt():
        print "Error: Wasn't supposed to fix it."
    
    ce1 = CondEvent(broke, fixIt, "positive")
    ce2 = CondEvent((aint, broke), dontFixIt, "negation")
    ce3 = CondEvent((aint, aint, broke), fixIt, "doubleNegation")
    
    print "\nCE1"    
    ce1.attempt()
    
    print "\nCE2"
    ce2.attempt() #does not execute
    
    print "\nCE3"
    ce3.attempt()

    