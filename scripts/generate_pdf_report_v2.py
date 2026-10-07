"""Script principal de génération et de compilation du rapport complet de PFA en PDF.

Projet : AI Market Intelligence (Marché Spot XAU/USD)
Conformité stricte aux audits factuels du dépôt local et aux 10 exigences méthodologiques.
"""

import os
import sys
import shutil
from pathlib import Path

# Ajouter la racine du projet et le dossier scripts au PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate

from report_sections.styles import get_academic_styles, NumberedCanvas
from report_sections.front_matter import get_front_matter_story
from report_sections.intro import get_intro_story
from report_sections.chapter1 import get_chapter1_story
from report_sections.chapter2 import get_chapter2_story
from report_sections.chapter3 import get_chapter3_story
from report_sections.chapter4 import get_chapter4_story
from report_sections.chapter5 import get_chapter5_story
from report_sections.chapter6 import get_chapter6_story
from report_sections.chapter7 import get_chapter7_story
from report_sections.chapter8 import get_chapter8_story
from report_sections.chapter9 import get_chapter9_story
from report_sections.conclusion import get_conclusion_story
from report_sections.bibliography import get_bibliography_story
from report_sections.annexes import get_annexes_story

def build_complete_pdf_report(target_pdf_path: str):
    """Compile et génère l'ensemble du document PDF académique."""
    print(f"[*] Initialisation de la compilation du rapport PFA vers : {target_pdf_path}")
    
    doc = SimpleDocTemplate(
        target_pdf_path,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm
    )

    styles = get_academic_styles()
    story = []

    print("[1/14] Génération des pages préliminaires (Garde, Dédicace, Résumés, Table des Matières)...")
    story.extend(get_front_matter_story(styles))

    print("[2/14] Génération de l'Introduction Générale...")
    story.extend(get_intro_story(styles))

    print("[3/14] Génération du Chapitre 1 (Contexte Général et Étude de l'Existant)...")
    story.extend(get_chapter1_story(styles))

    print("[4/14] Génération du Chapitre 2 (Analyse et Spécification des Besoins)...")
    story.extend(get_chapter2_story(styles))

    print("[5/14] Génération du Chapitre 3 (Analyse et Conception Système)...")
    story.extend(get_chapter3_story(styles))

    print("[6/14] Génération du Chapitre 4 (Acquisition et Préparation des Données de Marché)...")
    story.extend(get_chapter4_story(styles))

    print("[7/14] Génération du Chapitre 5 (Machine Learning et Prédiction Directionnelle)...")
    story.extend(get_chapter5_story(styles))

    print("[8/14] Génération du Chapitre 6 (Réalisation et Développement Applicatif)...")
    story.extend(get_chapter6_story(styles))

    print("[9/14] Génération du Chapitre 7 (Tests, Validation et Assurance Qualité)...")
    story.extend(get_chapter7_story(styles))

    print("[10/14] Génération du Chapitre 8 (Déploiement et DevOps)...")
    story.extend(get_chapter8_story(styles))

    print("[11/14] Génération du Chapitre 9 (Discussion Critique, Limites et Perspectives)...")
    story.extend(get_chapter9_story(styles))

    print("[12/14] Génération de la Conclusion Générale...")
    story.extend(get_conclusion_story(styles))

    print("[13/14] Génération de la Bibliographie et Webographie...")
    story.extend(get_bibliography_story(styles))

    print("[14/14] Génération des Annexes Techniques Exhaustives (PlantUML, API, Code, Features)...")
    story.extend(get_annexes_story(styles))

    print(f"[*] Assemblage du flux Platypus et génération du PDF via NumberedCanvas ({len(story)} éléments)...")
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[+] Succès : Rapport complet de PFA généré avec succès dans : {target_pdf_path}")

if __name__ == "__main__":
    out_dir = Path("output/pdf")
    out_dir.mkdir(parents=True, exist_ok=True)
    target_pdf = str(out_dir / "Rapport_PFA_AI_XAUUSD.pdf")
    
    build_complete_pdf_report(target_pdf)
    
    # Copie de sauvegarde dans docs/report/
    docs_report_dir = Path("docs/report")
    docs_report_dir.mkdir(parents=True, exist_ok=True)
    backup_pdf = str(docs_report_dir / "Rapport_PFA_AI_XAUUSD.pdf")
    shutil.copyfile(target_pdf, backup_pdf)
    print(f"[+] Copie de sauvegarde synchronisée dans : {backup_pdf}")

