from infrastructure.ai.openai_extractor import InstructorAIExtractor
from infrastructure.storage.local_fs import LocalContextStorage, LocalFileSystemRepo

from application.use_cases import MapTribalKnowledgeUseCase


def main():
    code_repo = LocalFileSystemRepo(
        base_path=""
    )
    storage = LocalContextStorage(
        base_path=""
    )
    ai_service = InstructorAIExtractor(api_key="")

    use_case = MapTribalKnowledgeUseCase(
        code_repository=code_repo, ai_extraction_service=ai_service, storage=storage
    )

    print("Mapping tribal knowledge...")
    result = use_case.execute(module_path="src/payment_processor")
    print(f"Success! Found key patterns: {result.non_obvious_patterns[:50]}...")


if __name__ == "__main__":
    main()
