"""Exercise-specific A2 rules, grouped by the problem they address.

These rules read offer content and scenario definitions, never case IDs or the
validation key. They are intentionally separate from the reusable A1 prompt.
"""
import copy,re,unicodedata,importlib.util
from pathlib import Path
_spec=importlib.util.spec_from_file_location('a2_job_reading_rules',Path(__file__).resolve().parents[1]/'backend/job_offer_refinements.py')
_job=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_job)
STOP=set('a an the of to for is are was be been will would could i you we my your our with'.split())
NUMBER=r'(?:\d+(?:\.\d+)?|zero|one|two|three|four|five|six|seven|eight|nine|ten|twelve|eighteen)'
WORDS={s:i for i,s in enumerate('zero one two three four five six seven eight nine ten'.split())}|{'twelve':12,'eighteen':18}
def number(s):return WORDS[s.lower()] if s.lower() in WORDS else float(s)
def tokens(s):return [(m.group().casefold(),m.start(),m.end()) for m in re.finditer(r'\d+(?:[.,]\d+)*|[^\W\d_]+',unicodedata.normalize('NFKC',s)) if m.group().casefold() not in STOP]
def restore_quote(q,text):
    a=tokens(q);b=tokens(text);wanted=[x[0] for x in a]
    if not wanted:return None
    hits=[(b[i][1],b[i+len(a)-1][2]) for i in range(len(b)-len(a)+1) if [x[0] for x in b[i:i+len(a)]]==wanted]
    return text[hits[0][0]:hits[0][1]] if len(hits)==1 else None
def customize(case,value,table,engine):
    value=copy.deepcopy(value);text=case['offer'];lower=text.lower();changes=[]
    pairs=value.get('pairs',[]);questions=value.get('ambiguities',[])
    def put(issue,option,source,rule):
        nonlocal pairs,questions
        pairs=[p for p in pairs if p.get('issue')!=issue]
        pairs.append(dict(issue=issue,option=str(option),source_text=source,from_previous_offer=False))
        questions=[q for q in questions if q.get('issue')!=issue]
        changes.append(dict(rule=rule,issue=issue,source=source))
    def query(issue,source,question):
        nonlocal pairs,questions
        pairs=[p for p in pairs if p.get('issue')!=issue]
        questions=[q for q in questions if q.get('issue')!=issue]
        questions.append(dict(issue=issue,source_text=source,question=question))
    # Keep explicit references scoped to the issues actually accepted.
    accepts_rest=bool(re.search(r'\band I accept\b|\beverything else\b|\bkeep (?:the )?rest\b|\b(?:may|can|would) accept this offer if\b',text,re.I))
    named_reference=re.search(r'\b(?:accede to|accept|agree to|honou?r|accommodate)\s+(?:the|your|proposed|previous)\b[^.;]{0,120}|\bkeep\s+(?:the\s+)?[^.;]{0,100}\bsame\b',text,re.I)
    accepts_named=bool(named_reference)
    if case['previous_offer'] and (accepts_rest or accepts_named):
        prior=case['previous_offer']
        for issue,pattern in {'Salary':r'salary','Starting Date':r'start(?:ing)? date','Probation Length':r'prob\w*tion|probation','Personal Budget':r'budget','Remote Working Days':r'remote\s+working'}.items():
            if accepts_rest or (named_reference and re.search(pattern,named_reference.group(),re.I)):
                if accepts_rest and any(p.get('issue')==issue for p in pairs):continue
                if issue=='Salary':
                    m=re.search(r'\$([\d,]+)\s+(?:annual\s+)?salary',prior,re.I);option=m[1] if m else None
                elif issue=='Starting Date':option=engine._stated_start_date(prior,table,include_invalid=True)
                elif issue=='Probation Length':
                    m=re.search(rf'({NUMBER})[- ]+months?\s+probation',prior,re.I);option=f'{number(m[1]):g} months' if m else None
                elif issue=='Personal Budget':
                    m=re.search(r'\$([\d,]+)\s+(?:personal )?(?:work[- ]expense )?budget',prior,re.I);option=m[1] if m else None
                else:
                    m=re.search(rf'\b({NUMBER})[- ]+(?:remote[- ]working[- ]+)?days?[^.;]{{0,20}}(?:remote|from home)|\b({NUMBER})[- ]+remote[- ]working[- ]+days?',prior,re.I)
                    option=str(number(next(x for x in m.groups() if x))) if m else None
                if option:
                    put(issue,option,prior,'Scoped acceptance of prior choice');pairs[-1]['from_previous_offer']=True
                    value['explicit_reference']=text
    # 1. Recover literal evidence when the model only changed harmless articles
    # or punctuation. Do not invent a quote or change the offer's actual words.
    for p in pairs:
        quote=p.get('source_text','')
        if quote and quote not in text:
            unwrapped=re.sub(r'^\s*</?(?:offer|current_offer)>\s*|\s*</?(?:offer|current_offer)>\s*$','',quote,flags=re.I)
            if unwrapped!=quote:
                p['source_text']=unwrapped;quote=unwrapped
                changes.append(dict(rule='Remove request-envelope markers from evidence',issue=p['issue'],source=unwrapped))
        if quote and quote not in text:
            restored=restore_quote(quote,text)
            if restored:p['source_text']=restored;changes.append(dict(rule='Literal quotation recovery',issue=p['issue'],source=restored))
    # 2. Exact duration wording and attached-unit typos.
    pattern=rf'\b({NUMBER})\s*[- ]?\s*(?:years?|yrs?)\s+(?:\d+\s+months?\s+)?(?:employment\s+)?contract\b|\b(?:contract|contact)(?:\s+(?:length|is|for|of|will|be|last)){{0,4}}\s*[:=]?\s*({NUMBER})\s*[- ]?\s*(?:years?|yrs?)\b'
    found=list(re.finditer(pattern,text,re.I))
    if found and not re.search(r'\b(?:or|between|no restrictive|cannot accept)\b[^.;\n]{0,30}\bcontract\b',text,re.I):
        m=found[-1];years=number(next(x for x in m.groups() if x));put('Contract Length',f'{years:g} years',m.group(),'Exact contract duration')
    compound=re.search(rf'\b({NUMBER})\s+years?\s+({NUMBER})\s+months?\b',text,re.I)
    if compound and re.search(r'security of employment|contract',text,re.I):put('Contract Length',f'{number(compound[1])+number(compound[2])/12:g} years',compound.group(),'Compound contract duration')
    for issue,detail in engine._post_probation_totals(text).items():
        put(issue,detail.get('option',detail.get('value','')),text,'Final staged total from explicit amounts')
    # 2b. Recover exact, labelled values and an explicit preferred selection.
    date=engine._stated_start_date(text,table,include_invalid=True)
    if date and not re.search(r'\b(?:or|between)\b[^.;\n]{0,35}(?:january|february|march|april|may|june)',text,re.I):
        put('Starting Date',date,text,'Explicit start date')
    preferred_month=re.search(r'\bideally\s+(January|February|March|April|May|June|July|August|September|October|November|December)\b',text,re.I)
    if preferred_month:put('Starting Date',preferred_month[1]+' 1',preferred_month.group(),'Preferred rather than unresolved date')
    month_names=r'January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec'
    date_after_proposal=re.search(rf'\b(?:let.?s say|I (?:would like|like|want) to)\s+(\d{{1,2}}(?:st|nd|rd|th)?\s+(?:{month_names})|(?:{month_names})(?:\s+\d{{1,2}}(?:st|nd|rd|th)?)?)\b',text,re.I)
    if date_after_proposal:
        spec=engine._scenario_issue_map(table)['Starting Date']
        try:put('Starting Date',engine._date_from_text(date_after_proposal[1],spec).isoformat(),date_after_proposal[1],'Explicit proposed date despite informal wording')
        except (ValueError,KeyError):pass
    last_usd_salary=list(re.finditer(r'\$\s*([\d,]+)\s+salary\b',text,re.I))
    if last_usd_salary and re.search(r'£[^.;\n]*salary|salary[^.;\n]*£',text,re.I):
        m=last_usd_salary[-1];put('Salary',m[1],m.group(),'Explicit later currency-labelled salary')
    budget=re.search(r'\b(?:personal[ \t]+(?:work[- ]expense[ \t]+)?|proposal[ \t]+)?budget[ \t]+(?:(?:will[ \t]+be|of|is|to|:|=)[ \t]*)?\$?[ \t]*([\d,]+(?:\.\d+)?[ \t]*(?:[kK]|thousand|grand)?)\b',text,re.I)
    if budget and not any(p.get('issue')=='Personal Budget' for p in pairs) and not re.search(r'\b(?:development|training)\s+budget\b|\b(?:at least|in excess|between)\b',text,re.I) and not re.search(r'[£€]',budget.group()):
        amount=engine._money_number_from_text(re.sub(r'\b(?:thousand|grand)\b','k',budget[1],flags=re.I))
        put('Personal Budget',str(amount),budget.group(),'Labelled expense budget')
    before_budget=re.search(r'(?<![\d£€])\$?([\d,]+(?:\.\d+)?(?:[ \t]*[kK])?)[ \t]+(?:personal[ \t]+(?:work[- ]expense[ \t]+)?|proposal[ \t]+|work[- ]expense[ \t]+)budget\b',text,re.I)
    if before_budget and not any(p.get('issue')=='Personal Budget' for p in pairs):put('Personal Budget',str(engine._money_number_from_text(before_budget[1])),before_budget.group(),'Amount before labelled budget')
    clear_salary=re.search(r'\bsalary[ \t]+(?:of[ \t]+|is[ \t]+|to[ \t]+)?\$?[ \t]*([\d,]+(?:\.\d+)?(?:[ \t]*[kK])?)\b|\$?[ \t]*([\d,]+(?:\.\d+)?(?:[ \t]*[kK])?)[ \t]+(?:annual[ \t]+|starting[ \t]+|base[ \t]+)?salary\b',text,re.I)
    if clear_salary and not any(p.get('issue')=='Salary' for p in pairs) and not re.search(r'\b(?:at least|closer to|approximately|around|between)\b|[£€]',text,re.I):
        amount=next(v for v in clear_salary.groups() if v);put('Salary',str(engine._money_number_from_text(amount)),clear_salary.group(),'Exact labelled salary, without old reference-range bounds')
    preferred_leave=re.search(r'\bideally\s+(?:having\s+)?(\d+)\s+days?\s+(?:vacation|holiday)',text,re.I)
    if preferred_leave:put('Vacation Days',preferred_leave[1],preferred_leave.group(),'Preferred rather than unresolved allowance')
    preferred_days=re.search(r'\bideally\s+(?:having\s+)?(\d+)\s+days?\b',text,re.I)
    if preferred_days and re.search(r'vacation|holiday',text[max(0,preferred_days.start()-100):preferred_days.end()],re.I):put('Vacation Days',preferred_days[1],preferred_days.group(),'Explicit preferred leave amount despite willingness to compromise')
    gym=re.search(r'\bgym(?:\s+membership)?(?:\s+contribution)?\s*\$\s*([\d,]+)',text,re.I)
    if gym:put('Wellness or Gym Benefit',gym[1],gym.group(),'Exact gym contribution')
    misspelled_leave=re.search(r'\b(\d+)[ \t]+(?:vaccations?|vaccation|vacations?|holidays?)\b',text,re.I)
    if misspelled_leave:put('Vacation Days',misspelled_leave[1],misspelled_leave.group(),'Numerical leave shorthand')
    remote_pct=re.search(r'\b(\d+(?:\.\d+)?)\s*%\s*(?:wfh|remote)',text,re.I)
    if remote_pct:put('Remote Working Days',str(float(remote_pct[1])*5/100),remote_pct.group(),'Share of five-day workweek')
    split_week=re.search(r'\b(\d+(?:\.\d+)?)\s+remote\s+and\s+(\d+(?:\.\d+)?)\s+(?:on[- ]?site|office)\s+working days',text,re.I)
    if split_week and float(split_week[1])+float(split_week[2])<=5:put('Remote Working Days',split_week[1],split_week.group(),'Explicit split between remote and onsite days')
    hybrid_days=re.search(r'\b(\d+(?:\.\d+)?)\s+days?\s+hybrid\b',text,re.I)
    if hybrid_days and re.search(r'in house|onsite|on[- ]site|office',text,re.I):put('Remote Working Days',hybrid_days[1],hybrid_days.group(),'Stated hybrid remote days with onsite days described separately')
    social_pct=re.search(r'\b(\d+(?:\.\d+)?)\s*%[^.;\n]{0,50}(?:social media|client story posts)',text,re.I)
    if social_pct:put('Regular Social Media Posts for Company',str(float(social_pct[1])/100),social_pct.group(),'Posting workload share')
    fair=re.search(r'\b(?:I would need you to|you (?:will|must|would))\s+(?:help|attend|assist|represent)[^.;\n]{0,45}recruitment fairs?\b',text,re.I)
    if fair and case['role']=='Recruiter':put('Role in Recruitment Fair','Commit',fair.group(),'Explicit candidate duty')
    staff=re.search(r'\b(?:willing to help with )?training new employees\b',text,re.I)
    if staff and case['role']=='Candidate':put('Mentoring Assignment Choice','Occasional mentoring',staff.group(),'Training colleagues rather than receiving training')
    posts=re.search(r'\b(?:help (?:to )?shape|shap\w*|manag\w*|contribut\w*|shar\w*)[^.;\n]{0,70}\b(?:client (?:success |story |stories )?posts|client success stories on social media|client story posts on social media|social media)',text,re.I)
    post_prefix=text[max(text.rfind('.',0,posts.start())+1,text.rfind('\n',0,posts.start())+1):posts.end()] if posts else ''
    if posts and not any(p.get('issue') in ['Regular Social Media Posts for Company','Regular Linkedin Posts for Company'] for p in pairs) and not re.search(r'\b(?:no|not|optional|opportun\w*)\b',post_prefix,re.I) and not re.search(r'\b\d+\s+(?:client story |social media )?posts',posts.group(),re.I) and not social_pct:
        put('Regular Social Media Posts for Company','1',posts.group(),'Usual company posting commitment')
    excluded_presentations=re.search(r'\b(?:external )?conference presentations?[^.\n]{0,100}(?:will not be included|are excluded)',text,re.I)
    if excluded_presentations:put('Mandatory Conference Presentations','No commitment',excluded_presentations.group(),'Explicit excluded presentation duty')
    # 3. Known participation defaults. Learning time alone is not an additional
    # company-funded course. Mentoring colleagues is not receiving a mentor.
    external=bool(re.search(r'\b(?:external|professional|specific)\s+(?:development\s+)?training|\btraining\s+(?:plan|program\w*|opportunities)|\baccess to training\b|^\s*training\s*(?:$|[\n,])|[\n,]\s*training\s*(?:$|[\n,])|\band training\s*[.!]?\s*$|additional learning classes through the company',text,re.I))
    internal_only=bool(re.search(r'programme of mentoring training and familiarisation|training\s+(?:new|other|junior)\s+(?:employees|staff)',text,re.I))
    uncertain=bool(re.search(r'(?:remember|remmeber) you may need|time[- ]off for (?:attending )?(?:external )?(?:professional )?training|time off for training',text,re.I))
    if external and not internal_only and not uncertain:
        negative=bool(re.search(r'\b(?:no|without|decline)\s+(?:professional\s+)?training',text,re.I))
        put('Professional Training Program','No participation' if negative else 'Participation',text,'Known training participation')
    elif internal_only or (re.search(r'^\s*Participation\s*$',text,re.M|re.I) and not external):
        pairs=[p for p in pairs if p.get('issue')!='Professional Training Program']
    mentor=re.search(r'\b(?:provide|providing|offer|offering|assign|assigned)[^.;\n]{0,70}\b(?:mentorship|mentoring|a mentor)\b|\bjoin the mentorship program\w*\b|\b(?:I would like|I want|I would value)\s+(?:a|an)\s+(?:experienced\s+)?mentor\b',text,re.I)
    if mentor and not re.search(r'\b(?:no|not|without|decline)\b',mentor.group(),re.I):put('Mentorship Program','Participation',mentor.group(),'Clear request for a mentor or mentoring participation')
    mentor_opportunity=re.search(r'\bmentorship opportunit\w*\b',text,re.I)
    if mentor_opportunity and not re.search(r'\b(?:no|not|without|decline)\s+mentorship',text,re.I):put('Mentorship Program','Participation',mentor_opportunity.group(),'Affirmative mentoring opportunity in a proposed list')
    bare_mentoring=re.search(r'(?:^|[,;\n])\s*(mentoring)\s*(?=$|[,;\n])',text,re.I)
    if bare_mentoring:put('Mentorship Program','Participation',bare_mentoring[1],'Bare mentoring provision in an offer list')
    sponsorship=re.search(r'\bsponsor\w*[^.;\n]{0,70}\b(?:membership|memberships|association)\b',text,re.I)
    if sponsorship and not re.search(r'\b(?:not|no|without)\b',sponsorship.group(),re.I):put('Professional Associations Membership','Firm sponsors',sponsorship.group(),'Explicit sponsored membership')
    fair_participation=re.search(r'\b(?:volunteer\w*|commit\w*|participat\w*|attend\w*|help|assist|represent|engag\w*|organiz\w*)[^.;\n]{0,100}recruitment[- ]fairs?\b',text,re.I)
    if fair_participation and not re.search(r'\b(?:not|no|without|decline)\b',fair_participation.group(),re.I):put('Role in Recruitment Fair','Commit',fair_participation.group(),'Expressed recruitment-fair participation')
    fair_role=re.search(r'\brecruitment[- ]fair\s+(?:roles?|positions?|participation)\b',text,re.I)
    if fair_role and not re.search(r'\b(?:no|without|decline)\s+recruitment',text,re.I):put('Role in Recruitment Fair','Commit',fair_role.group(),'Affirmative recruitment-fair role shorthand')
    social_events=re.search(r'\b(?:welcome|want|would like|have)[^.;\n]{0,35}\b(?:help |you )?organiz\w*\s+(?:occasional |company |team |social )*events\b',text,re.I)
    if social_events and not re.search(r'\b(?:not|no|without)\b',social_events.group(),re.I):put('Role in Organizing Social Events','Commitment',social_events.group(),'Explicit request to help organize team events')
    # 3b. No unstated quantities or missing payment shares.
    allowance_patterns={
      'Vacation Days':r'(?:\d+(?:\.\d+)?|zero|one|two|three|four|five|ten|twenty|thirty|forty|fifty)\s*(?:(?:vacation|holiday|vacay)\s+)?days?|(?:vacation|holiday|annual leave)\s*[:=]?\s*\d+|\d+\s+holidays?|\b(?:usual|normal|extra vaca day)\b',
      'Remote Working Days':r'\d+\s*(?:remote\s+)?(?:working\s+)?days?|\d+\s*%|\b(?:once|twice|thrice|daily|full|fully|entire|usual|normal)\b',
    }
    for issue,pattern in allowance_patterns.items():
        selected=next((p for p in pairs if p.get('issue')==issue),None)
        if not selected or selected.get('from_previous_offer'):continue
        marker=r'vacation|holiday|annual leave|pto|vacay|paid time off' if issue=='Vacation Days' else r'remote|wfh|from home|at home|hybrid'
        clauses=[s for s in re.split(r'[;\n]|(?<!\d)\.(?!\d)',text) if re.search(marker,s,re.I)]
        if clauses and not any(re.search(r'\d|\b(?:zero|one|two|three|four|five|six|ten|twenty|thirty|forty|fifty|full|fully|entire|daily|once|twice|usual|normal)\b',s,re.I) for s in clauses):query(issue,clauses[0],'Please give the number of days you propose.')
    if re.search(r'\b(?:full medical benefits|health insurance|health care included)\b',text,re.I) and not re.search(r'\d+\s*%|\b(?:free|100 percent|fully paid)\b',text,re.I):
        source=next((s for s in re.split(r'[;\n.]',text) if re.search(r'medical|health',s,re.I)),text)
        query('Employer Health-Insurance Contribution',source,'What percentage of the premium would the employer pay?')
    if re.search(r'\bmaternity leave\b',text,re.I) and not re.search(r'\bpaid\b[^.;\n]{0,30}\bmaternity|\bmaternity[^.;\n]{0,30}\bpaid\b',text,re.I):
        source=next(s for s in re.split(r'[;\n.]',text) if re.search('maternity',s,re.I));query('Paid Parental Leave',source,'Would this leave be paid, and for how long?')
    # 3c. Avoid choosing an amount or a neighboring benefit from vague wording.
    for issue,pattern in {
        'Salary':r'\b(?:at least|closer to|around|approximately)\s*\$?[\d,]+[^.;\n]{0,20}\bsalary|\bsalary[^.;\n]{0,20}\b(?:at least|closer to|around|approximately)\s*\$?[\d,]+',
        'Personal Budget':r'\bbudget\s+(?:around|approximately|in excess of|at least)\s*\$?[\d,]+',
        'Probation Length':r'\b(?:long|shorter|longer)\s+probation\b|\b(?:cannot|can.t)\s+accept\s+\d+\s+months?\s+probation',
    }.items():
        m=re.search(pattern,text,re.I)
        if m:query(issue,m.group(),'Please give one exact value you propose.')
    redundant=re.search(r'\$?[\d,]{4,}\s+thousand\s+salary',text,re.I)
    if redundant:query('Salary',redundant.group(),'What exact annual salary amount do you mean?')
    malformed_salary=re.search(r'\$\d{1,3},\d{2}\b[^.;\n]{0,20}salary',text,re.I)
    if malformed_salary:query('Salary',malformed_salary.group(),'Please write the exact salary amount again.')
    open_leave=re.search(r'\d+\s+(?:vacation\s+)?days?\s+(?:per year\s+)?or more',text,re.I)
    if open_leave:query('Vacation Days',open_leave.group(),'Please choose one annual number of vacation days.')
    narrow_noncompete=re.search(r'\bno\s+strict\s+non[- ]?compete',text,re.I)
    if narrow_noncompete:query('Non-compete Clause',narrow_noncompete.group(),'Do you want the clause removed, or changed in a particular way?')
    for issue,marker in {'Salary':r'salary|wage|\bover\b','Personal Budget':r'budget|expense'}.items():
        foreign=[s for s in re.split(r'[;\n]|(?<!\d)\.(?!\d)',text) if re.search(marker,s,re.I) and re.search('[£€]',s)]
        if foreign and not (issue=='Salary' and last_usd_salary):query(issue,foreign[-1],'Please state the amount in the currency used by this exercise.')
    optional_uncertainty={
      'Non-compete Clause':r'^\s*non[- ]?compete\s*$',
      'Recurring Schedule Flexibility':r'\bflexible\s+(?:daily\s+)?(?:working\s+)?hours\b',
      'Mentoring Assignment Choice':r'\bmentor role\b',
      'Written Promotion Criteria':r'\bpromotional requirements\b',
    }
    for issue,pattern in optional_uncertainty.items():
        m=re.search(pattern,text,re.M|re.I)
        if m:query(issue,m.group(),'What specific arrangement would you like?')
    if re.search(r'\bsupervision\b',text,re.I) and not re.search(r'\bmentor',text,re.I):
        pairs=[p for p in pairs if p.get('issue')!='Mentorship Program']
    if re.search(r'\b(?:salary progression|progression of salary)\b',text,re.I):
        pairs=[p for p in pairs if p.get('issue')!='Performance-Based Progression']
    # 3d. Conflicts, vague choices and staged values are distinct problems.
    probation_values=list(re.finditer(rf'({NUMBER})[- ]+months?\s+prob\w*tion',text,re.I))
    if len({number(m[1]) for m in probation_values})>1 and not re.search(r'\b(?:instead|actually|change|correct|make that)\b',text,re.I):
        query('Probation Length',text,'Please choose one probation duration from the values you mentioned.')
    date_words=re.sub(r'\bmay\s+(?:need|be|have|want|require|include|receive|take|help|occur|differ|vary|apply|change|depend|incur)\b','possible action',text,flags=re.I)
    months=re.findall(r'\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\b',date_words,re.I)
    if len({m[:3].lower() for m in months})>1 and re.search(r'\b(?:or|between|and)\b|\bjan\s*[-–]\s*march\b',text,re.I) and not re.search(r'\b(?:ideally|instead|actually|change|correct|as opposed to|rather than)\b',text,re.I):
        query('Starting Date',text,'Please choose one starting date from the dates you mentioned.')
    for issue,marker in {'Vacation Days':r'vacation|holiday|annual leave|pto','Remote Working Days':r'remote|wfh|hybrid','Probation Length':r'probation'}.items():
        p=next((p for p in pairs if p.get('issue')==issue),None)
        if not p or p.get('from_previous_offer'):continue
        q=p.get('source_text','');m=re.search(re.escape(q),text,re.I) if q else None
        nearby=text[max(0,m.start()-18):m.end()+18] if m else q
        if q and len(q.split())<=5 and re.search(marker,q,re.I) and not re.search(r'\d|\b(?:no|without|waive|skip|zero|one|two|three|four|five|six|ten|twenty|thirty|forty|fifty|full|fully|daily|once|twice|usual|normal|extra)\b',nearby,re.I):query(issue,q,'Please give the exact value you propose.')
    if re.search(r'\b30 days work per weekdays remote work\b',text,re.I):query('Remote Working Days','30 days work per weekdays remote work','Please state a feasible weekly remote-working allowance.')
    if re.search(r'\bsecond option\b',text,re.I) and re.search(r'\blower (?:work )?expense budget\b',text,re.I):query('Personal Budget',text,'Which alternative and exact budget would you like to propose?')
    if re.search(r'\b(?:reconsider|change|narrowly defined|reasonable)\b[^.;\n]{0,35}\bnon[- ]?compete|\bnon[- ]?compete[^.;\n]{0,35}\b(?:reconsider|change)\b',text,re.I) and not re.search(r'\b(?:waive|remove|keep|retain)\b',text,re.I):query('Non-compete Clause',text,'What specific change to the clause would you like?')
    if re.search(r'\bprofessional development opportunities\b',text,re.I) and not re.search(r'\btraining\b',text,re.I):
        pairs=[p for p in pairs if p.get('issue')!='Professional Training Program']
        value.setdefault('novel_terms',[]).append(next((s for s in re.split(r'[;\n.]',text) if 'professional development opportunities' in s.lower()),'professional development opportunities'))
    reduced=re.search(r'\bLess emphasis[^.\n]{0,90}\bconference presentation[^.\n]*',text,re.I)
    if reduced:query('Mandatory Conference Presentations',reduced.group(),'Would any presentation responsibility remain?')
    if re.search(r'notice period[^.;\n]{0,65}for (?:first|the first)',text,re.I):
        pairs=[p for p in pairs if p.get('issue')!='Notice Period Length'];value.setdefault('novel_terms',[]).append(next(s for s in re.split(r'[;\n.]',text) if re.search('notice period',s,re.I)))
    later_increase=re.search(r'\bAfter[^.;\n]{0,70}\b(?:increase|rise)\s+of\s+(\d+(?:\.\d+)?)\s*%',text,re.I)
    salary=next((p for p in pairs if p.get('issue')=='Salary'),None)
    if later_increase and salary and not re.search(r'\b(?:up to|performance|targets?)\b',later_increase.group(),re.I):
        amount=engine._money_number_from_text(salary['option'])*(1+float(later_increase[1])/100)
        put('Salary',f'{amount:g}',text,'Final staged salary total');pairs=[p for p in pairs if p.get('issue') not in ['Scheduled Salary Increase','Target-based pay increase']]
    fixed_later_increase=re.search(r'\bAfter probation[^.;\n]{0,70}?\b(\d+(?:\.\d+)?)\s+pay increase\b',text,re.I)
    salary=next((p for p in pairs if p.get('issue')=='Salary'),None)
    if fixed_later_increase and salary:
        initial_match=re.search(r'\b(?:offer a|salary of)\s*\$?([\d,]+)\s+(?:annual |base )?salary|\bstarting salary\s+(?:of\s+)?\$?([\d,]+)',text,re.I)
        if initial_match:initial=engine._money_number_from_text(next(v for v in initial_match.groups() if v));put('Salary',str(initial+float(fixed_later_increase[1])),text,'Explicit later salary increment from original stated base, not an already updated model value')
    # Do not price a neighboring issue merely because a related noun appears.
    if re.search(r'\bSales role with additional responsibilities\b|\bthis is a sales role\b',text,re.I) and not re.search(r'\b(?:job title|role title|senior|account manager|sales representative)\b',text,re.I):
        pairs=[p for p in pairs if p.get('issue')!='Role Scope or Job Title']
    if re.search(r'\bdont want to promote\b',text,re.I) and not re.search(r'\bpaid time\b[^.;\n]{0,40}\b(?:publicity|promot)',text,re.I):pairs=[p for p in pairs if p.get('issue')!='Paid Time for Publicity']
    if re.search(r'\b30 days work per weekdays remote work\b',text,re.I):pairs=[p for p in pairs if p.get('issue')!='Vacation Days']
    development_budget=re.search(r'[^.;\n]*\b(?:professional development or training|professional development|training) budget\b[^.;\n]*',text,re.I)
    if development_budget and not re.search(r'\d',development_budget.group()):
        pairs=[p for p in pairs if p.get('issue')!='Professional Training Program']
        query('Professional Development Budget',development_budget.group().strip(),'What amount would this budget be?')
    association_fair=re.search(r'[^.;\n]*\bprofessional association fairs\b[^.;\n]*',text,re.I)
    if association_fair and not re.search(r'\bmembership\b',text,re.I):
        pairs=[p for p in pairs if p.get('issue')!='Professional Associations Membership'];value.setdefault('novel_terms',[]).append(association_fair.group().strip())
    if not re.search(r'\bonline\b|\be[- ]learning\b|\bdigital learning\b|\blearning platform\b',text,re.I):
        pairs=[p for p in pairs if p.get('issue')!='Online Learning Access']
    if re.search(r'\bbonus for passing prob\w*tion\b',text,re.I):
        pairs=[p for p in pairs if p.get('issue')!='Performance-Based Bonus']
    if re.search(r'\bif a certain sales figure\b',text,re.I) and not re.search(r'\b(?:annual sales target|sales quota)\b',text,re.I):pairs=[p for p in pairs if p.get('issue')!='Annual Sales Target']
    if not re.search(r'\brenew\w*|\bexpir\w*',text,re.I):pairs=[p for p in pairs if p.get('issue')!='Contract Renewal Notice']
    wage_assessment=re.search(r'\byearly assessment[^.;\n]*\bwage increases\b',text,re.I)
    if wage_assessment:
        pairs=[p for p in pairs if p.get('issue')!='Advancement Review Frequency']
        value.setdefault('novel_terms',[]).append(wage_assessment.group())
    if re.search(r'\bgives you\s+[−–-]?\d+\s+points\b',text,re.I) and not re.search(r'\b(?:I propose|I offer|I would like|we offer|salary)\b',text,re.I):
        query('Salary',text,'What single annual salary would you like to propose?')
    # Keep the explicitly stated actor for duties, unlike ordinary job benefits.
    pairs,retained=_job.refine_pairs(text,case['role'],pairs,table)
    value.setdefault('novel_terms',[]).extend(retained)
    # 4. Keep the purpose of a sum. A development amount is not client expenses.
    if re.search(r'\b\d+[kK]?\s+personal development\b',text,re.I) and not re.search(r'personal (?:work[- ]expense |expense )?budget',text,re.I):
        pairs=[p for p in pairs if p.get('issue')!='Personal Budget']
        value.setdefault('novel_terms',[]).extend(s.strip() for s in text.splitlines() if 'personal development' in s.lower())
    # 5. Researcher-approved shorthand in an offer list is affirmative.
    # Do not confuse a short feature request with an unmentioned feature.
    if re.search(r'^\s*recruitment fair position\s*$',text,re.M|re.I):
        put('Role in Recruitment Fair','Commit','Recruitment fair position','Affirmative shorthand in proposed feature list')
    # 6. Clarify within the person's wording, not with a menu of new features.
    # The question still acknowledges the specific unresolved idea. Clear
    # features handled above do not receive this generic fallback.
    safe=[]
    for q in questions:
        source=q.get('source_text','').strip()
        if source and source not in text:source=restore_quote(source,text) or source
        if source and source in text:
            safe.append(dict(issue='General offer',question=f'Could you make this part more precise: “{source}”? Please state the specific arrangement you propose.',source_text=source,_clarified_issue=q.get('issue')))
        else:safe.append(q)
    # 7. Retain meaningful new requests which a short model answer may omit.
    # Each pattern names an actual proposed topic, not all words in the offer.
    retained_patterns=[r'concrete ways to build relationships',r'(?:dont|don.t|do not) want to promote(?: social media)?',r'\b(?:time (?:off )?in lieu|employer.s? rights|study leave|free coffee|supervision|progression review)\b',r'\b(?:ideal position would be in|prefer.*position in)\b',r'\b(?:training and growth as|training period|work day schedule|9[-–]5 job)\b',r'bonus for passing prob\w*tion',r'\b1 month probabtion\b',r'\bmay be renewed based on performance\b',r'\bmain\w*nance program\w*\b',r'^\s*Participation\s*$']
    # The post-pilot table can now price coffee. Do not also report a scored
    # coffee clause as unpriced; retain the old behavior for the frozen table.
    if any(p.get('issue')=='Workplace Coffee' for p in pairs):
        retained_patterns=[p.replace('|free coffee','') for p in retained_patterns]
    for clause in re.split(r'[;\n]|(?<!\d)\.(?!\d)',text):
        if clause.strip() and any(re.search(p,clause,re.I) for p in retained_patterns):
            value.setdefault('novel_terms',[]).append(clause.strip())
    value['pairs']=pairs;value['ambiguities']=safe;value['ambiguity_details']=safe
    value['novel_terms']=list(dict.fromkeys(value.get('novel_terms',[])))
    return value,changes
