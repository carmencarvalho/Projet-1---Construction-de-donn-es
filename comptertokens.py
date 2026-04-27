import requests
import json
import os
import re
from bs4 import BeautifulSoup
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("camembert-base")

def extraire_texte(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "fr-FR,fr;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        # Suppression des balises inutiles
        for tag in soup(["script", "style", "nav", "footer", "header",
                         "aside", "figure", "figcaption", "iframe",
                         "form", "button", "noscript", "meta",
                         "img", "svg", "video", "audio"]):
            tag.decompose()

        # Suppression des classes typiques de pub/menu
        for tag in soup.find_all(class_=re.compile(
            r'cookie|banner|popup|ad|pub|social|share|related|comment|sidebar|breadcrumb|tag|newsletter',
            re.I)):
            tag.decompose()

        # Cibler le contenu principal
        contenu = (
            soup.find("article") or
            soup.find("main") or
            soup.find(class_=re.compile(r'article|content|body|text', re.I)) or
            soup.find("body")
        )

        if contenu is None:
            print(f"   ⚠️ Aucun contenu trouvé")
            return ""

        texte = contenu.get_text(separator=" ", strip=True)

        # Détection de blocage
        mots_blocage = ["access denied", "403", "cloudflare",
                        "enable javascript", "abonnez-vous"]
        if any(mot in texte.lower() for mot in mots_blocage):
            print(f"   ⛔ Site bloqué ou paywall détecté")
            return ""

        return texte

    except requests.exceptions.Timeout:
        print(f"   ⏱️ Timeout")
        return ""
    except requests.exceptions.ConnectionError:
        print(f"   🔌 Erreur de connexion")
        return ""
    except Exception as e:
        print(f"   ❌ Erreur : {e}")
        return ""

def nettoyer_texte(texte):
    texte = re.sub(r'http\S+', '', texte)
    texte = re.sub(r'\S+@\S+', '', texte)
    texte = re.sub(r'[©®™•|<>{}[\]_]', '', texte)
    texte = re.sub(r'\d{1,2}/\d{1,2}/\d{2,4}', '', texte)
    texte = re.sub(r'\s+', ' ', texte)
    texte = re.sub(r'Écrit par .+', '', texte)               # auteur
    texte = re.sub(r'Publié le .+', '', texte)               # date publication
    texte = re.sub(r'mis à jour le .+', '', texte)           # date mise à jour
    texte = re.sub(r'Sur le même sujet.+', '', texte, flags=re.DOTALL)  # bloc "articles similaires"
    texte = re.sub(r'Commentaires?.*', '', texte, flags=re.DOTALL)      # section commentaires
    texte = re.sub(r'Partager.*', '', texte, flags=re.DOTALL)           # boutons partage
    segments = re.split(r'(?<=[.!?])\s+', texte)
    segments_propres = [s for s in segments if len(s.split()) > 4]
    return ' '.join(segments_propres).strip()

def compter_tokens(texte):
    tokens = tokenizer.encode(texte, add_special_tokens=False)
    return len(tokens)

urls = [
    "https://reporterre.net/Loi-Duplomb-2-la-demarche-malhonnete-du-senateur-pour-imposer-son-texte",
    "https://www.franceinfo.fr/politique/la-france-insoumise/ce-n-est-pas-notre-france-bruno-retailleau-lance-un-observatoire-des-municipalites-passees-sous-le-giron-de-la-france-insoumise_7913861.html",
    "https://www.franceinfo.fr/monde/iran/guerre-entre-les-etats-unis-israel-et-l-iran/direct-guerre-au-moyen-orient-l-armee-israelienne-a-de-nouveau-bombarde-la-banlieue-sud-de-beyrouth_7915160.html",
    "https://www.franceinfo.fr/faits-divers/j-ai-un-peu-peur-de-sortir-une-enquete-ouverte-apres-la-blessure-d-une-adolescente-de-14-ans-par-une-balle-perdue_7951571.html",
    "https://www.franceinfo.fr/replay-radio/le-choix-franceinfo/reportage-il-y-a-beaucoup-d-etudiants-qui-ne-vont-pas-bien-le-succes-des-stages-de-premiers-secours-en-sante-mentale_7905692.html",
    "https://lepetitjournal.com/ho-chi-minh/pham-thi-thanh-tra-premiere-femme-vice-premier-ministre-histoire-vietnam-426039",
    "https://www.programme-tv.net/news/people/263536-emily-ratajkowski-enceinte-le-mannequin-attend-son-premier-enfant/",
    "https://www.leparisien.fr/faits-divers/les-passagers-dun-vol-ryanair-abandonnes-en-pleine-nuit-a-160-km-de-leur-destination-21-04-2026-GM4ZPKSEWJHALKA6BFKIR64NPA.php",
    "https://www.leparisien.fr/etudiant/etudes/ecoles/en-arrivant-aucun-nous-a-parle-dingenieur-ou-de-chercheur-des-etudiants-de-centralesupelec-enseignent-la-science-a-des-ecoliers-QD2GDCHFBJEALN7WDJTHT47YMA.php",
    "https://www.journaldesfemmes.fr/maman/education-scolarite/3262995-enseigner-ne-suffit-plus-les-profs-se-forment-desormais-aupres-de-crs/",
    "https://actu.fr/grand-est/tomblaine_54526/on-les-protege-pres-de-nancy-des-infirmiers-autorises-a-ne-plus-aller-dans-ce-quartier-juge-trop-dangereux_64186576.html",
    "https://www.franceinfo.fr/replay-radio/l-il-de-constance/un-tiktokeur-traque-les-pickpockets-dans-le-metro-heros-ou-dangereux-justicier_7939817.html",
    "https://actualitte.com/article/128463/insolite/ces-ecrivains-et-artistes-entrent-dans-le-domaine-public-en-2026",
    "https://www.criteo.com/fr/blog/sephora-la-meilleure-strategie-de-marketing-offline-commence-en-ligne/",
    "https://associations.gouv.fr/travailleurs-independants",
    "https://www.programme-tv.net/news/cinema/400952-un-p-tit-truc-en-plus-que-deviennent-les-acteurs-du-film/",
    "https://www.lefigaro.fr/vox/societe/penurie-de-professeurs-il-faut-ouvrir-l-education-nationale-a-la-concurrence-20260420",
]

def charger_dossier_txt(dossier, corpus_json, total_tokens):
    fichiers_txt = [f for f in os.listdir(dossier) if f.endswith(".txt")]
    
    for nom_fichier in fichiers_txt:
        chemin = os.path.join(dossier, nom_fichier)
        with open(chemin, "r", encoding="utf-8") as f:
            texte_brut = f.read()

        texte_propre = nettoyer_texte(texte_brut)
        texte_final = texte_propre
        nb_tokens = compter_tokens(texte_final)
        total_tokens += nb_tokens

        print(f"✅ {nom_fichier}")
        print(f"   → Tokens  : {nb_tokens}")
        print(f"   → Aperçu  : {texte_final[:80]!r}\n")

        if texte_final.strip():
            corpus_json.append({
                "text": texte_final,
                "meta": {"source": nom_fichier}
            })

    return corpus_json, total_tokens

total_tokens = 0
corpus_json = []

for url in urls:
    texte_brut = extraire_texte(url)
    texte_propre = nettoyer_texte(texte_brut)
    texte_final = texte_propre
    nb_tokens = compter_tokens(texte_final)
    total_tokens += nb_tokens

    print(f"{'✅' if texte_final.strip() else '⚠️'} {url[:60]}")
    print(f"   → Brut    : {len(texte_brut)} caractères")
    print(f"   → Nettoyé : {len(texte_propre)} caractères")
    print(f"   → Tokens  : {nb_tokens}")
    print(f"   → Aperçu  : {texte_final[:80]!r}\n")

    if texte_final.strip():
        corpus_json.append({
            "text": texte_final,
            "meta": {"source": url}
        })

print(f"{'='*50}")
print("📂 Chargement des fichiers manuels...\n")
corpus_json, total_tokens = charger_dossier_txt("articles_manuels", corpus_json, total_tokens)

print(f"{'='*50}")
print(f"TOTAL CORPUS : {total_tokens} tokens")
print(f"Articles importés : {len(corpus_json)}/{len(urls) + 5}")

with open("corpus_annotation.json", "w", encoding="utf-8") as f:
    json.dump(corpus_json, f, ensure_ascii=False, indent=2)

print(f"\n✅ Fichier exporté : corpus_annotation.json")