import ezkl
import os
import json
import utils

def ezklProveSingle(modelName, transactionID, public):
    proofStrategy = "single"
    execDir = "scratch/"
    modelPath = "models/" + modelName
    compiledModelPath = modelPath + "_compiled"
    settingsPath = execDir + transactionID + ".settings"
    vkPath = execDir + transactionID + ".vk"
    pkPath = execDir + transactionID + ".pk"
    witnessPath = execDir + transactionID + ".witness"
    dataPath = execDir + transactionID + ".input"
    proofPath = execDir + transactionID + ".pf"

    runArgs = ezkl.PyRunArgs()
    runArgs.input_visibility = "public"
    runArgs.output_visibility = "public"
    runArgs.variables = [("batch_size", 1)]

    if public:
        runArgs.param_visibility = "kzgcommit" 
    else:
        runArgs.param_visibility = "private"

    # zkML Setup
    if not genSettings(modelPath, settingsPath, runArgs):
        raise Exception("Unable to generate ezKL settings")

    # TODO: calibrateSettings

    if not compileModel(modelPath, compiledModelPath, settingsPath):
        raise Exception("Unable to compile model " + str(modelPath))

    srsPath = getSrs(settingsPath)
    if not srsPath:
        raise Exception("Unable to obtain SRS")

    if not zkSetup(compiledModelPath, vkPath, pkPath, srsPath):
        raise Exception("Unable to setup ezKL keys")

    if not genWitness(dataPath, compiledModelPath, witnessPath):
        raise Exception("Unable to generate witness")

    # zkML Proof Generation
    proof = zkProve(witnessPath, compiledModelPath, pkPath, proofPath, srsPath, proofStrategy)
    if not proof:
        raise Exception("Unable to generate ezKL proof")

    # zkML Proof Validation
    valid = zkVerify(proofPath, settingsPath, vkPath, srsPath)
    if not valid:
        raise Exception("Unable to validate ezKL proof")

    vkFile = open(vkPath, "rb")
    vk = vkFile.read() 
    vkFile.close()

    proofFile = open(proofPath)
    proof = proofFile.read()
    proofFile.close()

    settingsFile = open(settingsPath)
    settings = settingsFile.read()
    settingsFile.close()

    results = [extractOutput(witnessPath, settingsPath), proof, vk, srsPath, settings]

    cleanUp([witnessPath, settingsPath, pkPath, vkPath, proofPath, compiledModelPath, dataPath])
    return results

def extractOutput(witnessPath, settingsPath):
    # Convert the quantized ezkl output to float value
    outputs = json.load(open(witnessPath))['outputs']
    with open(settingsPath) as f:
        settings = json.load(f)
    ezkl_outputs = [[ezkl.vecu64_to_float(
        outputs[i][j], settings['model_output_scales'][i]) for j in range(len(outputs[i]))] for i in range(len(outputs))]
    return ezkl_outputs

def genSettings(modelPath, settingsPath, runArgs):
    # Generate Settings
    if not ezkl.gen_settings(modelPath, settingsPath, py_run_args=runArgs):
        return False
    return True

def compileModel(modelPath, compiledModelPath, settingsPath):
    # Compile ONNX model into circuit
    if not ezkl.compile_circuit(modelPath, compiledModelPath, settingsPath):
        return False
    return True

def getSrs(settingsPath):
    # Get Reference String: Acquired from perpetual powers of Tau
    # https://github.com/privacy-scaling-explorations/perpetualpowersoftau
    settings = json.load(open(settingsPath))
    srsPath = "./srs/" + str(settings['run_args']['logrows']) + ".srs"
    if os.path.isfile(srsPath) or ezkl.get_srs(srsPath, settingsPath):
        return srsPath
    return ""

def genWitness(dataPath, compiledModelPath, witnessPath):
    if not ezkl.gen_witness(dataPath, compiledModelPath, witnessPath):
        return False
    return True

def zkSetup(compiledModelPath, vkPath, pkPath, srsPath):
    if not ezkl.setup(compiledModelPath, vkPath, pkPath, srsPath):
        return False
    return True

def zkProve(witnessPath, compiledModelPath, pkPath, proofPath, srsPath, proofStrategy):
    try:
        ezkl.mock(witnessPath, compiledModelPath)
    except:
        return False
    if not ezkl.prove(witnessPath, compiledModelPath, pkPath, proofPath, proofStrategy, srsPath):
        return False
    return True

def zkVerify(proofPath, settingsPath, vkPath, srsPath):
    if not ezkl.verify(proofPath, settingsPath, vkPath, srsPath):
        return False
    return True

def cleanUp(paths):
    for p in paths:
        os.system("rm " + p)

def writeInput(modelInput, txHash):
    params = json.loads(modelInput)
    data = dict(input_shapes=utils.getShape(params), input_data=params)
    json.dump(data, open("./scratch/" + txHash + ".input", 'w'))
    return

