import utils
import time

class InferenceCache:

    def __init__(self):
    	self.cache = {}
    	for inferenceType in utils.InferenceType:
    		self.cache[inferenceType] = {}

    def searchCache(self, tx):
        for inferenceType in utils.InferenceType:
            if inferenceType in self.cache and tx in self.cache[inferenceType]:
                return self.cache[inferenceType][tx]
        return None

    def store(self, inferenceType, tx, value):
    	self.cache[inferenceType][tx] = value

    def retrieve(self, inferenceType, tx):
        if inferenceType in self.cache and tx in self.cache[inferenceType]:
            while (self.cache[inferenceType][tx] is None):
                time.sleep(0.5)
        else:
            self.cache[inferenceType][tx] = None
        return self.cache[inferenceType][tx]

        
