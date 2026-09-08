"""
Image generation using stabilityai/sd-turbo, 256x256 by default, 1 step.

License note (say this in the viva if asked): SD-Turbo is under the
Stability AI Community/Research License - free to use for this academic
project, but non-commercial. It is also gated on Hugging Face: whoever
runs this needs a free HF account, to have clicked "accept" on the model
page, and to have run `huggingface-cli login` once before first download.

Runs in a background thread from the Flask route so it never blocks the
text response (see app/main.py /image_status/<session_id>).

Resolution note: the brief's spec is 512x512, but testing on the target
laptop (Intel i3, 3.77GB RAM total) showed the VAE-decode step segfaulting
at 512x512 -- almost certainly a failed native memory allocation under
memory pressure rather than a code bug (it crashed at the same point
regardless of thread count). Attention/VAE slicing and a default of
256x256 substantially cut peak memory; raise IMAGE_SIZE back to 512 only
on a machine with more headroom.
"""

import gc

import torch
from diffusers import AutoPipelineForText2Image

_MODEL_NAME = "stabilityai/sd-turbo"
IMAGE_SIZE = 256


class ImageGenerator:
    def __init__(self):
        self._pipe = AutoPipelineForText2Image.from_pretrained(
            _MODEL_NAME, torch_dtype=torch.float32
        )
        self._pipe.to("cpu")
        # Cuts peak memory during the UNet and VAE-decode steps by
        # processing attention/VAE tiles sequentially instead of all at
        # once -- the difference between segfaulting and completing on a
        # low-RAM machine.
        self._pipe.enable_attention_slicing()
        self._pipe.enable_vae_slicing()

    def generate(self, prompt: str, output_path: str, num_inference_steps: int = 1,
                 size: int = IMAGE_SIZE) -> str:
        image = self._pipe(
            prompt=prompt,
            num_inference_steps=num_inference_steps,
            guidance_scale=0.0,  # SD-Turbo is trained for guidance_scale=0
            height=size,
            width=size,
        ).images[0]
        image.save(output_path)
        return output_path

    def unload(self):
        del self._pipe
        gc.collect()


def build_image_prompt(case_frame, technique: dict) -> str:
    """
    Turns the case frame + chosen technique into a short, calm, non-literal
    illustrative prompt (avoids depicting distressing scenes literally).
    """
    return (
        f"A calm, gentle, hopeful illustration representing moving from {case_frame.core_emotion or 'worry'} "
        f"toward {technique['name'].lower()}, soft colors, minimalist, digital art, no text, no words"
    )
