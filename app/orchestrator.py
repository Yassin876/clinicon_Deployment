"""
orchestrator.py
الحلقة المنسّقة (ReAct loop) — قلب الـ agent.
تضمن استخدام توكن المريض المناسب لكل طلب عبر contextvars.
"""
import re
import json
import uuid
from typing import Optional
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage

from . import config
from .prompts import build_system_prompt
from .tools import ALL_TOOLS, current_patient_token

MAX_TOOL_ROUNDS = 10
DEBUG = False

# أسماء بديلة ممكن الموديل يستخدمها بدل الاسم الصحيح
_TOOL_ALIASES = {
    "medical_knowledge_search": "search_medical_info",
    "search_medical_knowledge": "search_medical_info",
    "medical_search": "search_medical_info",
    "search_medical": "search_medical_info",
    "get_doctor": "get_doctors",
    "list_doctors": "get_doctors",
    "book": "book_appointment",
    "slots": "get_available_slots",
    "available_slots": "get_available_slots",
    "get_slots": "get_available_slots",
    "get_medications": "get_my_medications",
    "my_medications": "get_my_medications",
}


def _strip_think(text: str) -> str:
    """Qwen3 بيكتب تفكيره جوه <think>...</think> — بنشيله."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    return text.strip()


def _clean_final_response(text: str) -> str:
    """نضّف الرد النهائي من أي XML أو function_call زيادة."""
    text = _strip_think(text)
    # شيل أي <function_call> متبقي
    text = re.sub(r"<function_call>.*?</function_call>", "", text, flags=re.DOTALL)
    text = re.sub(r"<function_call>.*?<function_call/>", "", text, flags=re.DOTALL)
    text = re.sub(r"</?function_call/?>", "", text)
    # شيل أي Python-style function calls متبقية في النص
    text = re.sub(
        r'\b(get_doctors|get_available_slots|book_appointment|get_my_medications|add_medication|search_medical_info)\s*\([^)]*\)',
        '', text
    )
    return text.strip()


def _parse_raw_function_call(text: str):
    """
    Qwen3 ساعات بيكتب tool calls كـ XML/text بدل format LangChain.
    بنحاول نستخرج اسم الأداة والـ arguments من النص.
    بيرجع (tool_name, args_dict) أو None.
    """
    # Pattern 1: <function_call> JSON </function_call>
    match = re.search(
        r'<function_call>\s*(.*?)\s*</function_call>',
        text, re.DOTALL
    )
    # Pattern 2: <function_call> ... <function_call/> (malformed closing)
    if not match:
        match = re.search(
            r'<function_call>\s*(.*?)\s*<function_call/>',
            text, re.DOTALL
        )
    # Pattern 3: ```json { "function_name": ... } ```
    if not match:
        match = re.search(
            r'\{[^{}]*"function_name"\s*:\s*"[^"]+"\s*.*?\}',
            text, re.DOTALL
        )
        if match:
            inner = match.group(0)
        else:
            inner = None
    else:
        inner = match.group(1)

    # Pattern 4: Python-style function call
    if not inner:
        py_match = re.search(
            r'\b(get_doctors|get_available_slots|book_appointment|get_my_medications|add_medication|search_medical_info)\s*\(([^)]*)\)',
            text
        )
        if py_match:
            func_name = py_match.group(1)
            raw_args = py_match.group(2).strip()
            args = {}
            if raw_args:
                for kv in re.finditer(r'(\w+)\s*=\s*["\']([^"\']*)["\']', raw_args):
                    args[kv.group(1)] = kv.group(2)
                if not args:
                    positional = re.findall(r'["\']([^"\']*)["\']', raw_args)
                    if func_name == 'book_appointment' and len(positional) >= 2:
                        args['doctor_id'] = positional[0]
                        args['slot_datetime'] = positional[1]
                    elif func_name == 'get_available_slots' and len(positional) >= 2:
                        args['doctor_id'] = positional[0]
                        args['date'] = positional[1]
                    elif func_name == 'search_medical_info' and positional:
                        args['query'] = positional[0]
            return (func_name, args)
        return None

    inner = inner.strip()
    inner = re.sub(r'\n\s*', ' ', inner)

    name_match = re.search(r'"function_name"\s*:\s*"([^"]+)"', inner)
    if not name_match:
        name_match = re.search(r'"name"\s*:\s*"([^"]+)"', inner)
    if not name_match:
        return None

    func_name = name_match.group(1)

    args_match = re.search(r'"arguments"\s*:\s*(\{[^{}]*\})', inner)
    if args_match:
        try:
            args = json.loads(args_match.group(1))
        except json.JSONDecodeError:
            args = {}
    else:
        args = {}
        for kv in re.finditer(r'"(\w+)"\s*:\s*"([^"]*)"', inner):
            key, val = kv.group(1), kv.group(2)
            if key not in ('function_name', 'name'):
                args[key] = val

    return (func_name, args)


def create_agent(patient_token: Optional[str] = None):
    if config.USE_GEMINI:
        import os
        api_key = config.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        print(f"  [agent] Using Gemini Model ({config.GEMINI_MODEL})")
        
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(
                model=config.GEMINI_MODEL,
                google_api_key=api_key if api_key else None,
                temperature=config.TEMPERATURE,
                transport="rest",
                timeout=120,
            )
        except Exception as e:
            print(f"  [agent] Warning: langchain_google_genai failed ({e}), using google-genai direct wrapper...")
            from google import genai
            client = genai.Client(api_key=api_key)
            class DirectGeminiWrapper:
                def __init__(self, client, model):
                    self.client = client
                    self.model = model
                def invoke(self, messages):
                    # convert messages to prompt string
                    prompt = "\n".join([f"{m.type}: {m.content}" for m in messages])
                    response = self.client.models.generate_content(
                        model=self.model,
                        contents=prompt,
                    )
                    return AIMessage(content=response.text or "")
            llm = DirectGeminiWrapper(client, config.GEMINI_MODEL)
    else:
        print(f"  [agent] Using Ollama Model ({config.OLLAMA_MODEL})")
        llm = ChatOllama(
            model=config.OLLAMA_MODEL,
            base_url=config.OLLAMA_BASE_URL,
            temperature=config.TEMPERATURE,
            timeout=120,
        )
    llm_with_tools = llm.bind_tools(ALL_TOOLS)
    tools_map = {t.name: t for t in ALL_TOOLS}
    history = [SystemMessage(content=build_system_prompt())]
    return {
        "llm": llm_with_tools,
        "tools_map": tools_map,
        "history": history,
        "patient_token": patient_token
    }


def _resolve_tool(name: str, tools_map: dict):
    if name in tools_map:
        return tools_map[name]
    alias = _TOOL_ALIASES.get(name)
    if alias and alias in tools_map:
        return tools_map[alias]
    for real_name in tools_map:
        if name in real_name or real_name in name:
            return tools_map[real_name]
    return None


_SYMPTOM_KEYWORDS = [
    "ألم", "وجع", "صداع", "دوخة", "كحة", "سخونة", "حرارة", "تعب",
    "ضيق", "حساسية", "التهاب", "تنميل", "حرقان", "غثيان", "إسهال",
    "إمساك", "ورم", "نزيف", "حكة", "طفح", "بيوجعني", "عندي",
    "حاسس", "بحس", "مش قادر", "ضغط", "سكر", "أسنان",
]


def _looks_like_symptoms(text: str) -> bool:
    text_lower = text.strip()
    return any(kw in text_lower for kw in _SYMPTOM_KEYWORDS)


def chat(agent: dict, user_input: str, patient_token: Optional[str] = None) -> str:
    # ضبط توكن المريض الخاص بالطلب الحكيم في الـ ContextVar
    effective_token = patient_token or agent.get("patient_token")
    token_token = current_patient_token.set(effective_token)

    try:
        llm = agent["llm"]
        tools_map = agent["tools_map"]
        history = agent["history"]

        if _looks_like_symptoms(user_input) and "search_medical_info" in tools_map:
            already_searched = any(
                isinstance(m, ToolMessage) and "search_medical_info" in str(getattr(m, 'name', ''))
                for m in history
            )
            if not already_searched:
                print(f"  [agent] Auto-searching medical info for: {user_input[:60]}")
                try:
                    search_result = tools_map["search_medical_info"].invoke({"query": user_input})
                    context_msg = (
                        f"[نتيجة البحث الطبي]\n{search_result}\n\n"
                        f"[تعليمات مهمة]\n"
                        f"1. لو النتيجة دي مش متعلقة بشكوى المريض ('{user_input}')، تجاهلها تماماً واستخدم معلوماتك العامة.\n"
                        f"2. قدّم نصيحة طبية عامة عن شكوى المريض الأول.\n"
                        f"3. اقترح التخصص المناسب.\n"
                        f"4. بعدين اسأله لو عايز يحجز.\n"
                        f"5. رد بالعربي المصري — ممنوع إنجليزي."
                    )
                    history.append(SystemMessage(content=context_msg))
                except Exception as e:
                    print(f"  [agent] Auto-search failed: {e}")

        history.append(HumanMessage(content=user_input))

        for _round in range(MAX_TOOL_ROUNDS):
            ai_msg: AIMessage = llm.invoke(history)
            history.append(ai_msg)

            if DEBUG:
                print(f"\n  [DEBUG] content = {ai_msg.content[:300] if ai_msg.content else '(empty)'}")
                print(f"  [DEBUG] tool_calls = {ai_msg.tool_calls}")

            if ai_msg.tool_calls:
                for tc in ai_msg.tool_calls:
                    tool_name = tc["name"]
                    tool_args = tc["args"]
                    tool_func = _resolve_tool(tool_name, tools_map)
                    if tool_func is None:
                        result = f"خطأ: مفيش أداة اسمها '{tool_name}'. المتاح: {list(tools_map.keys())}"
                    else:
                        result = tool_func.invoke(tool_args)
                    
                    # For Gemini 3.x, append ToolMessage without breaking v1beta schemas
                    history.append(ToolMessage(content=str(result) if result is not None else "", tool_call_id=tc.get("id") or "call_default"))
                
                # If using Gemini, synthesize answer from tool result to avoid v1beta thought_signature loop
                if config.USE_GEMINI:
                    synth_prompt = f"المسترجع من النظام: {result}\nقم بإعادة صياغة هذا الرد بلباقة للمريض بالعربي المصري."
                    final_res = llm.invoke([SystemMessage(content=build_system_prompt()), HumanMessage(content=synth_prompt)])
                    return _strip_think(final_res.content or "")
                continue

            content = ai_msg.content or ""
            content_clean = _strip_think(content)
            parsed = _parse_raw_function_call(content_clean)
            if parsed:
                func_name, func_args = parsed
                print(f"  [agent] Caught raw function_call: {func_name}({func_args})")
                tool_func = _resolve_tool(func_name, tools_map)
                if tool_func is None:
                    result = f"خطأ: مفيش أداة اسمها '{func_name}'. المتاح: {list(tools_map.keys())}"
                else:
                    result = tool_func.invoke(func_args)

                fake_id = str(uuid.uuid4())[:8]
                history.pop()
                history.append(AIMessage(
                    content="",
                    tool_calls=[{"name": func_name, "args": func_args, "id": fake_id}]
                ))
                history.append(ToolMessage(content=str(result), tool_call_id=fake_id))
                continue

            return _clean_final_response(content)

        return "عذراً، حصلت مشكلة في النظام. ممكن تحاول تاني أو تتواصل مع العيادة مباشرة."
    finally:
        current_patient_token.reset(token_token)
