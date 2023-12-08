import ezkl
import zkml

modelName = "test.onnx"
transactionID = '123test'
proofStrategy = "single"
execDir = "scratch/"
modelPath = "models/" + modelName
compiledModelPath = modelPath + "_compiled"
settingsPath = execDir + transactionID + ".settings"
vkPath = execDir + transactionID + ".vk"
pkPath = execDir + transactionID + ".pk"
witnessPath = execDir + transactionID + ".witness"
dataPath = execDir + transactionID + ".input"
proof_path = execDir + transactionID + ".pf"
srsPath = zkml.getSrs(settingsPath)

if not ezkl.prove(witnessPath, compiledModelPath, pkPath, proof_path, srsPath, proofStrategy):
	print("failed")

print("success")