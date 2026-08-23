"""Known skills database for resume extraction and matching."""

# Categories map to job-market taxonomy used in matching (Phase 3)
SKILL_CATEGORIES: dict[str, list[str]] = {
    "language": [
        "python", "java", "javascript", "typescript", "c++", "c#", "go", "golang",
        "rust", "scala", "kotlin", "ruby", "php", "swift", "r", "sql", "html", "css",
    ],
    "testing": [
        "selenium", "testng", "test automation", "api testing", "testing",
    ],
    "framework": [
        "react", "next.js", "nextjs", "vue", "angular", "django", "flask", "fastapi",
        "spring", "spring boot", "express", "node.js", "nodejs", "pytorch", "tensorflow",
        "keras", "scikit-learn", "sklearn", "pandas", "numpy", "langchain", "langgraph",
        "huggingface", "transformers", "opencv", "mediapipe",
    ],
    "database": [
        "postgresql", "postgres", "mysql", "mongodb", "redis", "elasticsearch",
        "sqlite", "dynamodb", "firestore", "supabase", "neo4j", "cassandra",
    ],
    "cloud": [
        "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "k8s",
        "terraform", "ci/cd", "github actions", "jenkins", "mlflow", "kubeflow",
    ],
    "ai_ml": [
        "machine learning", "deep learning", "nlp", "natural language processing",
        "computer vision", "rag", "retrieval augmented generation", "llm",
        "large language model", "generative ai", "genai", "embeddings",
        "vector database", "fine-tuning", "prompt engineering", "agents",
        "reinforcement learning", "neural networks", "transformers",
        "sentence transformers", "faiss", "vector search",
    ],
    "tool": [
        "git", "github", "gitlab", "jira", "confluence", "figma", "postman",
        "vscode", "linux", "bash", "nginx", "apache", "cloudinary", "firebase",
        "ollama", "jupyter", "notebook",
        "excel", "powerpoint", "tableau", "statistics", "data visualization",
        "infrastructure automation", "monitoring", "cloud platforms",
        "configuration management", "containerization", "continuous integration",
        "continuous deployment", "rest apis",
    ],
}

# Flat lookup: normalized skill -> category
SKILL_LOOKUP: dict[str, str] = {}
for category, skills in SKILL_CATEGORIES.items():
    for skill in skills:
        SKILL_LOOKUP[skill.lower()] = category

# Aliases map variant names to canonical form for matching
SKILL_ALIASES: dict[str, str] = {
    "nodejs": "node.js",
    "nextjs": "next.js",
    "postgres": "postgresql",
    "sklearn": "scikit-learn",
    "golang": "go",
    "k8s": "kubernetes",
    "genai": "generative ai",
    "cv": "computer vision",
    "ml": "machine learning",
    "dl": "deep learning",
    "rest api": "rest apis",
    "rest": "rest apis",
}


def get_all_skills_flat() -> list[str]:
    skills = set()
    for skill_list in SKILL_CATEGORIES.values():
        skills.update(skill_list)
    return sorted(skills)
