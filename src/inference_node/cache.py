import utils

class InferenceCache:

    def __init__(self):
    	self.cache = {}
    	for inferenceType in utils.InferenceType:
    		self.cache[inferenceType] = {}

    def store(self, inferenceType, tx, value):
    	self.cache[inferenceType][tx] = value

    def retrieve(self, inferenceType, tx):
    	if inferenceType in self.cache and tx in self.cache[inferenceType]:
    		return self.cache[inferenceType][tx]
    	else:
    		return None

        