/* Score explicit form choices using only the assigned role's disclosed rules. */
function coordinate(value, rule) {
  if (rule.value_type === 'date') {
    if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) throw Error('Enter a complete calendar date.');
    const parsed = Date.parse(value + 'T00:00:00Z');
    if (!Number.isFinite(parsed) || new Date(parsed).toISOString().slice(0, 10) !== value) throw Error('Enter a valid calendar date.');
    return parsed / 86400000;
  }
  if (typeof value === 'boolean' || value === null || (typeof value !== 'number' && typeof value !== 'string')) throw Error('Enter one number.');
  if (typeof value === 'string' && !value.trim()) throw Error('Enter one number.');
  const number = Number(value);
  if (!Number.isFinite(number)) throw Error('Enter one finite number.');
  return number;
}

export function scoreChoice(ownRole, issue, value) {
  const rule = ownRole.continuous_scoring?.[issue];
  if (!rule) {
    const option = ownRole.determinatescoretable?.[issue]?.find(row => row.option === value);
    if (!option) throw Error(`Choose one listed option for ${issue}.`);
    return option.score;
  }
  const number = coordinate(value, rule);
  if (rule.domain.min !== null && number < coordinate(rule.domain.min, rule)) throw Error(`${issue} is below its allowed minimum.`);
  if (rule.domain.max !== null && number > coordinate(rule.domain.max, rule)) throw Error(`${issue} is above its allowed maximum.`);
  const knots = rule.knots.map(k => [coordinate(k.value, rule), k.score]).sort((a,b) => a[0]-b[0]);
  if ((number < knots[0][0] || number > knots.at(-1)[0]) && rule.extrapolation !== 'linear') throw Error(`${issue} is outside its scoring range.`);
  let index = knots.findIndex((k,i) => i > 0 && number <= k[0]);
  if (index < 1) index = knots.length-1;
  const [left, right] = [knots[index-1], knots[index]];
  return left[1] + (number-left[0])/(right[0]-left[0])*(right[1]-left[1]);
}

export function scoreChoices(ownRole, choices, requiredIssues) {
  for (const issue of requiredIssues) if (!(issue in choices)) throw Error(`Please include ${issue}.`);
  const breakdown = Object.entries(choices).map(([issue,value]) => ({issue, value, score:scoreChoice(ownRole,issue,value)}));
  return {total:breakdown.reduce((sum,row) => sum+row.score,0),breakdown};
}
