"""Keep recent chat turns and rewrite follow-ups before retrieval."""

from __future__ import annotations

from mf_faq.config import GROQ_API_KEY, GROQ_MODEL, MEMORY_TURNS

_REWRITE_SYSTEM = (
    "You rewrite a follow-up into one standalone question. "
    "Use the conversation only to resolve references such as it, its, that, this, and the fund. "
    "Name the scheme from the earlier turns. "
    "If the user asks about fees, charges, or costs, ask for the expense ratio. "
    "If the question already names the scheme and the fact, return it unchanged. "
    "Do not answer the question. Output only the rewritten question on one line."
)


class Memory:
    """The last few user and assistant messages for one chat session."""

    def __init__(self, limit: int = MEMORY_TURNS) -> None:
        self.limit = limit
        self.messages: list[dict[str, str]] = []

    def add(self, role: str, content: str) -> None:
        text = " ".join(content.split())
        if not text:
            return
        self.messages.append({"role": role, "content": text})
        extra = len(self.messages) - self.limit
        if extra > 0:
            self.messages = self.messages[extra:]

    def rewrite(self, question: str) -> str:
        """Return a standalone question. The original is kept when there is no history."""
        if not self.messages or not GROQ_API_KEY:
            return question
        from groq import Groq

        history = "\n".join(f"{item['role']}: {item['content']}" for item in self.messages)
        try:
            client = Groq(api_key=GROQ_API_KEY)
            completion = client.chat.completions.create(
                model=GROQ_MODEL,
                temperature=0,
                messages=[
                    {"role": "system", "content": _REWRITE_SYSTEM},
                    {
                        "role": "user",
                        "content": f"Conversation:\n{history}\n\nFollow-up: {question}",
                    },
                ],
            )
            raw = (completion.choices[0].message.content or "").strip()
        except Exception:
            return question
        line = next((part.strip() for part in raw.splitlines() if part.strip()), "")
        line = line.strip("\"'")
        return line or question
