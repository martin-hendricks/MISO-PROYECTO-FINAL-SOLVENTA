/** A date-only value stays valid through that local calendar day. Timestamps compare as instants. */
export function offerExpired(venceEn: string | null | undefined, now: Date): boolean {
  if (!venceEn) return true;
  const dateOnly = /^(\d{4})-(\d{2})-(\d{2})$/.exec(venceEn);
  if (dateOnly) {
    const end = new Date(Number(dateOnly[1]), Number(dateOnly[2]) - 1, Number(dateOnly[3]), 23, 59, 59, 999);
    return Number.isNaN(end.getTime()) || end < now;
  }
  const instant = new Date(venceEn);
  return Number.isNaN(instant.getTime()) || instant <= now;
}
