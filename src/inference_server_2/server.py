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
from ecdsa import SECP256k1
from ecdsa.keys import SigningKey, VerifyingKey
from transformers import pipeline, set_seed
import hashlib

class InferenceServer(inference_pb2_grpc.InferenceServicer):
    def RunInference(self, inferenceParams, context):
        results = self.Infer(inferenceParams.modelHash, inferenceParams.modelInput)
        return inference_pb2.InferenceResult(tx=inferenceParams.tx, node=sign(config.private_key_hex, str(results)), value=str(results))

    def Infer(self, modelHash, modelInput):
        session = onnxruntime.InferenceSession(modelHash, providers=["CPUExecutionProvider"])
        results = session.run(curateOutputs(session), curateInputs(session, modelInput))[-1]
        return results[0][0]

    def RunPipeline(self, pipelineParams, context):
        results = self.Pipeline(pipelineParams.seed, pipelineParams.pipelineName, pipelineParams.modelHash, pipelineParams.modelInput)
        return inference_pb2.InferenceResult(tx=pipelineParams.tx, node=sign(config.private_key_hex, str(results)), value=str(results))

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

def sign(private_key_hex, message):
    private_key = SigningKey.from_string(bytes.fromhex(private_key_hex), curve=SECP256k1)
    signature = private_key.sign(message.encode())
    signature_hex = signature.hex()
    return signature_hex

def verify(public_key_hex, signature_hex):
    public_key = VerifyingKey.from_string(bytes.fromhex(public_key_hex), curve=SECP256k1)
    try:
        public_key.verify(signature, "message".encode())
        return True
    except ecdsa.BadSignatureError:
        print("Signature cannot be verified")
        return False


serve(config.port, config.maxWorkers)
