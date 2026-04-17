"""Local mock LLM used by the Day 12 production lab."""

from __future__ import annotations

import random
import time


MOCK_RESPONSES = {
    "default": [
        "This is a mock agent response. Replace it with a real provider when you are ready to integrate an external LLM.",
        "The production-ready agent received your question and answered through the mock model.",
        "The app is running with Redis-backed state and a mock answer generator.",
    ],
    "docker": [
        "Docker packages the service and its dependencies into a portable container image.",
    ],
    "deploy": [
        "Deployment is the process of shipping your application to a reachable environment and verifying it stays healthy.",
    ],
    "health": [
        "Health checks tell the platform whether the container is alive and ready to receive traffic.",
    ],
}


def ask(question: str, delay: float = 0.05) -> str:
    time.sleep(delay + random.uniform(0, 0.02))
    lowered = question.lower()
    for keyword, responses in MOCK_RESPONSES.items():
        if keyword in lowered:
            return random.choice(responses)
    return random.choice(MOCK_RESPONSES["default"])
