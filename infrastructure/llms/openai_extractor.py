import instructor
from openai import OpenAI

from application.interfaces import AIExtractionService
from domain.compass import ContextCompass


class InstructorAIExtractor(AIExtractionService):
    def __init__(self, api_key: str):
        self.client = instructor.from_openai(OpenAI(api_key=api_key))

    def extract_knowledge(self, code_snippets: dict) -> ContextCompass:
        prompt = f"""
        You are a senior principal engineer analyzing a code module. 
        Read the following files and extract the tribal knowledge.
        Files: {code_snippets}
        """
        compass = self.client.chat.completions.create(
            model="gpt-4o",
            response_model=ContextCompass,
            max_retries=3,
            messages=[
                {"role": "system", "content": "Extract strict, concise documentation."},
                {"role": "user", "content": prompt},
            ],
        )

        return compass
