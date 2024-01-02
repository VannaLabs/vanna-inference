from diffusers import AutoPipelineForText2Image
import torch
import io
import base64

class PipelineManager:
	
	def __init__(self):
		return

	def infer(self, seed, pipelineName, modelHash, inputs):
		if pipelineName == "AutoPipelineForText2Image":
			pipe = AutoPipelineForText2Image.from_pretrained(modelHash, torch_dtype=torch.float32, variant="fp16")
			return self.encodeImage(pipe(prompt=inputs, num_inference_steps=1, guidance_scale=0.0).images[0])
		else:
			return bytes()

	def encodeImage(self, image):
		buffer = io.BytesIO()
		image.save(buffer, format="JPEG")
		image_bytes = buffer.getvalue()
		return base64.b64encode(image_bytes)
