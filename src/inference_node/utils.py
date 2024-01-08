from enum import Enum
import ecdsa
from ecdsa import SECP256k1
from ecdsa.keys import SigningKey, VerifyingKey
import os
import ast
import onnxruntime
import numpy as np

class InferenceType(Enum):
    INFERENCE = 1
    ZKINFERENCE = 2
    PIPELINE = 3
    PRIVATE = 4
    OPTIMISTIC = 5
    BATCH = 6
    NONE = 7

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

def modelCheck(modelHash):
    path = "models/" + modelHash
    if not os.path.isfile(path) and not os.path.isdir(path):
        getModel(modelHash)
