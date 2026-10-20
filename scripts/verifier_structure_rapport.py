"""Vérifie les références du PBIP sans exécuter Power BI, DAX ou Power Query.

Usage : python -B scripts/verifier_structure_rapport.py
Option : --backup CHEMIN pour comparer les fichiers à une sauvegarde complète.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT/'Suivi_Appel_offre.SemanticModel/definition'
REPORT = ROOT/'Suivi_Appel_offre.Report/definition'
AUTOMATIC = re.compile(r'(?:LocalDateTable|DateTableTemplate)_[A-Za-z0-9_-]+')
FINAL_PAGES = {'5b804ba8646b7816a59f','9d01f4bf588b204a2bf9','d31a1500000000000001'}


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def literal(obj):
    value = obj.get('expr', {}).get('Literal', {}).get('Value')
    return value[1:-1].replace("''", "'") if value and value.startswith("'") else value


def check_structure():
    errors, warnings = [], []
    tables = {}
    for path in (MODEL/'tables').glob('*.tmdl'):
        text = path.read_text(encoding='utf-8-sig')
        first = text.splitlines()[0]
        if first.lstrip().startswith('///'):
            first = next(line for line in text.splitlines() if line.startswith('table '))
        table = first[len('table '):].strip().strip("'").replace("''", "'")
        fields = set()
        for _, quoted, plain in re.findall(r"^\t(column|measure) (?:'((?:[^']|'')*)'|([^\s=]+))", text, re.M):
            fields.add(quoted.replace("''", "'") if quoted else plain)
        tables[table] = fields
        if re.search(r'^\s*description\s*:', text, re.M):
            errors.append(f'Description TMDL incorrecte : {path.name}')
    if set(tables) != {'Données','_Mesures','Dynamic Slicer','Calendrier ouvré France'}:
        errors.append(f'Tables inattendues : {sorted(tables)}')
    model_text = (MODEL/'model.tmdl').read_text(encoding='utf-8-sig')
    if 'annotation __PBI_TimeIntelligenceEnabled = 0' not in model_text:
        errors.append('Date/heure automatique non désactivé dans model.tmdl')
    references = {name.strip("'").replace("''", "'")
                  for name in re.findall(r'^ref table (.+)$', model_text, re.M)}
    if references != set(tables): errors.append('Références de tables incohérentes dans model.tmdl')
    for folder in [MODEL,REPORT]:
        for path in folder.rglob('*'):
            if path.is_file() and path.suffix in ('.json','.tmdl'):
                if AUTOMATIC.search(path.read_text(encoding='utf-8-sig')):
                    errors.append(f'Référence de date automatique : {path.relative_to(ROOT)}')
    data = (MODEL/'tables/Données.tmdl').read_text(encoding='utf-8-sig')
    if re.search(r'^\s*variation\s', data, re.M): errors.append('Variation de date restante')
    relations_path = MODEL/'relationships.tmdl'
    if relations_path.exists() and relations_path.read_text(encoding='utf-8-sig').strip():
        errors.append('Relations présentes alors que le modèle livré est sans relation')
    culture = (MODEL/'cultures/fr-FR.tmdl').read_text(encoding='utf-8-sig')
    linguistic = json.loads(culture[culture.index('{'):culture.rindex('}')+1])
    entity_names = set(linguistic['Entities'])
    def check_linguistic(obj):
        if isinstance(obj, dict):
            if 'VariationSource' in obj: errors.append('Variation linguistique restante')
            if 'ConceptualEntity' in obj:
                table = obj['ConceptualEntity']
                if table not in tables: errors.append(f'Table linguistique absente : {table}')
                column = obj.get('ConceptualProperty')
                if column and column not in tables.get(table,set()): errors.append(f'Champ linguistique absent : {table}.{column}')
            for key,value in obj.items():
                if key == 'Entity' and isinstance(value,str) and value not in entity_names:
                    errors.append(f'Entité linguistique absente : {value}')
                check_linguistic(value)
        elif isinstance(obj,list):
            for value in obj: check_linguistic(value)
    check_linguistic(linguistic)
    pages = {path.parent.name:load(path) for path in (REPORT/'pages').glob('*/page.json')}
    metadata = load(REPORT/'pages/pages.json')
    if set(metadata['pageOrder']) != set(pages): errors.append('Ordre des pages incohérent')
    for key in ('activePageName','landingPageName'):
        if metadata.get(key) not in pages: errors.append(f'Page absente : {key}')
    visible = {name for name,page in pages.items() if page.get('visibility') != 'HiddenInViewMode'}
    if visible != FINAL_PAGES: errors.append('Les trois pages finales visibles ne correspondent pas')
    visuals = {}
    for name in pages:
        visuals[name] = {p.parent.name:load(p) for p in (REPORT/'pages'/name/'visuals').glob('*/visual.json')}
    bookmarks = {path.stem.removesuffix('.bookmark'):load(path)
                 for path in (REPORT/'bookmarks').glob('*.bookmark.json')}
    field_checks = 0
    def inspect(obj, aliases=None):
        nonlocal field_checks
        aliases = dict(aliases or {})
        if isinstance(obj, dict):
            for source in obj.get('From', []):
                if isinstance(source,dict) and source.get('Entity'):
                    aliases[source['Name']] = source['Entity']
            for kind in ('Column','Measure'):
                exp = obj.get(kind)
                if isinstance(exp,dict) and isinstance(exp.get('Expression'),dict):
                    ref = exp['Expression'].get('SourceRef',{})
                    table = ref.get('Entity') or aliases.get(ref.get('Source'))
                    if table:
                        field_checks += 1
                        if exp.get('Property') not in tables.get(table,set()):
                            errors.append(f'Champ absent : {table}.{exp.get("Property")}')
            if 'SourceRef' in obj:
                table = obj['SourceRef'].get('Entity')
                if table and table not in tables: errors.append(f'Table PBIR absente : {table}')
            if 'HierarchyLevel' in obj:
                errors.append('Hiérarchie PBIR à contrôler dans le modèle sans hiérarchie')
            for value in obj.values(): inspect(value, aliases)
        elif isinstance(obj,list):
            for value in obj: inspect(value,aliases)
    json_count = 0
    for path in REPORT.rglob('*.json'):
        inspect(load(path)); json_count += 1
    links = 0
    for name,items in visuals.items():
        for visual_name,obj in items.items():
            if obj['name'] != visual_name: errors.append(f'Nom de visuel incohérent : {visual_name}')
            for link in obj.get('visual',{}).get('visualContainerObjects',{}).get('visualLink',[]):
                props = link['properties']; kind = literal(props.get('type',{}))
                if kind == 'PageNavigation':
                    links += 1
                    if literal(props.get('navigationSection',{})) not in pages:
                        errors.append(f'Navigation vers une page absente : {visual_name}')
                elif kind == 'Bookmark':
                    links += 1
                    if literal(props.get('bookmark',{})) not in bookmarks:
                        errors.append(f'Bouton vers un signet absent : {visual_name}')
    all_visuals = {v for items in visuals.values() for v in items}
    for name,bookmark in bookmarks.items():
        state = bookmark.get('explorationState',{})
        if state.get('activeSection') not in pages: errors.append(f'Page active du signet absente : {name}')
        for page,section in state.get('sections',{}).items():
            if page not in pages: errors.append(f'Page du signet absente : {name}'); continue
            for visual in section.get('visualContainers',{}):
                if visual not in visuals[page]: errors.append(f'Visuel enregistré absent : {name}/{visual}')
        for visual in bookmark.get('options',{}).get('targetVisualNames',[]):
            if visual not in all_visuals:
                warnings.append(f'{bookmark["displayName"]} : cible vers le visuel absent {visual} ; Réinitialiser à vérifier dans Desktop')
    pbip = load(ROOT/'Suivi_Appel_offre.pbip')
    for item in pbip['artifacts']:
        if not (ROOT/item['report']['path']/'definition.pbir').exists(): errors.append('Rapport du PBIP absent')
    pbir = load(ROOT/'Suivi_Appel_offre.Report/definition.pbir')
    if (ROOT/'Suivi_Appel_offre.Report'/pbir['datasetReference']['byPath']['path']).resolve() != MODEL.parent.resolve():
        errors.append('Référence PBIR au modèle incorrecte')
    return {'tables':len(tables),'pages_visibles':len(visible),'pages_masquees':len(pages)-len(visible),
            'visuels':len(all_visuals),'json_lus':json_count,'references_champs':field_checks,
            'liens_navigation_signets':links,'erreurs':errors,'points_a_verifier_desktop':warnings}


def compare_backup(path):
    before = {p.relative_to(path).as_posix():p for p in path.rglob('*') if p.is_file()}
    after = {p.relative_to(ROOT).as_posix():p for p in ROOT.rglob('*') if p.is_file()}
    changed = sorted(name for name in before.keys() & after.keys()
                     if hashlib.sha256(before[name].read_bytes()).digest() != hashlib.sha256(after[name].read_bytes()).digest())
    return {'modifies':changed,'ajoutes':sorted(after.keys()-before.keys()),'supprimes':sorted(before.keys()-after.keys())}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--backup',type=Path)
    args = parser.parse_args()
    report = check_structure()
    if args.backup: report['comparaison_sauvegarde'] = compare_backup(args.backup.resolve())
    print(json.dumps(report,ensure_ascii=True,indent=2))
    if report['erreurs']: raise SystemExit(1)


if __name__ == '__main__':
    main()
