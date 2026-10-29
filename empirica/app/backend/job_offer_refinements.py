"""Exercise-specific interpretation safeguards for the economical job scorer.

These rules read the submitted words, never a test ID or expected answer.
Uncertain additional features are retained without inventing choices or points.
The tutorial and fixed-choice conditions do not use these refinements.
"""
from __future__ import annotations
import re
from scenario_rules import is_fixed

def active(scenario):
    return (not is_fixed(scenario) and scenario.get('validation_profile') != 'tutorial'
            and {'Salary','Personal Budget','Starting Date'}.issubset(scenario.get('required_issues',[])))

def clauses(text):
    return [s.strip(' •\t') for s in re.split(r'[;\n]|(?<!\d)\.(?!\d)',text) if s.strip(' •\t')]

def scoring_examples(text):
    return (len(re.findall(r'\bgives?\s+you\b',text,re.I))>=3
            and bool(re.search(r'\bpoints?\b',text,re.I))
            and not re.search(r'\b(?:I|we)\s+(?:propose|offer|want|need|accept|would\s+like)\b',text,re.I))

FAIR=r'\b(?:p?recruitment|recruiting|careers?|hiring)[-\s]+fairs?\b'
DUTIES={'Role in Recruitment Fair':FAIR,
 'Role in Organizing Social Events':r'\b(?:team[-\s]?building|team|social)[-\s]+events?\b',
 'Regular Linkedin Posts for Company':r'\b(?:social[-\s]+media|linkedin|client[-\s]+stor(?:y|ies))\b',
 'Regular Social Media Posts for Company':r'\b(?:social[-\s]+media|linkedin|client[-\s]+stor(?:y|ies))\b',
 'Mentorship Program':r'\b(?:mentor|mentorship|mentoring)\b',
 'Professional Training Program':r'\b(?:external|professional)\s+training\b'}

def refine_pairs(text,role,pairs,scenario):
    """Resolve a few high-risk mappings before points are calculated."""
    if not active(scenario): return pairs,[]
    pairs=[dict(p) if isinstance(p,dict) else p for p in pairs]; notes=[]
    def omit(name,source):
        nonlocal pairs
        pairs=[p for p in pairs if not (isinstance(p,dict) and p.get('issue')==name)]
        if source and source not in notes:notes.append(source)
    # Explicit alternatives are not a promise to provide both benefits.
    alternative=re.search(r'\b(?:professional\s+)?training\s+or\s+(?:experienced\s+)?mentor\w*',text,re.I)
    if alternative:
        for name in ['Mentorship Program','Professional Training Program']:omit(name,alternative.group())
    if training_other_staff_only(text):
        omit('Professional Training Program',next(s for s in clauses(text) if re.search(r'\btraining\s+(?:new|other|junior)\s+(?:employees|staff|colleagues)\b',s,re.I)))
    # No numerical flexibility allowance is established by a bare adjective.
    if re.search(r'\bflexible\s+(?:work\s+)?schedule\b',text,re.I) and not re.search(r'\b\d+(?:\.\d+)?\s*(?:hours?|hrs?)\b',text,re.I):
        omit('Within-Week Schedule Flexibility',next(s for s in clauses(text) if re.search(r'\bflexible\s+(?:work\s+)?schedule\b',s,re.I)))
    ambiguous_probation=re.search(r'\b(?:\d+\s+months?\s+probation(?:ary)?\s+period\s+of\s+\d+\s+years?|probation\s+(?:of\s+)?\d+\s+months?\s+(?:or|and)\s+\d+\s+months?)\b',text,re.I)
    if ambiguous_probation:omit('Probation Length',ambiguous_probation.group())
    probation_years=(re.search(r'\bprobation(?:ary)?(?:[ \t]+period)?[ \t]*(?:of|:|=)?[ \t]*(\d+(?:\.\d+)?|one|two|half)[ \t-]+years?\b(?![ \t]+(?:employment[ \t]+)?contract\b)',text,re.I)
        or re.search(r'\b(\d+(?:\.\d+)?|one|two|half)[- \t]+years?[ \t]+probation(?:ary)?\b(?![ \t]*(?:(?:period|of)[ \t]+)*(?:\d+(?:\.\d+)?|one|two|three|four|five|six)[- \t]+months?\b)',text,re.I))
    if probation_years and re.search(r'\bcontract(?:[ \t]+length)?[ \t:]*$',text[:probation_years.start()],re.I):
        probation_years=None
    if probation_years:
        raw=probation_years.group(1).lower();months=12*({'one':1,'two':2,'half':.5}.get(raw) if raw in ('one','two','half') else float(raw))
        omit('Probation Length',probation_years.group())
        spec=next((x for x in scenario.get('issues',[]) if x.get('name')=='Probation Length'),{})
        if not ambiguous_probation and float(spec.get('min',0))<=months<=float(spec.get('max',6)):
            pairs.append(dict(issue='Probation Length',option=f'{months:g} months',confidence=1,source_text=probation_years.group(),source='exercise_unit_conversion'))
    for sentence in clauses(text):
        for name,marker in DUTIES.items():
            found=re.search(marker,sentence,re.I)
            if not found:continue
            before=sentence[:found.start()]
            # Use the closest explicit subject in this clause. Ordinary job
            # benefits remain the candidate's package; duties must keep their actor.
            subject=r'you|the\s+recruiter' if role=='Candidate' else r'I|we|the\s+recruiter'
            modal=r'(?:(?:to|will|would|can|must|should|need\s+to|am\s+willing\s+to|are\s+to)\s+)?'
            if name in ('Mentorship Program','Professional Training Program'):
                # The recipient matters, not the person offering the benefit.
                # Ordinary employment benefits refer to the candidate package,
                # even if a proposer writes from the other person's viewpoint.
                # Only an explicitly different beneficiary overrides that rule.
                actor_pattern=rf'\b(?:the\s+recruiter|the\s+hiring\s+manager)\s+{modal}(?:be\s+paired|receive|join|undergo|participate)\b'
            else:
                actor_pattern=rf'\b(?:{subject})\s+{modal}(?:not\s+)?(?:help|take\s+on|organis\w*|organiz\w*|represent\w*|volunteer|attend|oversee|collaborat\w*|share|shape|write)\b'
            actor_text=sentence if name in ('Mentorship Program','Professional Training Program') else before
            if ':' in sentence and found.start()<sentence.index(':'):
                actor_text=sentence.split(':',1)[1]
            wrong=bool(re.search(actor_pattern,actor_text,re.I))
            if wrong:
                omit(name,sentence)
        fair=re.search(FAIR,sentence,re.I)
        willing=re.search(r'\b(?:I\s+can\s+help|(?:I\s+am\s+)?willing\s+to\s+(?:help|volunteer)|I\s+(?:will|would)\s+(?:help|volunteer))\b',sentence,re.I)
        declined=bool(willing and re.search(r'\b(?:not|cannot|never)\s*$',sentence[max(0,willing.start()-15):willing.start()],re.I))
        qualified=bool(fair and re.search(r'\b(?:only\s+if|subject\s+to|optional|mutual\s+agreement)\b',sentence[willing.start() if willing else fair.start():fair.end()+65],re.I))
        if fair and willing and role=='Candidate' and not declined and not qualified:
            pairs=[p for p in pairs if not(isinstance(p,dict) and p.get('issue')=='Role in Recruitment Fair')]
            pairs.append(dict(issue='Role in Recruitment Fair',option='Commit',confidence=1,source_text=sentence,source='exercise_reading_rule'))
        if re.search(r'\b(?:\d+|one|two|three|four|five)\s+(?:(?:social[-\s]+media|linkedin|client[-\s]+story)\s+)?posts?\b',sentence,re.I) and re.search(r'\b(?:social[-\s]+media|linkedin)\b',sentence,re.I) and not re.search(r'\b(?:usual|normal|half|percent)\b|%',sentence,re.I):
            for name in ['Regular Linkedin Posts for Company','Regular Social Media Posts for Company']:omit(name,sentence)
    return pairs,notes

def training_other_staff_only(text):
    return (bool(re.search(r'\btraining\s+(?:new|other|junior)\s+(?:employees|staff|colleagues)\b',text,re.I))
            and not re.search(r'\b(?:external|professional)\s+training\b|\btraining\s+(?:plan|program\w*|course)\b',text,re.I))

TOPICS=[
 ('Professional Training Program',r'\b(?:external\s+training|professional\s+training|training\s+(?:plan|program\w*))\b'),
 ('Professional Associations Membership',r'\b(?:sponsored\s+membership|professional\s+association\w*|company\s+sponsored\s+membership)\b'),
 ('Work arrangement',r'\b(?:office\s+(?:days?|based|attendance)|office\b[^.;]{0,40}\bdays?|days?\s+(?:a\s+week\s+)?(?:in|at)\s+(?:the\s+)?office|office\s+and\s+home|remot\w*|work\w*\s+from\s+home)\b'),
 ('Vacation Days',r'\b(?:vacays?|vacations?|annual\s+leave|holidays?|time\s+off|days?\s+of[f]?)\b'),
 ('Contract Length',r'\b(?:contract|permanent\s+(?:role|employment))\b'),
 ('Progression review',r'\b(?:progression|progress|career|performance)\s+review\b'),
 ('Pay increase',r'\b(?:salary|pay)\s+(?:increase|rise|raise)\b|\bthen\s+increase\b'),
 ('Training other employees',r'\btraining\s+(?:new|other|junior)\s+(?:employees|staff|colleagues)\b'),
 ('Role in Organizing Social Events',r'\b(?:team|social|work|company|staff|team[-\s]?building)\s+events?\b'),
 ('Role in Recruitment Fair',FAIR),
]

def retain_unhandled(text,result,scenario):
    """Keep a source-grounded topic when no existing field handles it.

    This does not echo the entire offer: it checks separate named topics and
    keeps only the relevant clause. Acknowledgement is distinct from pricing.
    """
    if not active(scenario):return
    priced=result.get('valid_pairs',{})
    retained=' '.join([str(x) for x in result.get('novel_terms',[])]+[str(x.get('detail','')) for x in result.get('unpriced_details',[])])
    questions=' '.join(str(f.get('message','')) for f in result.get('findings',[]))
    for name,pattern in TOPICS:
        matches=[s for s in clauses(text) if re.search(pattern,s,re.I)]
        if not matches:continue
        if name in priced:continue
        if name=='Work arrangement' and 'Remote Working Days' in priced:continue
        if name=='Pay increase' and any(k in priced for k in ['Scheduled Salary Increase','Target-based pay increase']):continue
        if re.search(pattern,retained+' '+questions,re.I):continue
        for source in matches:
            if source in result.setdefault('novel_terms',[]):continue
            result['novel_terms'].append(source)
            result.setdefault('unpriced_details',[]).append({'detail':source,'meaning':'This additional request is retained without points; clarify its precise choice if needed.'})
            result['display_text']+='\nRecorded without points: '+source
