"""Contrôles hors moteur : fichiers PBIR/TMDL et règle métier sur la copie Excel.

Aucun DAX ni Power Query exécuté. Aucune donnée du modèle/source modifiée.
Usage : python scripts/verifier_delais_reponse.py
"""
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from itertools import product
from zipfile import ZipFile
from xml.etree import ElementTree as ET
import json
import re
import ast
import operator
import argparse
from functools import lru_cache

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / 'Suivi_Appel_offre.SemanticModel/definition/tables'
PAGES = ROOT / 'Suivi_Appel_offre.Report/definition/pages'
PAGE = PAGES / 'd31a1500000000000001'
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def delay_before(start, end):
    """Référence indépendante : énumération strictement après J0."""
    if start is None or end is None or end < start:
        return None
    return sum((start + timedelta(days=n)).weekday() < 5
               for n in range(1, (end-start).days+1))


def deadline_before(start):
    if start is None:
        return None
    current, count = start, 0
    while count < 5:
        current += timedelta(days=1)
        count += current.weekday() < 5
    return current


def easter_reference(year):
    """Comput de Gauss, indépendant du comput Meeus/Jones/Butcher du DAX."""
    cycle, four, seven, century = year % 19, year % 4, year % 7, year // 100
    lunar = (15-(13+8*century)//25+century-century//4) % 30
    solar = (4+century-century//4) % 7
    epact = (19*cycle+lunar) % 30
    correction = (2*four+4*seven+6*epact+solar) % 7
    offset = epact+correction
    if (epact == 29 and correction == 6) or (epact == 28 and correction == 6 and cycle > 10):
        offset -= 7
    return date(year, 3, 22)+timedelta(days=offset)


@lru_cache(maxsize=None)
def holidays(year):
    easter = easter_reference(year)
    return frozenset([date(year, month, day) for month, day in
                      [(1, 1), (5, 1), (5, 8), (7, 14), (8, 15), (11, 1), (11, 11), (12, 25)]]
                     + [easter+timedelta(days=n) for n in (1, 39, 50)])


def working_day(day):
    return day.weekday() < 5 and day not in holidays(day.year)


def delay(start, end):
    if start is None or end is None or end < start:
        return None
    return sum(working_day(start+timedelta(days=n)) for n in range(1, (end-start).days+1))


def deadline(start):
    if start is None:
        return None
    current, count = start, 0
    while count < 5:
        current += timedelta(days=1)
        count += working_day(current)
    return current


def calendar_bounds(dates, fallback_year):
    valid = [d for d in dates if d is not None]
    return (date(min(valid).year if valid else fallback_year, 1, 1),
            date((max(valid).year if valid else fallback_year)+1, 12, 31))


def generated_holidays(year):
    """Lecture des expressions arithmétiques du TMDL, évaluées hors moteur.

    L'évaluateur AST accepte seulement nombres, noms et opérations du comput.
    Il n'exécute ni le DAX, ni du code arbitraire issu des fichiers.
    """
    source = (TABLES/'Calendrier ouvré France.tmdl').read_text(encoding='utf-8-sig')
    env = {'Annee': year}
    def evaluate(expression):
        def visit(node):
            if isinstance(node, ast.Constant):
                assert isinstance(node.value, int)
                return node.value
            if isinstance(node, ast.Name): return env[node.id]
            if isinstance(node, ast.BinOp):
                left, right = visit(node.left), visit(node.right)
                if isinstance(left, date) and isinstance(node.op, ast.Add):
                    return left+timedelta(days=right)
                operation = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul}[type(node.op)]
                return operation(left, right)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert not node.keywords
                function = {'MOD': operator.mod, 'QUOTIENT': operator.floordiv, 'DATE': date}[node.func.id]
                return function(*(visit(n) for n in node.args))
            raise AssertionError(ast.dump(node))
        return visit(ast.parse(expression.strip(), mode='eval').body)
    computus_names = {'Cycle19','Siecle','AnneeSiecle','Siecle4','SiecleReste4','CorrectionLune','CorrectionSiecle','Epacte','Annee4','AnneeReste4','CorrectionJour','CorrectionEpacte','BasePaques','Paques'}
    for name, expression in re.findall(r'^\s*VAR (\w+) = (.+)$', source, re.M):
        if name in computus_names:
            env[name] = evaluate(expression)
    records = [(name, evaluate(expression)) for expression, name in re.findall(
        r'ROW \( "DateFerie", (.+), "NomFete", "([^"]+)" \)', source)]
    assert len(records) == 11
    return records


def check_holidays():
    expected = {
        2026: ['01/01/2026','06/04/2026','01/05/2026','08/05/2026','14/05/2026','25/05/2026','14/07/2026','15/08/2026','01/11/2026','11/11/2026','25/12/2026'],
        2027: ['01/01/2027','29/03/2027','01/05/2027','08/05/2027','06/05/2027','17/05/2027','14/07/2027','15/08/2027','01/11/2027','11/11/2027','25/12/2027'],
    }
    for year, dates in expected.items():
        assert [d.strftime('%d/%m/%Y') for _, d in generated_holidays(year)] == dates
    # Vérification des fêtes mobiles et collisions de fêtes, hors années de l'extrait.
    for year in range(1900, 2400):
        actual = {d for _, d in generated_holidays(year)}
        assert actual == holidays(year), year
    assert len(holidays(2008)) == 10  # Ascension et 1er mai le même jour.
    assert date(2026, 8, 17) not in holidays(2026)
    assert date(2027, 8, 16) not in holidays(2027)
    assert date(2026, 4, 3) not in holidays(2026)  # Vendredi saint local exclu.
    assert date(2026, 12, 26) not in holidays(2026)
    assert date(2026, 5, 27) not in holidays(2026)  # Particularité outre-mer exclue.
    return {year: [{name: d.strftime('%d/%m/%Y')} for name, d in generated_holidays(year)] for year in expected}


def check_business_examples():
    monday = date(2026, 10, 5)
    for start, end, expected in [
        (monday, monday+timedelta(days=7), 5),
        (monday+timedelta(days=4), monday+timedelta(days=7), 1),
        (monday, monday, 0),
        (monday, monday+timedelta(days=8), 6),
        (None, monday, None), (monday, None, None),
        (monday, monday-timedelta(days=1), None),
    ]:
        assert delay(start, end) == expected
    # Vérification de l'équivalence de NETWORKDAYS inclusif moins J0 ouvré.
    # Cette comparaison mathématique ne lance pas la fonction DAX.
    for weekday in range(7):
        start = monday + timedelta(days=weekday)
        for days in range(41):
            end = start + timedelta(days=days)
            inclusive = sum((start+timedelta(days=n)).weekday() < 5
                            for n in range(days+1))
            assert inclusive - int(start.weekday() < 5) == delay_before(start, end)
        candidates = [start+timedelta(days=n) for n in range(1, 8)
                      if (start+timedelta(days=n)).weekday() < 5]
        assert candidates[4] == deadline(start)
        assert delay(start, deadline(start)) == 5
    assert delay(datetime(2026, 10, 5, 23, 50).date(),
                 datetime(2026, 10, 5, 0, 10).date()) == 0
    cases = [('03/04/2026','07/04/2026',1),('30/04/2026','04/05/2026',1),
             ('13/07/2026','15/07/2026',1),('14/08/2026','17/08/2026',1),
             ('24/12/2026','04/01/2027',5)]
    parse = lambda s: datetime.strptime(s, '%d/%m/%Y').date()
    for start, end, expected in cases:
        assert delay(parse(start), parse(end)) == expected
    for start, end in [('03/04/2026','13/04/2026'),('13/07/2026','21/07/2026'),('24/12/2026','04/01/2027')]:
        assert deadline(parse(start)) == parse(end)
    for day in [date(2026,4,6), date(2026,8,15), date(2026,10,14)]:
        assert delay(day, day) == 0
    assert delay(date(2026,4,30), date(2026,5,1)) == 0
    assert delay(date(2026,7,13), date(2026,7,14)) == 0
    assert delay(date(2026,7,14), date(2026,7,15)) == 1
    assert calendar_bounds([], 2028) == (date(2028,1,1),date(2029,12,31))
    assert calendar_bounds([None,None], 2028) == calendar_bounds([], 2028)
    assert calendar_bounds([date(2024,12,31),date(2027,1,4)], 2028) == (date(2024,1,1),date(2028,12,31))
    # Calendrier partagé matérialisé en Python : comparaison à la référence itérative.
    first, last = date(2025,1,1), date(2031,12,31)
    calendar = [first+timedelta(days=n) for n in range((last-first).days+1)
                if working_day(first+timedelta(days=n))]
    from bisect import bisect_right
    checks = 0
    for n in range((date(2030,12,31)-first).days+1):
        start = first+timedelta(days=n)
        after_start = bisect_right(calendar, start)
        assert calendar[after_start+4] == deadline(start)
        assert deadline(start) >= deadline_before(start)
        for days in [0,1,7,10,40]:
            end = start+timedelta(days=days)
            current = bisect_right(calendar,end)-after_start
            assert current == delay(start,end) <= delay_before(start,end)
            if delay_before(start,end) <= 5: assert current <= 5
            checks += 1
    return checks


def read_source():
    """Lecture seule du XLSX local, avec la bibliothèque standard."""
    with ZipFile(ROOT/'data/REPORTING_2026.xlsx') as archive:
        strings = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            strings = [''.join(e.itertext()) for e in ET.fromstring(
                archive.read('xl/sharedStrings.xml')).findall('s:si', NS)]
        book = ET.fromstring(archive.read('xl/workbook.xml'))
        rels = {e.attrib['Id']: e.attrib['Target'] for e in ET.fromstring(
            archive.read('xl/_rels/workbook.xml.rels'))}
        sheet = next(e for e in book.find('s:sheets', NS)
                     if e.attrib['name'] == 'SUIVI')
        target = rels[sheet.attrib[
            '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]
        path = target.lstrip('/') if target.startswith('/') else 'xl/'+target
        rows = []
        for row in ET.fromstring(archive.read(path)).findall('s:sheetData/s:row', NS):
            cells = {}
            for cell in row.findall('s:c', NS):
                key = re.sub(r'\d', '', cell.attrib['r'])
                value = cell.find('s:v', NS)
                value = value.text if value is not None else None
                kind = cell.attrib.get('t', 'n')
                if kind == 's' and value is not None:
                    value = strings[int(value)]
                elif kind == 'inlineStr':
                    value = ''.join(cell.find('s:is', NS).itertext())
                cells[key] = (value, kind)
            rows.append(cells)
        headers = {key: (value or '').strip() for key, (value, _) in rows[0].items()}
        return [{label: row.get(key, (None, 'n')) for key, label in headers.items()}
                for row in rows[1:]]


def parse_date(cell):
    """Contrôle indépendant, pas un émulateur du parseur Power Query."""
    value, kind = cell
    if value is None or not value.strip():
        return None, 'Absente'
    try:
        if kind == 'e':
            return None, 'Erreur source'
        if kind == 'n':
            result = (datetime(1899, 12, 30)+timedelta(days=float(value))).date()
        elif re.fullmatch(r'\d{1,2}/\d{1,2}/\d{1,4}', value.strip()):
            day, month, year = map(int, value.strip().split('/'))
            result = date(year, month, day)
        else:
            result = datetime.fromisoformat(value).date()
        if not 2000 <= result.year <= datetime.now(timezone.utc).year+1:
            return None, 'Année incohérente'
        return result, 'Valide'
    except (ValueError, OverflowError):
        return None, 'Erreur de conversion'


def classify(row, calculation=delay):
    start, start_check = parse_date(row["DATE D'EMISSION"])
    end, end_check = parse_date(row['DATE DE REPONSE'])
    problem = (start_check != 'Valide' or end_check not in ('Valide', 'Absente')
               or (start is not None and end is not None and end < start))
    result = calculation(start, end) if not problem else None
    qualification = ('Dates à vérifier' if problem else 'Sans date de réponse'
                     if end_check == 'Absente' else 'Dans le délai'
                     if result <= 5 else 'Hors délai')
    return dict(row=row, start=start, end=end, delay=result,
                qualification=qualification, missing=end_check == 'Absente')


def aggregates(rows):
    evaluated = [r for r in rows if r['delay'] is not None]
    within = sum(r['qualification'] == 'Dans le délai' for r in rows)
    late = sum(r['qualification'] == 'Hors délai' for r in rows)
    assert within + late == len(evaluated)
    assert all(r['qualification'] in ('Dans le délai', 'Hors délai') for r in evaluated)
    return {
        'lignes': len(rows), 'evaluables': len(evaluated), 'dans_delai': within,
        'hors_delai': late, 'sans_date_reponse': sum(r['missing'] for r in rows),
        'dates_a_verifier': sum(r['qualification'] == 'Dates à vérifier' for r in rows),
        'moyenne': sum(r['delay'] for r in evaluated)/len(evaluated) if evaluated else None,
        'taux': within/len(evaluated) if evaluated else None,
    }


def check_files():
    # Les descriptions TMDL utilisent /// devant l'objet, jamais description:.
    for path in TABLES.glob('*.tmdl'):
        lines = path.read_text(encoding='utf-8-sig').splitlines()
        for index, line in enumerate(lines):
            assert not re.match(r'^\s*description\s*:', line), (path.name, index+1)
            if line.lstrip().startswith('///'):
                next_line = lines[index+1]
                assert next_line.lstrip().startswith(('///', 'column ', 'measure ', 'table ', 'hierarchy ', 'level ')), (path.name, index+1)
                assert len(line)-len(line.lstrip()) == len(next_line)-len(next_line.lstrip()), (path.name, index+1)
    data = (TABLES/'Données.tmdl').read_text(encoding='utf-8-sig')
    measures = (TABLES/'_Mesures.tmdl').read_text(encoding='utf-8-sig')
    assert 'Table.Distinct' not in data
    assert 'DISTINCTCOUNT' not in measures
    assert 'Table.AddIndexColumn' in data
    assert '[STATUT] <> "Supprimé" and [STATUT] <> null and [STATUT] <> ""' in data
    assert data.count("ALL ( 'Calendrier ouvré France' )") == 2
    assert data.count("'Calendrier ouvré France'[Est jour ouvré]") == 2
    assert "'Calendrier ouvré France'[Date] <= Reponse" in data
    assert data.count("'Calendrier ouvré France'[Date] > Emission") == 2
    assert 'NETWORKDAYS' not in data
    assert 'DateTime.From(Lecture[Value], "fr-FR")' in data
    assert 'DIVIDE ( [Nb réponses dans le délai], [Nb réponses évaluables] )' in measures
    added_measures = measures[measures.index("\tmeasure 'Nb réponses évaluables'"):measures.index('\tcolumn Column')]
    assert 'REMOVEFILTERS' not in added_measures and 'ALL (' not in added_measures
    fields = {'Données': set(re.findall(r"^\tcolumn (?:'((?:[^']|'')*)'|([^\s=]+))", data, re.M)),
              '_Mesures': set(re.findall(r"^\tmeasure '((?:[^']|'')*)'", measures, re.M))}
    fields['Données'] = {quoted.replace("''", "'") if quoted else plain for quoted, plain in fields['Données']}
    meta = json.loads((PAGES/'pages.json').read_text(encoding='utf-8'))
    assert meta['pageOrder'].count(PAGE.name) == 1
    assert meta['activePageName'] in meta['pageOrder']
    assert meta['landingPageName'] in meta['pageOrder']
    page = json.loads((PAGE/'page.json').read_text(encoding='utf-8'))
    assert page['displayName'] == 'Délais de réponse'
    visuals = []
    for path in sorted((PAGE/'visuals').rglob('visual.json')):
        obj = json.loads(path.read_text(encoding='utf-8'))
        assert obj['name'] == path.parent.name
        pos = obj['position']
        assert 0 <= pos['x'] and pos['x']+pos['width'] <= page['width']
        assert 0 <= pos['y'] and pos['y']+pos['height'] <= page['height']
        visual = obj['visual']
        visuals.append(visual)
        for role in visual.get('query', {}).get('queryState', {}).values():
            for projection in role['projections']:
                f = next(iter(projection['field'].values()))
                assert f['Property'] in fields[f['Expression']['SourceRef']['Entity']]
    counts = Counter(v['visualType'] for v in visuals)
    assert counts['cardVisual'] == 6 and counts['hundredPercentStackedBarChart'] == 1
    assert counts['slicer'] == 3 and counts['textbox'] == 3 and counts['tableEx'] == 1
    slicers = [v['query']['queryState']['Values']['projections'][0]['field']['Column']['Property']
               for v in visuals if v['visualType'] == 'slicer']
    assert set(slicers) == {'Date émission jour', 'LIEU DE LA PRESTATION', 'ENTITE'}
    detail = next(v for v in visuals if v['visualType'] == 'tableEx')
    assert detail['query']['queryState']['Values']['projections'][0]['field']['Column']['Property'] == 'ID ligne besoin'
    chart = next(v for v in visuals if v['visualType'] == 'hundredPercentStackedBarChart')
    assert set(p['field']['Measure']['Property'] for p in chart['query']['queryState']['Y']['projections']) == {'Nb réponses dans le délai','Nb réponses hors délai'}
    assert len(chart['query']['queryState']['Tooltips']['projections']) == 4
    assert 'Jours ouvrés : hors week-ends et jours fériés nationaux français. Jour d’émission exclu.' in json.dumps(visuals, ensure_ascii=False)
    calendar = (TABLES/'Calendrier ouvré France.tmdl').read_text(encoding='utf-8-sig')
    assert 'WEEKDAY ( [Date], 2 ) <= 5 && NOT ( [Férié national] )' in calendar
    assert 'YEAR ( DerniereDate ) ) + 1' in calendar
    assert 'IF ( ISBLANK ( PremiereDate ), YEAR ( TODAY () ), YEAR ( PremiereDate ) )' in calendar
    assert '\tisHidden' in calendar
    assert 'Web.Contents' not in calendar and 'https://' not in calendar
    assert "ref table 'Calendrier ouvré France'" in (TABLES.parent/'model.tmdl').read_text(encoding='utf-8-sig')
    relationships_path = TABLES.parent/'relationships.tmdl'
    relationships = relationships_path.read_text(encoding='utf-8-sig') if relationships_path.exists() else ''
    assert 'Calendrier ouvré France' not in relationships
    for path in ROOT.glob('Suivi_Appel_offre.Report/definition/**/*.json'):
        json.loads(path.read_text(encoding='utf-8-sig'))
    return len(visuals)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, help='Rapport JSON hors moteur')
    args = parser.parse_args()
    calendar_checks = check_business_examples()
    holiday_dates = check_holidays()
    visual_count = check_files()
    all_rows = read_source()
    source_rows = [r for r in all_rows if r['STATUT'][0] not in ('Supprimé', None, '')]
    rows = [classify(r) for r in source_rows]
    before_rows = [classify(r, delay_before) for r in source_rows]
    before, after = aggregates(before_rows), aggregates(rows)
    for key in ('lignes','evaluables','sans_date_reponse','dates_a_verifier'):
        assert before[key] == after[key]
    changed_delays = changed_deadlines = newly_within = 0
    for old, new in zip(before_rows,rows):
        assert (old['delay'] is None) == (new['delay'] is None)
        if old['delay'] is not None:
            assert new['delay'] <= old['delay']
            changed_delays += new['delay'] < old['delay']
            if old['qualification']=='Dans le délai': assert new['qualification']=='Dans le délai'
            newly_within += old['qualification']=='Hors délai' and new['qualification']=='Dans le délai'
        if new['start'] is not None:
            assert deadline(new['start']) >= deadline_before(new['start'])
            changed_deadlines += deadline(new['start']) > deadline_before(new['start'])
    dahs = Counter(r['DAH'][0] for r in source_rows)
    # Répétitions conservées, jamais regroupées pour compter les besoins.
    assert len(rows) == sum(dahs.values())
    axes = [sorted({r['row'][name][0] or '' for r in rows})
            for name in ('LIEU DE LA PRESTATION', 'ENTITE')]
    months = sorted({r['start'].month for r in rows if r['start'] is not None})
    filter_checks = 0
    for place, entity, month in product([None]+axes[0], [None]+axes[1], [None]+months):
        filtered = [r for r in rows
                    if (place is None or (r['row']['LIEU DE LA PRESTATION'][0] or '') == place)
                    and (entity is None or (r['row']['ENTITE'][0] or '') == entity)
                    and (month is None or (r['start'] is not None and r['start'].month == month))]
        a = aggregates(filtered)
        assert a['taux'] is None or 0 <= a['taux'] <= 1
        filter_checks += 1
    report = {
        'controle': 'Hors moteur DAX/M ; copie locale Excel lue uniquement',
        'visuels': visual_count, 'cas_calendaires_complementaires': 287,
        'combinaisons_filtres': filter_checks, 'references_DAH_distinctes': len(dahs),
        'references_DAH_repetees': sum(n > 1 for n in dahs.values()),
        'resultats_reference_copie_locale': aggregates(rows),
        'qualifications': dict(Counter(r['qualification'] for r in rows)),
        'avant_sans_feries': before, 'apres_avec_feries': after,
        'delais_reduits': changed_delays, 'echeances_reculees': changed_deadlines,
        'nouveaux_besoins_conformes': newly_within,
        'cas_calendrier_2025_2030': calendar_checks,
        'annees_comput_verifiees': '1900 à 2399 (500 années)',
        'feries_verifies_service_public': holiday_dates,
    }
    if args.output:
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
