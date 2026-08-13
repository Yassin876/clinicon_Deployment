"""
وصلة الـ LLM — Qwen يتحمّل مباشرة بـ 4-bit NF4 quantization + FP16 compute.
يُحمّل الموديل مرة واحدة فقط على CUDA. يعمل على T500 4GB VRAM.
"""
import time
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import re
from . import config

# ──────────────────────────────────────────────────────────────
# Qwen model name (can override via env: QWEN_MODEL)
# ──────────────────────────────────────────────────────────────
import os
QWEN_MODEL_NAME = os.getenv("QWEN_MODEL", "Qwen/Qwen2.5-1.5B-Instruct")

# Singletons — loaded once, reused for every call
_tokenizer = None
_model = None


def _load_model():
    global _tokenizer, _model
    if _model is not None:
        return

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[LLM] Loading Qwen model: {QWEN_MODEL_NAME} on {device.upper()}")

    bnb_config = None
    if device == "cuda":
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",           # NF4 quantization
            bnb_4bit_compute_dtype=torch.float16, # FP16 computation
            bnb_4bit_use_double_quant=True,       # double quantization for extra memory saving
        )
        print("[LLM] Using 4-bit NF4 quantization + FP16 compute (BitsAndBytesConfig)")

    _tokenizer = AutoTokenizer.from_pretrained(
        QWEN_MODEL_NAME,
        trust_remote_code=True,
    )

    _model = AutoModelForCausalLM.from_pretrained(
        QWEN_MODEL_NAME,
        quantization_config=bnb_config,
        device_map="auto" if device == "cuda" else None,
        torch_dtype=torch.float16 if device == "cuda" and bnb_config is None else None,
        trust_remote_code=True,
    )

    _model.eval()
    print(f"[LLM] Qwen ready | dtype={'4-bit NF4 + FP16' if bnb_config else 'FP32 (CPU)'}")


def ask_llm(prompt: str) -> str:
    """Generate a response using local Qwen and measure Generation Time."""
    _load_model()
    start_time = time.time()

    messages = [{"role": "user", "content": prompt}]
    text = _tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    inputs = _tokenizer([text], return_tensors="pt")
    if next(_model.parameters()).is_cuda:
        inputs = {k: v.to("cuda") for k, v in inputs.items()}

    with torch.inference_mode():
        output_ids = _model.generate(
            **inputs,
            max_new_tokens=256,
            temperature=0.1,
            do_sample=True,
            pad_token_id=_tokenizer.eos_token_id,
        )

    elapsed_generation = time.time() - start_time
    print(f"⏱️ [Metric] Generation Time (Qwen LLM): {elapsed_generation:.4f} seconds")

    # Decode only the newly generated tokens (not the input)
    generated = output_ids[0][inputs["input_ids"].shape[-1]:]
    response = _tokenizer.decode(generated, skip_special_tokens=True)

    # Strip Qwen3 thinking tags if present
    response = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL)
    return response.strip()
