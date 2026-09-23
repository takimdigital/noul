import json
import os
import sys
sys.path.insert(0, 'D:/laya')
from noul import decide

cases = [
    ('The client capped the project budget at $12,000 and asked for weekly status reports every Monday.', 'How often are status reports?', 'ANSWERABLE'),
    ('The client capped the project budget at $12,000 and asked for weekly status reports every Monday.', 'What is the CEO phone number?', 'NOT ANSWERABLE'),
    ('The project deadline is March 15, 2026 and the team uses agile methodology with 2-week sprints.', 'What methodology does the team use?', 'ANSWERABLE'),
    ('The project deadline is March 15, 2026 and the team uses agile methodology with 2-week sprints.', 'What is the project budget?', 'NOT ANSWERABLE'),
    ('The warehouse stores 15,000 units across 3 regional distribution centers in Algiers, Oran, and Constantine.', 'How many distribution centers are there?', 'ANSWERABLE'),
    ('The warehouse stores 15,000 units across 3 regional distribution centers in Algiers, Oran, and Constantine.', 'What is the warehouse temperature?', 'NOT ANSWERABLE'),
    ('Our API rate limit is 1000 requests per minute per API key, with burst allowance up to 1500.', 'What is the rate limit per minute?', 'ANSWERABLE'),
    ('Our API rate limit is 1000 requests per minute per API key, with burst allowance up to 1500.', 'What database do we use?', 'NOT ANSWERABLE'),
    ('The meeting is scheduled for 3 PM CET on Thursday in Conference Room B, with mandatory attendance for all team leads.', 'What time is the meeting?', 'ANSWERABLE'),
    ('The meeting is scheduled for 3 PM CET on Thursday in Conference Room B, with mandatory attendance for all team leads.', 'What is the lunch menu?', 'NOT ANSWERABLE'),
    ('The flight departs at 08:45 from Gate C12 and arrives at 11:30 local time, with a layover in Istanbul.', 'What gate does the flight depart from?', 'ANSWERABLE'),
    ('The flight departs at 08:45 from Gate C12 and arrives at 11:30 local time, with a layover in Istanbul.', 'What is the hotel booking reference?', 'NOT ANSWERABLE'),
    ('The medication dosage is 500mg twice daily for 7 days, with food, and no alcohol during treatment.', 'How many times per day should the medication be taken?', 'ANSWERABLE'),
    ('The medication dosage is 500mg twice daily for 7 days, with food, and no alcohol during treatment.', 'What is the patient blood type?', 'NOT ANSWERABLE'),
    ('The contract renews automatically on January 1 each year with 30-day notice required for cancellation.', 'When does the contract renew?', 'ANSWERABLE'),
    ('The contract renews automatically on January 1 each year with 30-day notice required for cancellation.', 'What is the office Wi-Fi password?', 'NOT ANSWERABLE'),
    ('The server runs Ubuntu 24.04 LTS with 64 GB RAM and 2 TB NVME storage in the EU-West-1 region.', 'What operating system does the server run?', 'ANSWERABLE'),
    ('The server runs Ubuntu 24.04 LTS with 64 GB RAM and 2 TB NVME storage in the EU-West-1 region.', 'What is the server IP address?', 'NOT ANSWERABLE'),
    ('The invoice total is €4,750 including 19% VAT, due within 30 days of receipt, payable by bank transfer only.', 'What is the invoice total?', 'ANSWERABLE'),
    ('The invoice total is €4,750 including 19% VAT, due within 30 days of receipt, payable by bank transfer only.', 'What is the shipping method?', 'NOT ANSWERABLE'),
    ('The restaurant is open Tuesday-Sunday 11AM-11PM, closed Mondays, accepts reservations at +213 00 00 00 00.', 'What days is the restaurant closed?', 'ANSWERABLE'),
    ('The restaurant is open Tuesday-Sunday 11AM-11PM, closed Mondays, accepts reservations at +213 00 00 00 00.', 'What is the dress code?', 'NOT ANSWERABLE'),
    ('The package weighs 2.5 kg and measures 30x20x15 cm, ships via express delivery within 2 business days.', 'What is the package weight?', 'ANSWERABLE'),
    ('The package weighs 2.5 kg and measures 30x20x15 cm, ships via express delivery within 2 business days.', 'What is the package color?', 'NOT ANSWERABLE'),
    ('The exam starts at 09:00 AM sharp, duration 3 hours, bring ID and admission ticket, no calculators allowed.', 'How long is the exam?', 'ANSWERABLE'),
    ('The exam starts at 09:00 AM sharp, duration 3 hours, bring ID and admission ticket, no calculators allowed.', 'What is the passing grade?', 'NOT ANSWERABLE'),
    ('The policy covers up to $50,000 per incident with a $500 deductible, excludes flood and earthquake damage.', 'What is the deductible?', 'ANSWERABLE'),
    ('The policy covers up to $50,000 per incident with a $500 deductible, excludes flood and earthquake damage.', 'What is the policyholder date of birth?', 'NOT ANSWERABLE'),
    ('The train leaves Platform 7 at 14:20, arrives at 16:45, carriage B seats 12-15 are reserved.', 'What platform does the train leave from?', 'ANSWERABLE'),
    ('The train leaves Platform 7 at 14:20, arrives at 16:45, carriage B seats 12-15 are reserved.', 'What is the dining car menu?', 'NOT ANSWERABLE'),
    ('The offer expires on December 31, 2026 at 23:59 UTC, use code SAVE20 at checkout for 20% off.', 'What discount does the code provide?', 'ANSWERABLE'),
    ('The offer expires on December 31, 2026 at 23:59 UTC, use code SAVE20 at checkout for 20% off.', 'What is the shipping address?', 'NOT ANSWERABLE'),
    ('The office has 45 workstations across 3 floors, open 8AM-6PM weekdays, access requires keycard after hours.', 'How many workstations are there?', 'ANSWERABLE'),
    ('The office has 45 workstations across 3 floors, open 8AM-6PM weekdays, access requires keycard after hours.', 'What is the parking fee?', 'NOT ANSWERABLE'),
    ('The warranty covers manufacturing defects for 24 months from purchase date, does not cover accidental damage.', 'How long does the warranty last?', 'ANSWERABLE'),
    ('The warranty covers manufacturing defects for 24 months from purchase date, does not cover accidental damage.', 'What is the store manager name?', 'NOT ANSWERABLE'),
    ('The event capacity is 500 attendees, doors open at 6PM, keynote at 7:30PM, networking reception follows at 9PM.', 'What time does the keynote start?', 'ANSWERABLE'),
    ('The event capacity is 500 attendees, doors open at 6PM, keynote at 7:30PM, networking reception follows at 9PM.', 'What is the catering menu?', 'NOT ANSWERABLE'),
    ('The loan interest rate is 5.5 percent APR fixed for 3 years, early repayment allowed without penalty after 12 months.', 'What is the interest rate?', 'ANSWERABLE'),
    ('The loan interest rate is 5.5 percent APR fixed for 3 years, early repayment allowed without penalty after 12 months.', 'What is the bank SWIFT code?', 'NOT ANSWERABLE'),
    ('The shipment contains 250 units of model XJ-9, manufactured in Vietnam, HS code 8471.60.00.', 'What is the HS code?', 'ANSWERABLE'),
    ('The shipment contains 250 units of model XJ-9, manufactured in Vietnam, HS code 8471.60.00.', 'What is the warehouse humidity level?', 'NOT ANSWERABLE'),
]

import os
EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
GT_PATH = os.path.join(EVAL_DIR, 'eval_ground_truth.jsonl')

with open(GT_PATH, 'w') as gt:
    for i, (ctx, q, truth) in enumerate(cases):
        gt.write(json.dumps({'index': i, 'context': ctx, 'question': q, 'ground_truth': truth}) + '\n')

print(f'wrote {len(cases)} eval pairs to eval_ground_truth.jsonl')
print(f'ANSWERABLE: {sum(1 for c in cases if c[2]=="ANSWERABLE")}')
print(f'NOT ANSWERABLE: {sum(1 for c in cases if c[2]=="NOT ANSWERABLE")}')
