SKILL_OPTIONS = [
    {"key": "python", "label": "Python"},
    {"key": "java", "label": "Java"},
    {"key": "cpp", "label": "C++"},
    {"key": "sql", "label": "SQL"},
    {"key": "web_dev", "label": "Web Development"},
    {"key": "communication", "label": "Communication"},
    {"key": "aptitude", "label": "Aptitude"},
    {"key": "problem_solving", "label": "Problem Solving"},
    {"key": "cloud", "label": "Cloud"},
    {"key": "ai_ml", "label": "AI/ML"},
    {"key": "cybersecurity", "label": "Cybersecurity"},
    {"key": "data_structures", "label": "Data Structures"},
]

CAREER_DOMAINS = {
    "Software Development": {
        "description": "Build scalable applications, APIs, and products using modern software engineering practices.",
        "required_skills": ["python", "java", "cpp", "sql", "web_dev", "problem_solving", "data_structures"],
        "courses": ["DSA Mastery", "System Design Fundamentals", "API Development with Flask"],
        "roadmap": ["Strengthen DSA", "Build 2 production-grade projects", "Practice system design basics"],
        "keywords": ["oop", "algorithms", "backend", "api", "version control"],
    },
    "Data Science": {
        "description": "Analyze data, build predictive models, and communicate insights to stakeholders.",
        "required_skills": ["python", "sql", "ai_ml", "problem_solving", "aptitude", "communication"],
        "courses": ["Statistics for Data Science", "Machine Learning with scikit-learn", "Data Visualization"],
        "roadmap": ["Master Python and SQL", "Learn statistics and ML", "Create end-to-end data projects"],
        "keywords": ["statistics", "pandas", "numpy", "visualization", "modeling"],
    },
    "Cybersecurity": {
        "description": "Protect systems, applications, and networks from threats and vulnerabilities.",
        "required_skills": ["python", "cybersecurity", "problem_solving", "communication", "sql"],
        "courses": ["Network Security Essentials", "Ethical Hacking Basics", "Security Operations"],
        "roadmap": ["Learn networking fundamentals", "Practice threat analysis", "Study secure coding"],
        "keywords": ["risk", "threat", "encryption", "network", "security"],
    },
    "Cloud Computing": {
        "description": "Design, deploy, and maintain scalable cloud infrastructure and automation.",
        "required_skills": ["cloud", "python", "web_dev", "problem_solving", "communication"],
        "courses": ["AWS Fundamentals", "DevOps and CI/CD", "Cloud Architecture"],
        "roadmap": ["Understand virtualization and cloud models", "Deploy services", "Automate infrastructure"],
        "keywords": ["aws", "azure", "docker", "kubernetes", "ci/cd"],
    },
    "AI Engineer": {
        "description": "Build intelligent systems with machine learning, deep learning, and automation.",
        "required_skills": ["python", "ai_ml", "problem_solving", "data_structures", "sql"],
        "courses": ["ML Algorithms", "Deep Learning Foundations", "MLOps Essentials"],
        "roadmap": ["Study ML math basics", "Implement models", "Deploy an AI project"],
        "keywords": ["models", "training", "neural", "mlops", "deployment"],
    },
    "Full Stack Developer": {
        "description": "Develop full web solutions across frontend, backend, databases, and deployment.",
        "required_skills": ["python", "java", "sql", "web_dev", "problem_solving", "communication"],
        "courses": ["Frontend Mastery", "Backend APIs", "Database Design"],
        "roadmap": ["Build UI projects", "Practice backend integrations", "Deploy a full stack app"],
        "keywords": ["frontend", "backend", "database", "rest", "responsive"],
    },
    "DevOps Engineer": {
        "description": "Automate delivery pipelines, infrastructure, and operational reliability.",
        "required_skills": ["cloud", "python", "problem_solving", "communication", "sql"],
        "courses": ["Linux and Shell Scripting", "Docker and Kubernetes", "CI/CD Pipelines"],
        "roadmap": ["Learn Linux fundamentals", "Automate deployments", "Monitor systems"],
        "keywords": ["automation", "deployment", "monitoring", "containers", "pipelines"],
    },
    "UI/UX Developer": {
        "description": "Craft intuitive and visually pleasing product experiences for users.",
        "required_skills": ["web_dev", "communication", "problem_solving", "aptitude"],
        "courses": ["UI Design Principles", "Figma for Developers", "Front-End Interaction Design"],
        "roadmap": ["Study user journeys", "Practice responsive design", "Build interactive prototypes"],
        "keywords": ["design", "prototype", "ux", "accessibility", "interface"],
    },
}

JOB_DESCRIPTIONS = {
    "Software Development": "We need a software developer with strong problem solving, data structures, backend API knowledge, SQL, and modern coding practices.",
    "Data Science": "We are looking for a data scientist skilled in Python, SQL, statistics, machine learning, analysis, and communication.",
    "Cybersecurity": "The role requires network security, threat analysis, secure coding, incident response, and clear communication.",
    "Cloud Computing": "We need cloud engineers with knowledge of AWS, automation, containerization, CI/CD, and infrastructure design.",
    "AI Engineer": "This position focuses on machine learning, model training, deployment, Python, and experimentation.",
    "Full Stack Developer": "We need a full stack engineer comfortable with frontend UI, backend APIs, SQL databases, and deployment.",
    "DevOps Engineer": "The role involves automation, CI/CD, containers, monitoring, and Linux-based operational workflows.",
    "UI/UX Developer": "We are seeking a UI/UX developer with design thinking, responsive interface skills, communication, and user research awareness.",
}

INTERVIEW_QUESTION_BANK = {
    "technical": [
        {
            "question": "Explain the difference between a stack and a queue.",
            "keywords": ["stack", "queue", "lifo", "fifo"],
        },
        {
            "question": "What is normalization in a database and why is it important?",
            "keywords": ["normalization", "redundancy", "database", "design"],
        },
        {
            "question": "Describe how a REST API works.",
            "keywords": ["rest", "http", "endpoint", "json"],
        },
        {
            "question": "What is the purpose of machine learning model evaluation?",
            "keywords": ["accuracy", "precision", "recall", "evaluation"],
        },
    ],
    "hr": [
        {
            "question": "Tell me about a time you solved a difficult problem.",
            "keywords": ["problem", "solution", "team", "result"],
        },
        {
            "question": "Why should we hire you?",
            "keywords": ["skills", "value", "team", "learn"],
        },
        {
            "question": "How do you handle feedback from seniors or managers?",
            "keywords": ["feedback", "improve", "listen", "growth"],
        },
        {
            "question": "Where do you see yourself in three years?",
            "keywords": ["growth", "learning", "career", "goal"],
        },
    ],
}
