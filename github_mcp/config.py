"""
Configuration — GitHub MCP
===========================

Central source of truth for API URLs, tech stack keywords, output paths,
and repo filtering rules.

To adapt to different use cases, edit ONLY this file.
"""

from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────
# API Configuration
# ──────────────────────────────────────────────────────────────────────────

GRAPHQL_URL = "https://api.github.com/graphql"
REST_BASE_URL = "https://api.github.com"

# Request timeout in seconds
REQUEST_TIMEOUT = 30.0

# Max repos to fetch per page (GraphQL limit = 100, REST limit = 100)
REPOS_PER_PAGE = 100

# ──────────────────────────────────────────────────────────────────────────
# Output Configuration
# ──────────────────────────────────────────────────────────────────────────

DEFAULT_OUTPUT_DIR: Path = Path("md") / "github"
PROJECTS_SUBDIR = "projects"
SUMMARY_FILENAME = "projects_summary.md"

# ──────────────────────────────────────────────────────────────────────────
# Repo Filtering — auto-skip patterns
# ──────────────────────────────────────────────────────────────────────────

# Repo names matching these patterns (case-insensitive) are flagged as
# low-relevance during discovery. They are still returned but marked.
LOW_RELEVANCE_PATTERNS: list[str] = [
    ".github",           # profile README repo
    "config",            # dotfiles
    "dotfiles",
    "test",
    "hello-world",
    "tutorial",
    "learning",
    "course",
    "practice",
]

# ──────────────────────────────────────────────────────────────────────────
# Tech Stack Inference Keywords
# ──────────────────────────────────────────────────────────────────────────
# Matched against: repo topics, README text (lowercased), filenames
# Each entry: category → set of keywords

TECH_STACK_KEYWORDS: dict[str, dict[str, set[str]]] = {
    "Frontend": {
        "frameworks": {"react", "react.js", "reactjs", "next.js", "nextjs", "vue",
                       "vue.js", "vuejs", "angular", "svelte", "sveltekit",
                       "gatsby", "nuxt", "nuxtjs", "remix"},
        "libraries": {"tailwindcss", "tailwind", "bootstrap", "material-ui",
                      "chakra-ui", "styled-components", "sass", "scss"},
    },
    "Backend": {
        "frameworks": {"express", "express.js", "expressjs", "fastapi", "flask",
                       "django", "spring-boot", "springboot", "spring", "rails",
                       "ruby-on-rails", "gin", "fiber", "nestjs", "nest.js",
                       "koa", "hapi"},
        "libraries": {"node.js", "nodejs", "deno", "bun"},
    },
    "AI / ML": {
        "frameworks": {"tensorflow", "pytorch", "keras", "scikit-learn",
                       "sklearn", "huggingface", "transformers", "langchain",
                       "llamaindex", "openai", "groq", "ollama", "mlflow"},
        "concepts": {"machine-learning", "deep-learning", "nlp",
                     "natural-language-processing", "computer-vision",
                     "image-processing", "llm", "large-language-model",
                     "generative-ai", "chatbot", "rag", "fine-tuning"},
    },
    "Database": {
        "systems": {"mongodb", "mongoose", "postgresql", "postgres", "mysql",
                    "sqlite", "redis", "firebase", "firestore", "supabase",
                    "dynamodb", "cassandra", "neo4j", "elasticsearch",
                    "pinecone", "chromadb", "weaviate", "qdrant"},
    },
    "DevOps / Cloud": {
        "tools": {"docker", "kubernetes", "k8s", "terraform", "ansible",
                  "github-actions", "ci-cd", "jenkins", "aws", "gcp",
                  "azure", "vercel", "netlify", "heroku", "nginx"},
    },
    "Mobile": {
        "frameworks": {"react-native", "flutter", "swift", "kotlin",
                       "expo", "ionic", "xamarin"},
    },
}

# Files that signal specific tech stacks
TECH_INDICATOR_FILES: dict[str, str] = {
    "package.json": "Node.js",
    "requirements.txt": "Python",
    "pyproject.toml": "Python",
    "setup.py": "Python",
    "Pipfile": "Python",
    "Gemfile": "Ruby",
    "pom.xml": "Java / Maven",
    "build.gradle": "Java / Gradle",
    "go.mod": "Go",
    "Cargo.toml": "Rust",
    "composer.json": "PHP",
    "Dockerfile": "Docker",
    "docker-compose.yml": "Docker Compose",
    "docker-compose.yaml": "Docker Compose",
    ".env.example": "Environment Config",
    "Makefile": "Make",
    "tsconfig.json": "TypeScript",
    "next.config.js": "Next.js",
    "next.config.ts": "Next.js",
    "next.config.mjs": "Next.js",
    "vite.config.js": "Vite",
    "vite.config.ts": "Vite",
    "tailwind.config.js": "Tailwind CSS",
    "tailwind.config.ts": "Tailwind CSS",
    ".streamlit": "Streamlit",
    "app.py": "Python App",
    "manage.py": "Django",
}

# ──────────────────────────────────────────────────────────────────────────
# Domain Classification Keywords
# ──────────────────────────────────────────────────────────────────────────

DOMAIN_KEYWORDS: dict[str, set[str]] = {
    "AI / Machine Learning": {"machine-learning", "deep-learning", "nlp", "llm",
                               "ai", "ml", "tensorflow", "pytorch", "chatbot",
                               "computer-vision", "generative-ai"},
    "Web Development": {"react", "vue", "angular", "web", "frontend", "backend",
                        "full-stack", "fullstack", "mern", "nextjs", "api"},
    "Mobile Development": {"react-native", "flutter", "mobile", "android", "ios"},
    "Data Science": {"data-science", "data-analysis", "pandas", "visualization",
                     "jupyter", "matplotlib", "analytics"},
    "DevOps / Infrastructure": {"docker", "kubernetes", "ci-cd", "devops",
                                 "terraform", "cloud", "aws", "gcp"},
    "Automation / Tools": {"automation", "bot", "scraper", "cli", "tool",
                           "utility", "script"},
    "Security": {"security", "vulnerability", "encryption", "auth",
                 "authentication", "cybersecurity"},
}
