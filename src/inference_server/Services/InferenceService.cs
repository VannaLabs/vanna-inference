using Grpc.Core;
using Microsoft.ML.OnnxRuntime;
using Microsoft.ML.OnnxRuntime.Tensors;
using System.Text;

namespace inference_server.Services;

/**
Longshot TODO Items:
(1) Implement RLP encoding and decoding for inputs / outputs
(2) Create flexible byte array interface for RPC (in conjunction with RLP)
(3) Handle ONNX file-type metadata for input/output preprocessing or postprocessing
*/

public class InferenceService : Inference.InferenceBase
{
    private readonly ILogger<InferenceService> _logger;
    private static string signer;
    public InferenceService(ILogger<InferenceService> logger)
    {
        _logger = logger;
        signer = "0x83FFe2cbe305cCD48836b64726BdfD1fB643A13a";
    }

    public override Task<InferenceResult> RunInference(InferenceParameters request, ServerCallContext context)
    {
        string result = ONNXInference(request.ModelHash, request.ModelInput);
        string sign = nodeJSService.InvokeFromFileAsync<Result>("./js/eas/attest.js", args: new[] { request.ModelHash, request.ModelInput, result, signer })?.Message;

        return Task.FromResult(new InferenceResult
        {
            Tx = sign,
            Node = signer,
            Value = result
        });
    }

    public string ONNXInference(string hash, string input) 
    {
        // Generalized
        string modelPath = "./models/" + hash + ".onnx";
        var inferenceSession = new InferenceSession(modelPath);
        List<NamedOnnxValue> inferenceParams;

        // Flexible but need to be made generic
        Tensor<float> inputTensor;
        float[][] input2d;

        switch(hash) {
            case "LinearTest":
                input2d = parse2DInput(input);
                inputTensor = new DenseTensor<float>(new[] { input2d.Count(), input2d[0].Count() });
                for (int x = 0; x < input2d.Count(); x++) {
                    for (int y = 0; y < input2d[0].Count(); y++) {
                        inputTensor[x, y] = input2d[x][y];
                    }
                }
                inferenceParams = new List<NamedOnnxValue>() {
                    NamedOnnxValue.CreateFromTensor<float>("float_input", inputTensor)
                };
                return parseFloatResult(inferenceSession.Run(inferenceParams).ToList().Last());
            
            case "Volatility":
                input2d = parse2DInput(input);
                inferenceParams = new List<NamedOnnxValue>();
                string[] featureNames = new string[] {"vol_1","vol_2","vol_3","vol_4","vol_5"};
                for (int x = 0; x < input2d.Count(); x++) {
                    for (int y = 0; y < input2d[0].Count(); y++) {
                        inputTensor = new DenseTensor<float>(new[] { 1, 1 });
                        inputTensor[0, 0] = input2d[x][y];
                        inferenceParams.Add(NamedOnnxValue.CreateFromTensor<float>(featureNames[inferenceParams.Count()], inputTensor));
                    }
                }
                return parseFloatResult(inferenceSession.Run(inferenceParams).ToList().Last());

            default:
                return "Invalid Result";
        }
    }

    public string parseFloatResult(DisposableNamedOnnxValue results) {
        List<float> resultList = ((results.Value as IEnumerable<float>).ToList());
        if (resultList.Count > 1) {
            StringBuilder sb = new StringBuilder("[");
            for (int i = 0; i < resultList.Count; i++) {
                sb.Append(resultList[i]);
                if (i < resultList.Count-1) {
                    sb.Append(",");
                }
            }
            sb.Append("]");
            return sb.ToString();
        }
        return resultList[0].ToString();
    }

    public float[] parse1DInput(string input) {   
        return System.Text.Json.JsonSerializer.Deserialize<float[]>(input);
    }

    public float[][] parse2DInput(string input) {
        return System.Text.Json.JsonSerializer.Deserialize<float[][]>(input);
    }
}
