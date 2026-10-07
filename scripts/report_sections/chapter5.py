"""Chapitre 5 — Machine Learning et Prédiction Directionnelle."""

from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.lib import colors
from .styles import PRIMARY, SECONDARY, ACCENT, BORDER_COLOR, HIGHLIGHT, LIGHT_BG

def get_chapter5_story(styles):
    story = []

    story.append(Paragraph("Chapitre 5 — Machine Learning et Prédiction Directionnelle", styles['ChapterTitle']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceBefore=2, spaceAfter=12))

    story.append(Paragraph("5.1 Formalisation mathématique de la cible binaire (BULLISH vs BEARISH)", styles['SectionTitle']))
    story.append(Paragraph(
        "L'objectif de modélisation supervisée consiste à anticiper le régime directionnel futur du cours au comptant de l'or. "
        "Contrairement aux approches de régression directe qui tentent de prédire la valeur numérique exacte du prix futur "
        "(exercice hautement instable et sujet à un bruit démesuré), notre approche formule la tâche sous forme d'une classification "
        "probabiliste de régime tendanciel.",
        styles['Body']
    ))
    story.append(Paragraph(
        "Soit $C_t$ le cours de clôture de la bougie pivot H1 à l'instant $t$. Pour un horizon temporel de projection de $H$ périodes "
        "($H = 24$ barres d'une heure pour l'horizon journalier <i>Daily</i> ; $H = 120$ barres pour l'horizon hebdomadaire <i>Weekly</i>), "
        "le rendement arithmétique futur non anticipé est formellement défini par :<br/>"
        "<font face='TimesNewRoman-Italic' color='#0F2942'>&nbsp;&nbsp;&nbsp;&nbsp;R_{t, H} = \\frac{C_{t+H} - C_t}{C_t} = \\frac{C_{t+H}}{C_t} - 1</font><br/>"
        "La variable cible supervisée $Y_t$ est construite par discrétisation du rendement futur par rapport à un seuil d'amplitude "
        "paramétrique $\\theta$ fixé empiriquement ($\\theta = 0.005$, soit $0.5\\%$ pour l'horizon Daily 24H ; $\\theta = 0.010$, soit $1.0\\%$ "
        "pour l'horizon Weekly 120H) :<br/>"
        "• <b>Classe BULLISH (Label 1)</b> : Si $R_{t, H} \\ge +\\theta$ (impulsion haussière significative).<br/>"
        "• <b>Classe BEARISH (Label 0)</b> : Si $R_{t, H} \\le -\\theta$ (impulsion baissière significative).",
        styles['Body']
    ))

    story.append(Paragraph("5.2 Filtrage de la zone morte et justification de l'espace binaire", styles['SectionTitle']))
    story.append(Paragraph(
        "<b>Règle fondamentale de conception : Absence formelle de classe NEUTRAL.</b><br/>"
        "Lorsque la variation future du cours vérifie l'inégalité stricte $|R_{t, H}| < \\theta$, l'observation se situe "
        "dans une <i>zone morte d'indécision</i> (<i>deadband</i>). Dans cet intervalle étroit, les mouvements de prix sont "
        "dominés par le bruit brownien de microstructure, les micro-oscillations du carnet d'ordres et les coûts de transaction "
        "(frais de courtage et spread bid/ask). Tenter d'entraîner un modèle d'apprentissage à classifier ces mouvements insignifiants "
        "revient à contraindre l'algorithme à apprendre du bruit pur, dégradant sévèrement ses frontières de décision.",
        styles['Body']
    ))
    story.append(Paragraph(
        "Conformément à la spécification formalisée dans <code>backend/app/ml/labels.py</code> et auditée dans "
        "<code>models/xauusd/label_definition.json</code>, ces observations en zone morte sont <b>systématiquement filtrées "
        "et exclues lors de la constitution du jeu de données d'apprentissage et de validation</b>.<br/>"
        "L'espace de prédiction opérationnel est donc un <b>problème de classification binaire stricte</b> satisfaisant en tout temps :<br/>"
        "<font face='TimesNewRoman-Italic' color='#0F2942'>&nbsp;&nbsp;&nbsp;&nbsp;CLASS\\_ORDER = [\\text{\"BEARISH\"}, \\text{\"BULLISH\"}]</font><br/>"
        "<font face='TimesNewRoman-Italic' color='#0F2942'>&nbsp;&nbsp;&nbsp;&nbsp;P(\\text{BULLISH}) + P(\\text{BEARISH}) = 1.0</font><br/>"
        "Le système n'émet en aucune circonstance une prédiction de classe 'NEUTRAL'.",
        styles['Body']
    ))

    story.append(Paragraph("5.3 Algorithmes benchmarkés et protocole Walk-Forward expansif", styles['SectionTitle']))
    story.append(Paragraph(
        "Dans l'étape 4 (<code>backend/app/ml/step4.py</code>), quatre familles d'algorithmes de référence ont été évaluées "
        "de manière rigoureusement comparative :<br/>"
        "1. <b>Régression Logistique (Logistic Regression)</b> : Modèle linéaire probabiliste régularisé par pénalisation L2, "
        "précédé d'une standardisation z-score via <code>StandardScaler</code>. Paramètres : <code>C=1.0, max_iter=1000, solver='lbfgs'</code>.<br/>"
        "2. <b>Forêt Aléatoire (Random Forest Classifier)</b> : Ensemble d'arbres de décision décorrélés par bagging. "
        "Paramètres : <code>n_estimators=100, max_depth=6, min_samples_leaf=20, random_state=42</code>.<br/>"
        "3. <b>XGBoost (Extreme Gradient Boosting)</b> : Boosting de gradient avec régularisation. "
        "Paramètres : <code>n_estimators=100, max_depth=4, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8</code>.<br/>"
        "4. <b>LightGBM (Light Gradient Boosted Machine)</b> : Boosting de gradient avec optimisation foliaire. "
        "Paramètres : <code>n_estimators=100, max_depth=4, learning_rate=0.05, num_leaves=15</code>.",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>Protocole expérimental Walk-Forward sans fuite temporelle :</b><br/>"
        "L'évaluation s'interdit formellement tout mélange aléatoire d'observations (<code>shuffle = False</code>). "
        "Elle repose sur une validation temporelle glissante à <b>4 plis (folds) à fenêtre expansive (expanding window)</b> :<br/>"
        "• Chaque pli $k$ s'entraîne sur l'intégralité du passé disponible depuis l'origine jusqu'à une date de coupure $t_k$.<br/>"
        "• <b>Période d'embargo temporel</b> : Un intervalle de purge de 24 barres H1 est systématiquement inséré entre la fin "
        "de la fenêtre d'entraînement et le début de la fenêtre de validation afin de neutraliser toute corrélation sérielle induite "
        "par le calcul des rendements à 24 périodes.<br/>"
        "• La validation s'effectue sur les 1 722 barres immédiatement postérieures à l'embargo.<br/>"
        "• <b>Score de sélection multicritère</b> : La sélection du meilleur modèle repose sur la formule formalisée dans l'audit :<br/>"
        "<font face='TimesNewRoman-Italic' color='#0F2942'>&nbsp;&nbsp;&nbsp;&nbsp;Score = 0.40 \\cdot \\overline{\\text{AUC}} + 0.40 \\cdot \\overline{\\text{BalAcc}} - 0.10 \\cdot \\overline{\\text{Brier}} - 0.10 \\cdot \\sigma_{\\text{BalAcc}}</font><br/>"
        "<i>Règle de disqualification absolue :</i> Tout algorithme subissant un effondrement de classe (<i>class collapse</i> — prédiction "
        "systématique d'une seule classe sur l'ensemble d'un fold) est immédiatement et définitivement disqualifié.",
        styles['Body']
    ))

    story.append(Paragraph("5.4 Analyse comparative détaillée des plis et sélection du modèle", styles['SectionTitle']))
    story.append(Paragraph(
        "Le Tableau 5.1 détaille le découpage chronologique et la répartition des classes supervisées sur les 4 plis expansifs "
        "du protocole walk-forward pour le modèle journalier (Daily 24H) :",
        styles['Body']
    ))

    fold_data = [
        [Paragraph("Pli (Fold)", styles['TableHeader']), Paragraph("Échantillon Train", styles['TableHeader']), Paragraph("Échantillon Val", styles['TableHeader']), Paragraph("Date de Coupure (Cutoff)", styles['TableHeader']), Paragraph("Répartition Train (Bull/Bear)", styles['TableHeader']), Paragraph("Répartition Val (Bull/Bear)", styles['TableHeader'])],
        [Paragraph("<b>Pli 1</b>", styles['TableText']), Paragraph("5 200", styles['TableText']), Paragraph("1 722", styles['TableText']), Paragraph("12/04/2024 10:00 UTC", styles['TableText']), Paragraph("2 802 / 2 398 (53.9% Bull)", styles['TableText']), Paragraph("1 061 / 661 (61.6% Bull)", styles['TableText'])],
        [Paragraph("<b>Pli 2</b>", styles['TableText']), Paragraph("6 928", styles['TableText']), Paragraph("1 722", styles['TableText']), Paragraph("22/10/2024 12:00 UTC", styles['TableText']), Paragraph("3 857 / 3 071 (55.7% Bull)", styles['TableText']), Paragraph("1 087 / 635 (63.1% Bull)", styles['TableText'])],
        [Paragraph("<b>Pli 3</b>", styles['TableText']), Paragraph("8 645", styles['TableText']), Paragraph("1 722", styles['TableText']), Paragraph("17/04/2025 22:00 UTC", styles['TableText']), Paragraph("4 947 / 3 698 (57.2% Bull)", styles['TableText']), Paragraph("1 114 / 608 (64.7% Bull)", styles['TableText'])],
        [Paragraph("<b>Pli 4</b>", styles['TableText']), Paragraph("10 375", styles['TableText']), Paragraph("1 722", styles['TableText']), Paragraph("17/10/2025 23:00 UTC", styles['TableText']), Paragraph("6 052 / 4 323 (58.3% Bull)", styles['TableText']), Paragraph("994 / 728 (57.7% Bull)", styles['TableText'])],
    ]
    t_f = Table(fold_data, colWidths=[20 * mm, 26 * mm, 26 * mm, 40 * mm, 38 * mm, 38 * mm])
    t_f.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, HIGHLIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_f)
    story.append(Paragraph("Tableau 5.1 : Découpage temporel et distribution des classes sur les 4 plis du walk-forward Daily", styles['Caption']))

    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "Le Tableau 5.2 rapporte les métriques individuelles de chaque pli obtenues par le modèle de production "
        "(Régression Logistique) lors de la validation walk-forward pour les deux horizons prévisionnels (Daily et Weekly) :",
        styles['Body']
    ))

    fold_metrics = [
        [Paragraph("Horizon & Pli", styles['TableHeader']), Paragraph("Balanced Accuracy", styles['TableHeader']), Paragraph("ROC-AUC", styles['TableHeader']), Paragraph("Brier Score", styles['TableHeader']), Paragraph("Écart Surapprentissage (Train - Val)", styles['TableHeader'])],
        [Paragraph("<b>Daily — Pli 1</b>", styles['TableText']), Paragraph("54.79%", styles['TableText']), Paragraph("51.77%", styles['TableText']), Paragraph("0.2519", styles['TableText']), Paragraph("-0.73% (Généralisation optimale)", styles['TableText'])],
        [Paragraph("<b>Daily — Pli 2</b>", styles['TableText']), Paragraph("50.56%", styles['TableText']), Paragraph("56.13%", styles['TableText']), Paragraph("0.2609", styles['TableText']), Paragraph("+2.35% (Surapprentissage très faible)", styles['TableText'])],
        [Paragraph("<b>Daily — Pli 3</b>", styles['TableText']), Paragraph("50.93%", styles['TableText']), Paragraph("50.06%", styles['TableText']), Paragraph("0.2714", styles['TableText']), Paragraph("+3.59% (Stabilité conservée)", styles['TableText'])],
        [Paragraph("<b>Daily — Pli 4</b>", styles['TableText']), Paragraph("53.23%", styles['TableText']), Paragraph("51.40%", styles['TableText']), Paragraph("0.2970", styles['TableText']), Paragraph("+4.00% (Contrôle de la variance)", styles['TableText'])],
        [Paragraph("<b>Daily — Moyenne</b>", styles['TableText']), Paragraph("<b>52.38% (±1.73%)</b>", styles['TableText']), Paragraph("<b>52.34% (±2.28%)</b>", styles['TableText']), Paragraph("<b>0.2703 (±0.017)</b>", styles['TableText']), Paragraph("<b>+2.30% (±1.85%) — Sélectionné</b>", styles['TableText'])],
        [Paragraph("<b>Weekly — Pli 1</b>", styles['TableText']), Paragraph("39.89%", styles['TableText']), Paragraph("39.93%", styles['TableText']), Paragraph("0.2865", styles['TableText']), Paragraph("+18.92% (Choc de régime)", styles['TableText'])],
        [Paragraph("<b>Weekly — Pli 2</b>", styles['TableText']), Paragraph("55.44%", styles['TableText']), Paragraph("62.29%", styles['TableText']), Paragraph("0.1826", styles['TableText']), Paragraph("-13.08% (Excellente généralisation)", styles['TableText'])],
        [Paragraph("<b>Weekly — Pli 3</b>", styles['TableText']), Paragraph("56.42%", styles['TableText']), Paragraph("61.09%", styles['TableText']), Paragraph("0.2530", styles['TableText']), Paragraph("+2.57% (Stabilité)", styles['TableText'])],
        [Paragraph("<b>Weekly — Pli 4</b>", styles['TableText']), Paragraph("66.86%", styles['TableText']), Paragraph("73.49%", styles['TableText']), Paragraph("0.2569", styles['TableText']), Paragraph("-0.60% (Forte puissance prédictive)", styles['TableText'])],
        [Paragraph("<b>Weekly — Moyenne</b>", styles['TableText']), Paragraph("<b>54.65% (±9.63%)</b>", styles['TableText']), Paragraph("<b>59.20% (±12.13%)</b>", styles['TableText']), Paragraph("<b>0.2448 (±0.038)</b>", styles['TableText']), Paragraph("<b>+1.95% (±11.41%) — Sélectionné</b>", styles['TableText'])],
    ]
    t_fm = Table(fold_metrics, colWidths=[38 * mm, 32 * mm, 28 * mm, 28 * mm, 44 * mm])
    t_fm.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, HIGHLIGHT]),
        ('BACKGROUND', (0,5), (-1,5), LIGHT_BG),
        ('BACKGROUND', (0,10), (-1,10), LIGHT_BG),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_fm)
    story.append(Paragraph("Tableau 5.2 : Métriques détaillées par pli du modèle de production (Logistic Regression)", styles['Caption']))

    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "Les résultats du benchmark comparatif agrégés sur les 4 plis (Tableau 5.3) ont mis en lumière un phénomène "
        "majeur de surapprentissage chez les modèles complexes :",
        styles['Body']
    ))

    bm_data = [
        [Paragraph("Modèle Candidat", styles['TableHeader']), Paragraph("Accuracy Moyenne", styles['TableHeader']), Paragraph("Balanced Acc.", styles['TableHeader']), Paragraph("Écart Surapprentissage", styles['TableHeader']), Paragraph("Diagnostic & Décision de Sélection", styles['TableHeader'])],
        [Paragraph("<b>Logistic Regression</b>", styles['TableText']), Paragraph("57.37% (±2.52%)", styles['TableText']), Paragraph("52.38% (±1.73%)", styles['TableText']), Paragraph("<b>2.30%</b> (±1.85%)", styles['TableText']), Paragraph("<font color='#1B4D3E'><b>SÉLECTIONNÉ POUR LA PRODUCTION</b><br/>Score = 0.3901 (Rang 1) | Aucun effondrement | Écart train-val minime.</font>", styles['TableText'])],
        [Paragraph("<b>Random Forest</b>", styles['TableText']), Paragraph("54.69% (±8.73%)", styles['TableText']), Paragraph("51.13% (±2.36%)", styles['TableText']), Paragraph("27.45% (±6.93%)", styles['TableText']), Paragraph("<font color='#7A2525'><b>DISQUALIFIÉ</b> : Effondrement de classe (fold 1) et surapprentissage massif (27.4%).</font>", styles['TableText'])],
        [Paragraph("<b>XGBoost</b>", styles['TableText']), Paragraph("55.92% (±3.63%)", styles['TableText']), Paragraph("50.93% (±2.77%)", styles['TableText']), Paragraph("21.64% (±3.26%)", styles['TableText']), Paragraph("<font color='#A87A1E'><b>Écarté</b> : Rang 2 (Score = 0.3748) ; surapprentissage élevé (21.6%).</font>", styles['TableText'])],
        [Paragraph("<b>LightGBM</b>", styles['TableText']), Paragraph("54.02% (±5.05%)", styles['TableText']), Paragraph("49.22% (±2.41%)", styles['TableText']), Paragraph("33.54% (±4.52%)", styles['TableText']), Paragraph("<font color='#7A2525'><b>DISQUALIFIÉ</b> : Effondrement de classe (fold 1) et surapprentissage extrême (33.5%).</font>", styles['TableText'])],
    ]
    t_bm = Table(bm_data, colWidths=[32 * mm, 32 * mm, 32 * mm, 34 * mm, 40 * mm])
    t_bm.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, HIGHLIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_bm)
    story.append(Paragraph("Tableau 5.3 : Benchmark comparatif des algorithmes ML lors de la validation walk-forward", styles['Caption']))

    story.append(Paragraph(
        "<b>Conclusion de l'étape de sélection :</b> Les modèles d'arbres ensemblistes (Random Forest et LightGBM) "
        "ont tous deux échoué lors du premier pli en prédisant exclusivement la classe majoritaire haussière (<i>class collapse</i>), "
        "entraînant leur élimination immédiate. De plus, leur écart de performance entre apprentissage et validation "
        "(dépassant 27% à 33%) atteste d'une mémorisation toxique du bruit. "
        "La <b>Régression Logistique</b> s'est imposée avec éclat comme l'unique modèle retenu pour la production grâce à sa régularité "
        "exemplaire, son écart de surapprentissage remarquablement faible de <b>2.30%</b> et son score de sélection de <b>0.3901</b> (Rang 1).",
        styles['Body']
    ))
    story.append(PageBreak())

    story.append(Paragraph("5.5 Analyse exhaustive des métriques réelles hors-échantillon", styles['SectionTitle']))
    story.append(Paragraph(
        "Fidèles aux exigences d'honnêteté scientifique absolue et au mandat d'audit du projet, nous exposons sans fard "
        "les résultats réels obtenus par le modèle final de production (Régression Logistique) sur le jeu de test final holdout "
        "(strictement isolé dans le futur, non vu durant l'apprentissage ni la validation walk-forward).",
        styles['Body']
    ))

    story.append(Paragraph("A. Résultats du modèle journalier (Daily 24H) — <code>models/xauusd/final_metrics.json</code>", styles['SubSectionTitle']))
    story.append(Paragraph(
        "Évalué sur <b>N = 2 144 bougies fermées</b> (période du 18/03/2026 au 17/09/2026) :",
        styles['Body']
    ))

    m_daily = [
        [Paragraph("Métrique Statistique Réelle", styles['TableHeader']), Paragraph("Valeur Mesurée", styles['TableHeader']), Paragraph("Interprétation Technique & Signification Statistique", styles['TableHeader'])],
        [Paragraph("<b>Accuracy (Justesse)</b>", styles['TableText']), Paragraph("<b>45.71%</b> (0.4571)", styles['TableText']), Paragraph("Proportion globale de prédictions correctes. <b>Inférieure à la baseline majoritaire (48.04%)</b>.", styles['TableText'])],
        [Paragraph("<b>Balanced Accuracy</b>", styles['TableText']), Paragraph("<b>47.31%</b> (0.4731)", styles['TableText']), Paragraph("Moyenne arithmétique des rappels : (Rappel_Bull + Rappel_Bear) / 2.", styles['TableText'])],
        [Paragraph("<b>Précision</b>", styles['TableText']), Paragraph("<b>46.56%</b> (0.4656)", styles['TableText']), Paragraph("907 vrais positifs haussiers sur 1 948 prédictions BULLISH émises.", styles['TableText'])],
        [Paragraph("<b>Rappel (Recall)</b>", styles['TableText']), Paragraph("<b>88.06%</b> (0.8806)", styles['TableText']), Paragraph("Capacité à détecter 907 mouvements haussiers réels sur un total de 1 030.", styles['TableText'])],
        [Paragraph("<b>F1-Score</b>", styles['TableText']), Paragraph("<b>60.91%</b> (0.6091)", styles['TableText']), Paragraph("Moyenne harmonique entre précision et rappel haussiers.", styles['TableText'])],
        [Paragraph("<b>ROC-AUC</b>", styles['TableText']), Paragraph("<b>49.28%</b> (0.4928)", styles['TableText']), Paragraph("Aire sous la courbe ROC légèrement en-deçà du seuil aléatoire de 50.0%.", styles['TableText'])],
        [Paragraph("<b>Brier Score Loss</b>", styles['TableText']), Paragraph("<b>0.2871</b>", styles['TableText']), Paragraph("Écart quadratique moyen entre probabilités prédites et réalisations binaires réelles.", styles['TableText'])],
        [Paragraph("<b>Majority Baseline Acc.</b>", styles['TableText']), Paragraph("<b>48.04%</b> (0.4804)", styles['TableText']), Paragraph("Performance obtenue par un modèle naïf prédisant toujours la classe majoritaire.", styles['TableText'])],
        [Paragraph("<b>Accuracy Lift</b>", styles['TableText']), Paragraph("<b>-2.33%</b> (-0.0233)", styles['TableText']), Paragraph("Différentiel de justesse négatif par rapport à la baseline majoritaire.", styles['TableText'])],
        [Paragraph("<b>Matrice de Confusion</b>", styles['TableText']), Paragraph("TN: 73 | FP: 1041<br/>FN: 123 | TP: 907", styles['TableText']), Paragraph("Biais haussier massif : 1 948 prédictions BULLISH pour seulement 196 prédictions BEARISH.", styles['TableText'])],
    ]
    t_d = Table(m_daily, colWidths=[45 * mm, 35 * mm, 90 * mm])
    t_d.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, HIGHLIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_d)
    story.append(Paragraph("Tableau 5.4 : Métriques réelles mesurées hors-échantillon pour le modèle Daily (24H)", styles['Caption']))

    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("B. Résultats du modèle hebdomadaire (Weekly 120H) — <code>models/xauusd_weekly/final_metrics.json</code>", styles['SubSectionTitle']))
    story.append(Paragraph(
        "Évalué sur <b>N = 2 472 bougies fermées</b> (période du 06/03/2026 au 11/09/2026) :",
        styles['Body']
    ))

    m_weekly = [
        [Paragraph("Métrique Statistique Réelle", styles['TableHeader']), Paragraph("Valeur Mesurée", styles['TableHeader']), Paragraph("Interprétation Technique & Signification Statistique", styles['TableHeader'])],
        [Paragraph("<b>Accuracy (Justesse)</b>", styles['TableText']), Paragraph("<b>39.20%</b> (0.3920)", styles['TableText']), Paragraph("Proportion globale de succès sur 5 jours. <b>Inférieure à la baseline (43.77%)</b>.", styles['TableText'])],
        [Paragraph("<b>Balanced Accuracy</b>", styles['TableText']), Paragraph("<b>43.90%</b> (0.4390)", styles['TableText']), Paragraph("Moyenne des rappels équilibrés entre régimes hebdomadaires.", styles['TableText'])],
        [Paragraph("<b>Précision</b>", styles['TableText']), Paragraph("<b>40.37%</b> (0.4037)", styles['TableText']), Paragraph("883 vrais positifs haussiers sur 2 187 prédictions BULLISH émises.", styles['TableText'])],
        [Paragraph("<b>Rappel (Recall)</b>", styles['TableText']), Paragraph("<b>81.61%</b> (0.8161)", styles['TableText']), Paragraph("Détection de 883 mouvements haussiers hebdomadaires sur 1 082.", styles['TableText'])],
        [Paragraph("<b>F1-Score</b>", styles['TableText']), Paragraph("<b>54.02%</b> (0.5402)", styles['TableText']), Paragraph("Score F1 du régime hebdomadaire.", styles['TableText'])],
        [Paragraph("<b>ROC-AUC</b>", styles['TableText']), Paragraph("<b>53.62%</b> (0.5362)", styles['TableText']), Paragraph("Capacité discriminante supérieure au hasard pur (53.62% > 50%).", styles['TableText'])],
        [Paragraph("<b>Brier Score Loss</b>", styles['TableText']), Paragraph("<b>0.4452</b>", styles['TableText']), Paragraph("Incertitude probabiliste plus prononcée à l'horizon 5 jours.", styles['TableText'])],
        [Paragraph("<b>Majority Baseline Acc.</b>", styles['TableText']), Paragraph("<b>43.77%</b> (0.4377)", styles['TableText']), Paragraph("Baseline de la classe majoritaire hebdomadaire.", styles['TableText'])],
        [Paragraph("<b>Accuracy Lift</b>", styles['TableText']), Paragraph("<b>-4.57%</b> (-0.0457)", styles['TableText']), Paragraph("Gain de justesse négatif par rapport à la baseline majoritaire.", styles['TableText'])],
        [Paragraph("<b>Matrice de Confusion</b>", styles['TableText']), Paragraph("TN: 86 | FP: 1304<br/>FN: 199 | TP: 883", styles['TableText']), Paragraph("Persistance du biais haussier : 2 187 prédictions BULLISH contre 285 BEARISH.", styles['TableText'])],
    ]
    t_w = Table(m_weekly, colWidths=[45 * mm, 35 * mm, 90 * mm])
    t_w.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, HIGHLIGHT]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_w)
    story.append(Paragraph("Tableau 5.5 : Métriques réelles mesurées hors-échantillon pour le modèle Weekly (120H)", styles['Caption']))

    story.append(Paragraph(
        "<b>Constat fondamental et explicite d'audit :</b><br/>"
        "Les deux modèles affichent une justesse globale (Accuracy) <b>strictement inférieure à leur baseline majoritaire respective</b> "
        "(Lift négatif de -2.33% en Daily 24H et de -4.57% en Weekly 120H). "
        "L'examen des matrices de confusion révèle un déséquilibre prononcé de la distribution des inférences : "
        "le modèle prédit massivement la classe <code>BULLISH</code> (90.8% des prédictions en Daily, 88.5% en Weekly). "
        "Ce comportement reflète l'empreinte de la tendance haussière séculaire très puissante de l'or durant la période "
        "d'entraînement (2022-2025). Lorsque le marché a traversé des consolidations baissières sur le jeu de test final de 2026, "
        "le modèle a continué d'émettre un biais haussier, générant un volume élevé de faux positifs (1 041 en Daily et 1 304 en Weekly). "
        "Cette réalité statistique sera discutée de manière approfondie au Chapitre 9 à la lumière de la théorie financière.",
        styles['Body']
    ))

    story.append(Paragraph("5.6 Modélisation de la confiance et scénarios probabilistes", styles['SectionTitle']))
    story.append(Paragraph(
        "Dans <code>backend/app/ml/step5_serving.py</code>, l'inférence ne se limite pas à la restitution d'une étiquette binaire. "
        "Le moteur associe à chaque prédiction une quantification d'incertitude et une contextualisation scénaristique :",
        styles['Body']
    ))
    story.append(Paragraph(
        "• <b>Indice de confiance normalisé :</b> Dérivé de la distance relative à la frontière d'indécision (0.5) :<br/>"
        "<font face='TimesNewRoman-Italic' color='#0F2942'>&nbsp;&nbsp;&nbsp;&nbsp;\\text{Confidence} = 2 \\cdot |P(\\text{BULLISH}) - 0.5| \\in [0, 1]</font><br/>"
        "Une probabilité de 0.50 produit une confiance de 0.0 (incertitude totale), tandis qu'une probabilité de 0.90 produit une confiance de 0.80.<br/>"
        "• <b>Dérivation contextuelle des trois scénarios (<code>build_scenarios</code>) :</b><br/>"
        "1. <i>Scénario Base</i> : Conditionné au maintien de la dynamique courante dans le sens prédominant. "
        "Règle d'invalidation : clôture de toute nouvelle bougie H1 modifiant significativement les indicateurs d'entrée.<br/>"
        "2. <i>Scénario Bullish</i> : Conditionné au maintien des cours au-dessus des moyennes mobiles pivots (SMA 20/50/200) "
        "avec momentum haussier positif. Règle d'invalidation formelle : clôture confirmée sous la moyenne mobile SMA.<br/>"
        "3. <i>Scénario Bearish</i> : Conditionné au rejet sous les résistances de moyennes mobiles avec accélération du momentum baissier. "
        "Règle d'invalidation formelle : franchissement haussier et clôture confirmée au-dessus de la SMA.",
        styles['Body']
    ))

    story.append(Paragraph("5.7 Explicabilité causale : Coefficients logit linéaires et SHAP", styles['SectionTitle']))
    story.append(Paragraph(
        "Pour répondre aux exigences de transparence et refuser l'effet 'boîte noire', le système intègre une décomposition "
        "analytique des décisions :",
        styles['Body']
    ))
    story.append(Paragraph(
        "<b>A. Mécanisme de production principal : Décomposition linéaire des coefficients logit :</b><br/>"
        "Le modèle de production étant une Régression Logistique avec standardisation préalable, la fonction de décision s'écrit :<br/>"
        "<font face='TimesNewRoman-Italic' color='#0F2942'>&nbsp;&nbsp;&nbsp;&nbsp;\\text{Logit}(X) = w_0 + \\sum_{i=1}^{87} w_i \\cdot X_{\\text{scaled}, i}</font><br/>"
        "La contribution individuelle de la $i$-ème caractéristique à l'instant d'inférence est calculée par "
        "<code>_linear_contributions</code> (dans <code>backend/app/services/predictions.py</code>) :<br/>"
        "<font face='TimesNewRoman-Italic' color='#0F2942'>&nbsp;&nbsp;&nbsp;&nbsp;\\text{Contribution}_i = w_i \\cdot X_{\\text{scaled}, i}</font><br/>"
        "Le système extrait les 8 variables présentant la plus forte valeur absolue $|\\text{Contribution}_i|$, "
        "précisant pour chacune son nom, sa valeur brute non normalisée, son signe (direction <code>positive</code> favorisant BULLISH, "
        "ou <code>negative</code> favorisant BEARISH) et son rang de 1 à 8.<br/>"
        "<b>B. Statut réel de SHAP (SHapley Additive exPlanations) :</b><br/>"
        "Le code source du backend intègre bel et bien la bibliothèque SHAP (<code>shap.TreeExplainer</code>) au sein "
        "de la fonction <code>_tree_contributions</code> dans <code>backend/app/services/predictions.py</code>. "
        "Toutefois, nous établissons clairement la distinction suivante :<br/>"
        "<i>SHAP est implémenté comme mécanisme disponible et de repli pour les modèles arborescents (XGBoost, Random Forest). "
        "Dans la mesure où l'artefact sélectionné pour la production est la Régression Logistique, SHAP n'est pas le mécanisme actif "
        "en exécution runtime sur le modèle déployé. L'explicabilité en production est assurée par la décomposition exacte des coefficients linéaires logit.</i>",
        styles['Body']
    ))
    story.append(PageBreak())

    return story

