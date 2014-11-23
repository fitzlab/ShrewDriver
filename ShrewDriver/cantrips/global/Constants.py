from __future__ import division
from Enumeration import Enumeration

#stores enums and values used in various places

'''
Sequences:
    RANDOM - Each trial is chosen randomly from the set of possible trials. (sample with replacement)
    BLOCK - Each trial is presented once (random order). 
    RANDOM_RETRY - Each trial is chosen randomly. If a trial is failed, keep retrying until success.
    BLOCK_RETRY - Each trial is presented once (random order). Unsuccessful trials are repeated until success.
'''

sequenceSet = ['RANDOM', 'BLOCK', 'RANDOM_RETRY', 'BLOCK_RETRY'] 
Sequences = Enumeration("Sequences", sequenceSet)



'''
Trial Results:
    SUCCESS - Correct lick
    FAILURE - Incorrect lick
    ABORT - Shrew left IR beam
    NORESPONSE - Shrew didn't lick
'''
resultsSet = ['SUCCESS', 'FAILURE', 'ABORT', 'NORESPONSE'] 
Results = Enumeration("Results", resultsSet)
