import pdfplumber
import re
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Chargement du modèle une seule fois
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

SKILLS_DATABASE = [
    "python", "javascript", "java", "c++", "c#", "php", "typescript",
    "react", "vue", "angular", "html", "css", "tailwind", "bootstrap",
    "next.js", "jquery", "sass", "django", "flask", "fastapi", "node.js",
    "express", "spring", "laravel", "postgresql", "mysql", "mongodb",
    "redis", "sqlite", "docker", "kubernetes", "aws", "azure", "git",
    "linux", "nginx", "jenkins", "machine learning", "deep learning",
    "nlp", "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
    "power bi", "tableau", "agile", "scrum", "rest api", "graphql",
    "sql", "odoo", "sap", "excel", "word",
]


def extract_text_from_pdf(file_path):
    """Lit un PDF et retourne le texte brut."""
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Erreur lecture PDF: {e}")
    return text.strip()


def extract_skills(text):
    """Cherche les compétences connues dans le texte du CV."""
    text_lower = text.lower()
    found_skills = []
    for skill in SKILLS_DATABASE:
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, text_lower):
            found_skills.append(skill.title())
    return list(set(found_skills))


def compute_match_score(cv_text, job_description, required_skills):
    """
    Calcule le score de matching entre CV et offre.
    60% similarité sémantique + 40% compétences matchées.
    """
    if not cv_text or not job_description:
        return 0.0, []

    # Similarité sémantique
    try:
        vectors = model.encode([cv_text[:1000], job_description[:1000]])
        semantic_score = float(cosine_similarity([vectors[0]], [vectors[1]])[0][0]) * 100
    except Exception as e:
        print(f"Erreur vectorisation: {e}")
        semantic_score = 0.0

    # Compétences matchées
    cv_skills = extract_skills(cv_text)
    if required_skills:
        req_lower = [s.lower().strip() for s in required_skills]
        cv_lower = [s.lower().strip() for s in cv_skills]
        matched = sum(1 for skill in req_lower if skill in cv_lower)
        skills_score = (matched / len(req_lower)) * 100
    else:
        skills_score = semantic_score

    # Score final pondéré
    final_score = round(min((semantic_score * 0.6) + (skills_score * 0.4), 100.0), 1)
    return final_score, cv_skills


def analyze_application(application):
    """
    Fonction principale — analyse une candidature Django.
    Retourne (score, skills).
    """
    try:
        cv_path = application.cv.path
        cv_text = extract_text_from_pdf(cv_path)

        if not cv_text:
            print("⚠️ PDF vide ou illisible")
            return 0.0, []

        job_text = application.job_offer.description
        required_skills = application.job_offer.required_skills

        score, skills = compute_match_score(cv_text, job_text, required_skills)
        print(f"✅ Score calculé: {score}% | Skills: {skills}")
        return score, skills

    except Exception as e:
        print(f"❌ Erreur analyze_application: {e}")
        return 0.0, []