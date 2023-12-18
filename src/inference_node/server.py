import grpc
import os
import sys
from concurrent import futures
import inference_pb2 
import inference_pb2_grpc 
import onnxruntime
import numpy as np
import json
import ast
import config
import ecdsa
from ecdsa import SECP256k1
from ecdsa.keys import SigningKey, VerifyingKey
from transformers import pipeline, set_seed
import hashlib
from Crypto.Hash import keccak
import zkml

class InferenceServer(inference_pb2_grpc.InferenceServicer):
    inferenceMap = {}
    zkInferenceMap = {}
    def RunInference(self, inferenceParams, context):
        if inferenceParams.tx in self.inferenceMap:
            return self.inferenceMap[inferenceParams.tx]
        if not os.path.isfile("models/" + inferenceParams.modelHash):
            getModel(inferenceParams.modelHash)
        results = self.Infer(inferenceParams.modelHash, inferenceParams.modelInput)
        inferenceResults = inference_pb2.InferenceResult(tx=inferenceParams.tx, node=config.public_key_hex, value=str(results))
        self.inferenceMap[inferenceParams.tx] = inferenceResults
        return inferenceResults

    def RunZKInference(self, inferenceParams, context):
        if inferenceParams.tx in self.zkInferenceMap:
            return self.zkInferenceMap[inferenceParams.tx]
        if not os.path.isfile("models/" + inferenceParams.modelHash):
            getModel(inferenceParams.modelHash)
        writeInput(inferenceParams.modelInput, inferenceParams.tx)
        results = self.ZKInfer(inferenceParams.modelHash, inferenceParams.modelInput, inferenceParams.tx)
        inferenceResults = inference_pb2.ZKInferenceResult(tx=inferenceParams.tx, node=config.public_key_hex, 
            value=str(results[0]), proof=results[1], settings=results[4], vk=results[2], srs=results[3])
        self.zkInferenceMap[inferenceParams.tx] = inferenceResults
        return inferenceResults

    def ZKInfer(self, modelHash, modelInput, txHash):
        results = zkml.ezklProveSingle(modelHash, txHash, True)
        results[0] = unwrap(results[0])
        return results

    def Infer(self, modelHash, modelInput):
        session = onnxruntime.InferenceSession("./models/" + modelHash, providers=[config.execution])
        output = session.run(curateOutputs(session), curateInputs(session, modelInput))[0]
        results = unwrap(output)
        return results

    def RunPipeline(self, pipelineParams, context):
        results = self.Pipeline(pipelineParams.seed, pipelineParams.pipelineName, pipelineParams.modelHash, pipelineParams.modelInput)
        return inference_pb2.InferenceResult(tx=pipelineParams.tx, node=config.public_key_hex, value=str(results))

    def Pipeline(self, seed, pipelineName, model, inputs):
        generator = pipeline(pipelineName, model=model)
        set_seed(int(seed))
        return generator(inputs, max_length=50, num_return_sequences=1)[0]['generated_text'].split(".")[0]

def writeInput(modelInput, txHash):
    params = json.loads(modelInput)
    data = dict(input_shapes=getShape(params), input_data=params)
    json.dump(data, open("./scratch/" + txHash + ".input", 'w'))
    return

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

def getModel(cid):
    path = "./models/" + cid
    if os.path.isfile(path):
        return
    os.system("ipfs get --output=./models/" + cid + " " + cid)

def sign(privateKeyHex, message):
    privateKey = SigningKey.from_string(bytes.fromhex(privateKeyHex), curve=SECP256k1)
    k = keccak.new(digest_bits=256)
    k.update(b'message')
    signature = privateKey.sign(k.digest())
    return signature.hex()

def verify(publicKeyHex, signature, value):
    publicKey = VerifyingKey.from_string(bytes.fromhex(publicKeyHex), curve=SECP256k1)
    k = keccak.new(digest_bits=256)
    k.update(bytes(value.encode()))
    try:
        publicKey.verify(bytes.fromhex(signature), k.digest())
        return True
    except ecdsa.BadSignatureError:
        print("Signature cannot be verified")
        return False

def unwrap(outputs):
    if outputs.__class__ != list and outputs.__class__ != np.ndarray:
        return outputs
    if len(outputs) == 1:
        return unwrap(outputs[0])
    results = []
    for x in outputs:
        results.append(unwrap(x))
    return results

def getShape(params):
    if isinstance(params, list):
        shape = []
        if isinstance(params[0], list):
            for p in params:
                shape.append(getShape(p))
        else:
            shape.append(len(params))
        return shape

serve(config.port, config.max_workers)
