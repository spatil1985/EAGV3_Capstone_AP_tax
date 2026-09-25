UC-01 — The 180-day rule (build this first)
Plain English: If we bought something from a supplier and claimed a tax credit for the GST we paid on it, but then we never actually pay that supplier within 180 days, the law says: "give that tax credit back, plus 18% interest." Nobody in the current system checks for this because it's stuck between two departments — the payments team doesn't think about tax, and the tax team doesn't watch unpaid bills.

Example: We buy ₹1,00,000 of steel, claim ₹18,000 GST credit on it. Six months later, we still haven't paid the steel vendor. The agent should say: "Warning — you owe the government ₹18,000 back, plus interest, because you never paid this bill."

Why it's first: it applies to literally every kind of business (school, factory, clinic — all of them), no competitor product checks for this, and the "shape" of its output (a warning row) gets reused by two of Geetha's use cases later. So getting this one right sets the template for others.

UC-05 — Duplicate vendor payment (your original core mission)
Plain English: Is any vendor accidentally being paid twice for the same thing?

Example — the real bug you already found: A vendor "Apex Metals" had a recurring monthly bill for $8,500 internet service. But the system's scheduler was broken and created a new $8,500 bill every single day instead of once a month. Your original detection logic (same vendor + same amount within 3 days) would have falsely flagged legitimate monthly retainer clients as "duplicates" too — that's 3 false alarms it created. The fix: instead of just "same amount, similar date," check the actual document number + which financial year it's in + the vendor's tax ID. That's a much more precise fingerprint — real duplicates share it exactly; legitimate recurring bills don't.

UC-04 — Paying small vendors late (MSME 45-day rule)
Plain English: If a small supplier (officially registered as "MSME" — a small/micro business) isn't paid within 45 days, two bad things happen: (1) we owe them penalty interest, and (2) the tax office won't let us deduct that expense from our taxable income until we actually pay it. So being late costs us twice.

Example: A small hardware supplier invoices ₹10,00,000. We sit on it for 60 days. Now we owe penalty interest AND we can't claim that ₹10,00,000 as a business expense on this year's taxes yet. The agent's job: watch every MSME vendor's unpaid bills and warn before day 45.

UC-03 & UC-21 — "We forgot to tax ourselves" (Reverse Charge Mechanism / RCM)
Plain English: Normally, the seller charges you tax and pays the government. But for a few special categories — hiring a truck company, paying a lawyer, paying a company director, sponsoring an event, or paying any foreign vendor (like a US software subscription) — the law flips it: you, the buyer, must calculate and pay the tax yourself, even though the seller never charged you anything.

Example: Your company pays $50/month for a US-based SaaS tool (foreign vendor = "overseas"). Nobody charged you GST on that invoice because the seller is abroad. But Indian law says you owe that tax anyway. If your books don't reflect this, you have an undeclared tax liability sitting there, quietly growing. UC-03 catches this for domestic special cases (truck companies, lawyers, etc.), UC-21 catches it specifically for foreign vendors — same idea, applied twice, so you're building them together.

UC-06 — Did the approval process actually work? (newly unlocked)
Plain English: When a bill needs sign-off before payment, is the approval system actually enforcing its own rules? Specifically: did anyone approve their own bill (a classic fraud risk — no one should approve their own expense), and did approvals happen within the promised time window (SLA)?

Twist you found: the platform has a field that says "was this approval late?" (is_overdue) — but that field is wrong 74% of the time on the India data. So your agent can't trust the platform's own flag; it has to recalculate "was this actually late?" itself from the raw timestamps. That makes your agent more accurate than the platform's own UI — a good story to tell.

UC-09 — Did we deduct the right amount of TDS?
Plain English: TDS = "Tax Deducted at Source" — when you pay certain vendors (contractors, professionals, landlords), you're required to hold back a percentage and pay it directly to the tax office on their behalf, rather than paying them the full amount. Different vendor types have different percentages (contractors 194C, professional fees 194J, rent 194I).

Example: You pay a consultant ₹1,00,000 for professional services. The rule says deduct 10% TDS, so you should pay them ₹90,000 and send ₹10,000 to the tax department. If you got the percentage wrong, you accrue interest and risk having 30% of that expense disallowed at tax time. You found a real bug here too: on 9 real bills, the stored TDS amount is corrupted — it doesn't match percentage × base amount, and it's even causing negative totals. So your agent must recompute this itself rather than trusting the stored number.

UC-13 — Have we crossed the ₹50 lakh (5 million) threshold?
Plain English: Two tax rules kick in only after you've bought (or sold) more than ₹50 lakh worth of goods from/to the same party in a financial year. Below that line: no extra tax obligation. Cross it, even by ₹1: a new withholding obligation begins immediately, for the rest of the year.

Example: You've bought ₹49,80,000 of raw material from one supplier this year. Your next purchase from them is ₹40,000. That single purchase crosses the ₹50 lakh line — starting with that exact transaction, you must start withholding 0.1% TDS on everything you buy from them for the rest of the year. Nobody is currently tracking this running total per-vendor, so it's easy to miss the exact moment it flips on.
