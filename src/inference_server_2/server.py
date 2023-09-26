import grpc
import sys
from concurrent import futures
import inference_pb2_grpc 
import onnx
import onnxruntime
import numpy as np
import inference_pb2 
import ezkl
import ast
import config
import ecdsa
from ecdsa.keys import SigningKey, VerifyingKey
import hashlib

class InferenceServer(inference_pb2_grpc.InferenceServicer):
    def RunInference(self, inferenceParams, context):
        results = self.Infer(inferenceParams.modelHash, inferenceParams.modelInput)
        return inference_pb2.InferenceResult(tx=inferenceParams.tx, node=inferenceParams.modelHash, value=str(results))

    def Infer(self, modelHash, modelInput):
        session = onnxruntime.InferenceSession(modelHash, providers=['CPUExecutionProvider'])
        results = session.run(curateOutputs(session), curateInputs(session, modelInput))[-1]
        return results[0][0]

def serve(port, maxWorkers):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=maxWorkers))
    inference_pb2_grpc.add_InferenceServicer_to_server(InferenceServer(), server)
    server.add_insecure_port("[::]:" + str(port))
    server.start()
    server.wait_for_termination()
    
def parseInput(modelInput, typeString):
    if "tensor" in typeString:
        if "float" in typeString:
            return onnxruntime.OrtValue.ortvalue_from_numpy(np.array([modelInput]).astype("float32"))
        if "string" in typeString:
            return onnxruntime.OrtValue.ortvalue_from_numpy(np.array([modelInput]).astype("string"))

def curateInputs(session, modelInput):
    inputs = {}
    sessionInputs = session.get_inputs()
    for i in range(0, len(sessionInputs)):
        param = ast.literal_eval(modelInput)[i]
        inputs[sessionInputs[i].name] = parseInput(param, sessionInputs[i].type)
    return inputs

def curateOutputs(session):
    outputs = []
    for o in session.get_outputs():
        outputs.append(o.name)
    return outputs

def sign(private_key):
    signing_key = ecdsa.SigningKey.from_string(private_key, curve=ecdsa.SECP256k1)

serve(config.port, config.maxWorkers)
