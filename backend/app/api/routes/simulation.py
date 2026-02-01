"""
Simulation routes for testing without Gemini/ArXiv.
Returns canned podcast (AI development) and canned Q&A answers.
"""

import random
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/simulation", tags=["Simulation"])

# Inlined so the endpoint never touches the filesystem (avoids path/timeout issues)
AI_DEVELOPMENT_PODCAST = {
    "metadata": {
        "title": "AI Development: From Theory to Practice",
        "summary": "A guided tour of modern AI development—large language models, training pipelines, and responsible deployment.",
        "sources_analyzed": 4,
        "estimated_duration_minutes": 12,
        "primary_topics": ["LLMs", "training", "deployment", "ethics", "AI safety"],
        "voices": {"host": "host_voice_id", "expert": "expert_voice_id"},
    },
    "segments": [
        {
            "id": 1,
            "topic_label": "Introduction",
            "dialogue": [
                {"speaker": "host", "text": "Welcome to PodAsk. Today we're talking AI development—how models are built, trained, and shipped. What's the landscape look like right now?"},
                {"speaker": "expert", "text": "We're past the 'it might work' phase. LLMs are in production everywhere. The real questions now are scale, cost, and how to train and deploy responsibly."},
            ],
            "key_terms": ["LLM", "training", "deployment"],
            "difficulty_level": "beginner",
            "source_reference": "Overview",
            "is_interruptible": True,
            "transition_to_question": "Any questions before we dive in?",
            "resume_phrase": "Let's get into how these models are actually trained.",
        },
        {
            "id": 2,
            "topic_label": "Training pipelines",
            "dialogue": [
                {"speaker": "host", "text": "Walk us through a typical training pipeline. What does 'training' actually mean for a big model?"},
                {"speaker": "expert", "text": "You have data—text or multimodal—then you run a massive optimization loop. The model adjusts billions of parameters to predict the next token. It's compute-heavy and data quality matters as much as size."},
            ],
            "key_terms": ["training", "parameters", "tokens", "compute"],
            "difficulty_level": "intermediate",
            "source_reference": "Paper_01_Training",
            "is_interruptible": True,
            "transition_to_question": "Questions on the training process?",
            "resume_phrase": "Now, what about after training—deployment?",
        },
        {
            "id": 3,
            "topic_label": "Deployment and scaling",
            "dialogue": [
                {"speaker": "host", "text": "So the model is trained. How do teams actually ship it?"},
                {"speaker": "expert", "text": "Inference is a different beast. You need batching, caching, and often smaller or distilled models for latency. Many companies use APIs from OpenAI, Anthropic, or self-host with vLLM, TGI, or similar."},
            ],
            "key_terms": ["inference", "latency", "API", "vLLM"],
            "difficulty_level": "intermediate",
            "source_reference": "Paper_02_Deployment",
            "is_interruptible": True,
            "transition_to_question": "Anything unclear about deployment?",
            "resume_phrase": "Let's touch on safety and ethics.",
        },
        {
            "id": 4,
            "topic_label": "Safety and ethics",
            "dialogue": [
                {"speaker": "host", "text": "What should developers keep in mind around safety and ethics?"},
                {"speaker": "expert", "text": "Alignment—making the model do what we want—and robustness. Red-teaming, evals, and clear use policies. It's not optional anymore; regulators and users expect it."},
            ],
            "key_terms": ["alignment", "red-teaming", "evals", "ethics"],
            "difficulty_level": "beginner",
            "source_reference": "Paper_03_Safety",
            "is_interruptible": True,
            "transition_to_question": "Questions on safety or ethics?",
            "resume_phrase": "We'll wrap with a quick recap.",
        },
    ],
}


# Canned answers for "AI development" topic (simulated research)
AI_DEVELOPMENT_ANSWERS = [
    {
        "answer_dialogue": [
            {"speaker": "host", "text": "Good question. Let me hand that to our expert."},
            {"speaker": "expert", "text": "In AI development, training means feeding the model huge amounts of data and adjusting billions of parameters so it learns patterns. The more quality data and compute you have, the better the model can predict—whether that's the next word or the next frame in a video."},
        ],
    },
    {
        "answer_dialogue": [
            {"speaker": "host", "text": "We get that one a lot."},
            {"speaker": "expert", "text": "Deployment is different from training. You need low latency and high throughput. Teams use inference APIs from providers like OpenAI or Anthropic, or self-host with engines like vLLM or TensorRT-LLM. Batching and caching are key to keeping costs down."},
        ],
    },
    {
        "answer_dialogue": [
            {"speaker": "host", "text": "Important topic."},
            {"speaker": "expert", "text": "Safety in AI development means alignment—making sure the model does what we intend—and robustness against misuse. That includes red-teaming, evals, and clear policies. Regulators and users increasingly expect this to be built in from the start."},
        ],
    },
    {
        "answer_dialogue": [
            {"speaker": "host", "text": "Short version coming up."},
            {"speaker": "expert", "text": "LLMs are large neural networks trained on text to predict the next token. They're used for chat, code, and many other tasks. Development involves curating data, scaling training, and then deploying with the right latency and cost trade-offs."},
        ],
    },
    {
        "answer_dialogue": [
            {"speaker": "host", "text": "Let's clarify."},
            {"speaker": "expert", "text": "Parameters are the weights the model learns during training. A model with 7 billion parameters has 7 billion numbers that get updated. More parameters usually mean more capacity, but you also need more data and compute to train them well."},
        ],
    },
    {
        "answer_dialogue": [
            {"speaker": "host", "text": "Good one."},
            {"speaker": "expert", "text": "Ethics in AI development covers fairness, transparency, and accountability. Teams do bias audits, document limitations, and set clear use policies. It's not just compliance—users and partners expect responsible development and deployment."},
        ],
    },
    {
        "answer_dialogue": [
            {"speaker": "host", "text": "Here's the takeaway."},
            {"speaker": "expert", "text": "AI development today is about data quality, scale, and responsible deployment. The theory is one thing; shipping models that are safe, useful, and cost-effective is where most of the work happens."},
        ],
    },
]


class SimulateAnswerRequest(BaseModel):
    question: str


@router.get("/ping")
async def simulation_ping():
    """Quick connectivity check; returns immediately."""
    return {"ok": True, "simulation": "ready"}


@router.get("/podcast")
async def get_simulation_podcast():
    """
    Return the AI development podcast JSON for simulation.
    Inlined so no file I/O — returns immediately.
    """
    return AI_DEVELOPMENT_PODCAST


@router.post("/answer")
async def simulate_answer(request: SimulateAnswerRequest):
    """
    Simulate "research" and return a canned answer for the AI development topic.
    Picks an answer by keyword match or randomly. No Gemini required.
    """
    q = (request.question or "").lower()
    # Prefer answer that matches question topic
    for entry in AI_DEVELOPMENT_ANSWERS:
        dialogue_text = " ".join(line["text"] for line in entry["answer_dialogue"]).lower()
        if any(term in q for term in ["train", "training", "parameter", "deploy", "safety", "ethic", "llm", "model", "scale"]):
            if "train" in q and "train" in dialogue_text:
                return entry
            if "deploy" in q and "deploy" in dialogue_text:
                return entry
            if "safety" in q or "ethic" in q:
                if "safety" in dialogue_text or "ethic" in dialogue_text:
                    return entry
            if "llm" in q or "model" in q:
                return entry
    # Default: random canned answer
    return random.choice(AI_DEVELOPMENT_ANSWERS)
