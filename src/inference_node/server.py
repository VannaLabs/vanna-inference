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

class InferenceServer(inference_pb2_grpc.InferenceServicer):

    cache = cache.InferenceCache()

    def RunInference(self, inferenceParams, context):
        cached = self.cache.retrieve(utils.InferenceType.INFERENCE, inferenceParams.tx)
        if cached is not None:
            return cached
        elif context.peer().split(":")[1] != config.sequencer_ip: 
            return
        utils.modelCheck(inferenceParams.modelHash)
        results = self.Infer(inferenceParams.modelHash, inferenceParams.modelInput)
        inferenceResults = inference_pb2.InferenceResult(tx=inferenceParams.tx, node=config.public_key_hex, value=str(results))
        self.cache.store(utils.InferenceType.INFERENCE, inferenceParams.tx, inferenceResults)
        return inferenceResults

    def RunZKInference(self, inferenceParams, context):
        cached = self.cache.retrieve(utils.InferenceType.ZKINFERENCE, inferenceParams.tx)
        if cached is not None:
            return cached
        elif context.peer().split(":")[1] != config.sequencer_ip: 
            return
        utils.modelCheck(inferenceParams.modelHash)
        zkml.writeInput(inferenceParams.modelInput, inferenceParams.tx)
        results = self.ZKInfer(inferenceParams.modelHash, inferenceParams.modelInput, inferenceParams.tx)
        inferenceResults = inference_pb2.ZKInferenceResult(tx=inferenceParams.tx, node=config.public_key_hex, 
            value=str(results[0]), proof=results[1], settings=results[4], vk=results[2], srs=results[3])
        self.cache.store(utils.InferenceType.ZKINFERENCE, inferenceParams.tx, inferenceResults)
        return inferenceResults

    def RunPipeline(self, pipelineParams, context):
        cached = self.cache.retrieve(utils.InferenceType.PIPELINE, inferenceParams.tx)
        if cached is not None:
            return cached
        results = self.Pipeline(pipelineParams.seed, pipelineParams.pipelineName, pipelineParams.modelHash, pipelineParams.modelInput)
        return inference_pb2.InferenceResult(tx=pipelineParams.tx, node=config.public_key_hex, value=str(results))

    def Infer(self, modelHash, modelInput):
        session = onnxruntime.InferenceSession("./models/" + modelHash, providers=[config.execution])
        output = session.run(utils.curateOutputs(session), utils.curateInputs(session, modelInput))[0]
        results = utils.unwrap(output)
        return results

    def ZKInfer(self, modelHash, modelInput, txHash):
        results = zkml.ezklProveSingle(modelHash, txHash, True)
        results[0] = unwrap(results[0])
        return results

    def Pipeline(self, seed, pipelineName, model, inputs):
        generator = pipeline(pipelineName, model=model)
        set_seed(int(seed))
        return generator(inputs, max_length=50, num_return_sequences=1)[0]['generated_text'].split(".")[0]

def serve(port, maxWorkers):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=maxWorkers))
    inference_pb2_grpc.add_InferenceServicer_to_server(InferenceServer(), server)
    server.add_insecure_port("[::]:" + str(port))
    server.start()
    server.wait_for_termination()

serve(config.port, config.max_workers)
