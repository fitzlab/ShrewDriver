import random

# An enhanced Enumeration that's really good for working with nouns
# Eliminates so much gross formatting code, it's great

class Term():
    def __init__(self, base):
        self.base = base.capitalize()
        self.plural = self.base + "s"
        self.ppart = self.base + "ing" #present participle, e.g. "train" -> "training"
        self.enumKey = self.base
        
        self.idx = 0
    
    def __repr__(self):
        return self.base

    def __int__(self):
        return self.idx    
    
    #Terms are considered equal if they have the same index, as with an enum.
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.idx == other.idx
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other) 

class TermSet():
    def __init__(self,strings):
        #makes terms from a list of strings
        self.strings = strings
        self.terms = {}
        idx = 0
        for s in strings:
            t = Term(s)
            t.idx = idx
            idx += 1
            self.terms[s] = t
    
    #objects can be referred to, enum-style, by their base
    def __getattr__(self, s):
        if not self.terms.has_key(s):
            raise AttributeError
        return self.terms[s]

    def __len__(self):
        return len(self.terms)   
    
    def get(self,idx):
        return self.__getattr__(self.strings[idx])
    
    def randomChoice(self):
        return self.terms[random.choice(self.terms.keys())]
        

if __name__ == '__main__':
    #examples
    Races = TermSet(['DRACONIAN','FROSTLING','HUMAN','DWARF'])
    print Races.DRACONIAN
    print Races.DRACONIAN.plural
    
    print "\n"
    Actions = TermSet(['TRAIN','ATTACK','EXPAND'])
    print Actions.EXPAND
    print Actions.TRAIN.ppart
    
    print "\n"    
    a = Actions.EXPAND
    print str(a == Actions.EXPAND) #True
    print str(a == Actions.TRAIN)  #False
    print str(a == Races.HUMAN)    #True, since indices will match
    
    print "\n"        
    