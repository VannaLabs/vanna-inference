import grpc
import os
import sys
from concurrent import futures
import inference_pb2 
import inference_pb2_grpc 
import onnxruntime
import numpy as np
import json
import config
from transformers import pipeline, set_seed
import hashlib
from Crypto.Hash import keccak
import zkml
import cache
import types
import utils
import pipeline

class InferenceServer(inference_pb2_grpc.InferenceServicer):

    def __init__(self):
        self.txCache = cache.InferenceCache()
        self.pipelineManager = pipeline.PipelineManager()

    def GetCachedInference(self, inferenceParams, context):
        cached = self.txCache.searchCache(inferenceParams.tx)
        if cached is None:
            return inference_pb2.InferenceResult(inferenceType=str(utils.InferenceType.NONE))
        return cached

    def RunInference(self, inferenceParams, context):
        cached = self.txCache.retrieve(utils.InferenceType.INFERENCE, inferenceParams.tx)
        if cached is not None:
            return cached
        utils.modelCheck(inferenceParams.modelHash)
        results = self.Infer(inferenceParams.modelHash, inferenceParams.modelInput)
        inferenceResults = inference_pb2.InferenceResult(inferenceType=str(utils.InferenceType.INFERENCE), tx=inferenceParams.tx, node=config.public_key_hex, value=bytes(results, 'utf-8'))
        self.txCache.store(utils.InferenceType.INFERENCE, inferenceParams.tx, inferenceResults)
        return inferenceResults

    def RunZKInference(self, inferenceParams, context):
        cached = self.txCache.retrieve(utils.InferenceType.ZKINFERENCE, inferenceParams.tx)
        if cached is not None:
            return cached
        utils.modelCheck(inferenceParams.modelHash)
        zkml.writeInput(inferenceParams.modelInput, inferenceParams.tx)
        results = self.ZKInfer(inferenceParams.modelHash, inferenceParams.modelInput, inferenceParams.tx)
        inferenceResults = inference_pb2.InferenceResult(inferenceType=str(utils.InferenceType.ZKINFERENCE), tx=inferenceParams.tx, node=config.public_key_hex, 
            value=bytes(results[0], 'utf-8'), proof=results[1], settings=results[4], vk=results[2], srs=results[3])
        self.txCache.store(utils.InferenceType.ZKINFERENCE, inferenceParams.tx, inferenceResults)
        return inferenceResults

    def RunPipeline(self, pipelineParams, context):
        cached = self.txCache.retrieve(utils.InferenceType.PIPELINE, pipelineParams.tx)
        if cached is not None:
            return cached
        results = self.PipelineInfer(pipelineParams.seed, pipelineParams.pipelineName, pipelineParams.modelHash, pipelineParams.modelInput)
        inferenceResults = inference_pb2.InferenceResult(inferenceType=str(utils.InferenceType.PIPELINE), tx=pipelineParams.tx, node=config.public_key_hex, value=results)
        self.txCache.store(utils.InferenceType.PIPELINE, pipelineParams.tx, inferenceResults)
        return inferenceResults

    def Infer(self, modelHash, modelInput):
        session = onnxruntime.InferenceSession("./models/" + modelHash, providers=[config.execution])
        output = session.run(utils.curateOutputs(session), utils.curateInputs(session, modelInput))[0]
        results = str(utils.unwrap(output))
        return results

    def ZKInfer(self, modelHash, modelInput, txHash):
        results = zkml.ezklProveSingle(modelHash, txHash, True)
        results[0] = str(utils.unwrap(results[0]))
        return results

    def PipelineInfer(self, seed, pipelineName, modelHash, inputs):
        utils.modelCheck(modelHash)
        return self.pipelineManager.infer(seed, pipelineName, "./models/" + modelHash, inputs)

def serve(port, maxWorkers):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=maxWorkers))
    inference_pb2_grpc.add_InferenceServicer_to_server(InferenceServer(), server)
    server.add_insecure_port("[::]:" + str(port))
    server.start()
    server.wait_for_termination()

serve(config.port, config.max_workers)
