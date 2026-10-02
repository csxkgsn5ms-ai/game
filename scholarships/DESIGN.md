# ScholarPilot: design notes

ScholarPilot is a scholarship tool. It asks you a lot of questions once, finds the scholarships you qualify for, and does most of the work of applying to them. This file walks through how it was designed, step by step, using the engineering design process.

---

## Step 1: Define the problem

**Need.** Students leave a lot of scholarship money unclaimed. The reason usually isn't that they don't qualify. Applying is slow and repetitive: you type your name, address, GPA and activities into dozens of nearly identical forms, rewrite the same essay over and over, and lose track of deadlines.

**Goal.** Make applying to every scholarship you qualify for take a few minutes each, not an hour each.

**Problem statement.** *Design a tool that collects a student's information one time, works out which scholarships they're eligible for, and automates filling out and tracking the applications, while the student stays in control of what gets submitted under their name.*

## Step 2: Research (what existing tools do)

| Tool | What it does well | Where it falls short | What we borrowed |
|---|---|---|---|
| **Fastweb / Scholarships.com** | Large databases, matching by profile | Lots of ads and email spam, weak matches, no help applying | Profile-based matching |
| **Going Merry** | "Common App for scholarships": one profile, reused | Only works for scholarships on its own platform | One profile that feeds every application |
| **ScholarshipOwl** | Actually auto-applies | Paid subscription, and it only auto-applies to its own partner scholarships, which are mostly small sweepstakes | Auto-apply where it's allowed; flag no-essay awards |
| **Bold.org / Niche** | Simple no-essay scholarships | Low odds of winning; they're mostly lead generation | Separate category for "quick entries" |
| **Simplify / Teal (job autofill)** | Browser extension that fills any application form from your profile | Built for jobs | **The core idea**: one-click autofill on any website |
| **Common App** | Asks every question once, with a guided wizard and a progress bar | Colleges only | The long, step-by-step question wizard |
| **Scholly (now Sallie)** | Clean mobile matching UI | Small database, now owned by a lender | Showing why you match, at a glance |

**Main finding.** Nobody can legally and reliably press "Submit" on thousands of third-party scholarship sites for you:

1. Most real scholarships need a **unique essay, recommendation letters, a transcript, or a video**. A bot can't produce those honestly.
2. Many sites use **CAPTCHAs and log-ins**, and their terms of service **ban automated submissions**. Breaking those rules can disqualify you.
3. Applications usually end with **"I certify this is my own work."** Submitting AI-written essays without reading them puts the award at risk.
4. **Scholarship scams** target students who apply in bulk ("pay a fee", "give us your SSN or bank info").

So the tools that work automate **everything up to the Submit button** and leave the final click to you. That's the approach we chose.

## Step 3: Requirements and constraints

**Must have**
- R1: Ask as many questions as needed, but in small steps, with a progress bar, and save progress.
- R2: Match scholarships to the profile and explain *why* you qualify, don't qualify, or might qualify ("answer this question to find out").
- R3: Autofill application forms on any scholarship website in one click.
- R4: Reuse essays: store your essays by theme and suggest the right one for each prompt, with a word count check.
- R5: Track every application: status, deadline and documents needed.
- R6: Privacy. Your data stays on your device. No account, no server, no selling your info.
- R7: Works on a phone and a laptop.

**Constraints**
- C1: Free, no backend (hosted as a static page on GitHub Pages).
- C2: The student always reviews and submits. The tool never clicks Submit.
- C3: Scholarship rules change every year, so every listing says "verify on the official site", and you can add your own.

## Step 4: Brainstorm (three concepts)

| | Concept A: Full robot | Concept B: Copilot web app + autofill bookmarklet | Concept C: Spreadsheet + templates |
|---|---|---|---|
| How it works | Server with headless browsers that log in and submit for you | Web app holds your profile, matches and tracker; a bookmarklet fills forms on any site | Google Sheet of scholarships plus copy-paste text blocks |
| Automation | Highest (in theory) | High: matching, form filling, essay reuse, deadlines | Low |
| Cost | Servers, CAPTCHA-solving services | Free | Free |
| Risk | ToS violations, disqualification, stores your passwords | Low | Low |
| Build effort | Very high, breaks every time a site changes | Medium | Low |

## Step 5: Choose a concept (decision matrix)

Scores are 1 to 5 (5 is best), multiplied by weight.

| Criterion | Weight | A: Full robot | B: Copilot | C: Spreadsheet |
|---|---|---|---|---|
| Time saved per application | 5 | 5 → 25 | 4 → 20 | 2 → 10 |
| Safe for your eligibility / follows rules | 5 | 1 → 5 | 5 → 25 | 5 → 25 |
| Privacy | 4 | 1 → 4 | 5 → 20 | 4 → 16 |
| Cost | 3 | 1 → 3 | 5 → 15 | 5 → 15 |
| Reliability | 3 | 1 → 3 | 4 → 12 | 5 → 15 |
| Ease of use | 3 | 4 → 12 | 4 → 12 | 2 → 6 |
| **Total** | | **52** | **104** | **87** |

**Pick: Concept B.**

## Step 6: The plan

```
 ┌───────────────┐   ┌───────────────┐   ┌────────────────┐   ┌───────────────┐
 │ 1. Profile    │──▶│ 2. Matcher    │──▶│ 3. Apply queue │──▶│ 4. Tracker    │
 │ ~95 questions │   │ checks rules, │   │ ranked by $,   │   │ status,       │
 │ in 10 steps   │   │ shows reasons │   │ effort, due    │   │ deadlines,    │
 └──────┬────────┘   └───────────────┘   └───────┬────────┘   │ calendar file │
        │                                        │            └───────────────┘
        │            ┌───────────────┐   ┌───────▼────────┐
        └──────────▶ │ 5. Essay bank │──▶│ 6. Autofill    │──▶  YOU review + Submit
                     │ by theme      │   │ bookmarklet    │
                     └───────────────┘   └────────────────┘
```

**Modules**
1. **Profile wizard**: personal, background, school, test scores, money, activities, goals, references, preferences. Every answer is optional, and the matcher tells you which missing answers would unlock more matches.
2. **Matcher**: each scholarship has structured rules (grade level, minimum GPA, citizenship, background, major, state, income/Pell, age, memberships). Each rule comes back as pass, fail, or unknown, and the result is **Eligible**, **Maybe** (lists the missing answers) or **Not eligible** (says which rule failed).
3. **Apply queue**: eligible scholarships ranked by award size, how much work they take (based on your preference), and how soon they're due.
4. **Essay bank**: you write about 10 core essays once (leadership, adversity, career goals and so on). Each scholarship's essay themes are mapped to your essays. A "tailor prompt" button copies a ready-made request you can paste into ChatGPT or Claude to adapt *your* essay. You still edit the result.
5. **Autofill bookmarklet**: drag a button to your bookmarks bar. On any application page, click it and it fills name, contact info, address, birthday, school, GPA, test scores, major and similar fields. It highlights what it filled. **It never submits.**
6. **Tracker**: statuses (Not started → In progress → Submitted → Won / Not selected), a deadline countdown, a calendar export (.ics), and profile backup/restore (JSON).
7. **Scam guard**: built-in red-flag checks for scholarships you add yourself.

## Step 7: Judge the plan (critique before building)

| Risk / weakness | Severity | Fix in the design |
|---|---|---|
| Built-in scholarship list goes out of date (deadlines change every year) | High | Every card says "verify"; deadlines shown as a typical month; you can add or import scholarships |
| Autofill guesses the wrong field | Medium | Conservative matching rules; filled fields highlighted for review; never touches passwords, files or Submit buttons |
| The bookmarklet carries a copy of your data | Medium | It only includes form fields (no essays, no references' contact info by default); regenerate it after edits; don't share it |
| Long questionnaire makes people quit | Medium | 10 short steps, autosave, "skip" allowed, matcher shows what each answer unlocks |
| Data stored only in the browser can be lost | Medium | Export/import a backup file |
| Copying essays across applications is unethical when prompts differ | Medium | Word count and theme checks; the tailor prompt asks for adaptation, not a new essay; you must edit |
| Local and state scholarships aren't in a national list (these have the best odds) | High | "Local sources checklist" plus "Add scholarship" for awards from your counselor, community foundation, employer or credit union |
| "Auto-apply" expectation vs. reality | High | Said plainly in the app: it automates prep and filling; you submit |

**Verdict.** The plan meets R1–R7 within C1–C3. The biggest remaining limit is the size of the scholarship list. That's covered by import/add for now; a later version could pull listings from an API.

## Step 8: Build

Everything lives in one file: `scholarships/index.html` (no build step, no server). With GitHub Pages turned on for this repo, it's served at `/scholarships/`. `scholarships/test-form.html` is a fake application form for trying out autofill.

## Step 9: Test plan

| Test | How | Pass when |
|---|---|---|
| Matcher logic | Sample student profile vs. known rules (e.g. GPA 3.2 vs. Gates 3.3 minimum) | Correct Eligible / Maybe / Not eligible with the right reason |
| Autofill | Run the bookmarklet on `test-form.html` | Name, email, address, DOB, school, GPA, SAT and major filled; Submit not clicked |
| Persistence | Fill out the profile, reload the page | Answers are still there |
| Backup | Export, clear, import | Profile restored |
| Phone layout | 390px-wide viewport | No sideways scrolling; wizard usable |

**Results (first build):** all five passed in headless Chromium.
- Matcher: the sample student gets 23 eligible, 1 maybe and 17 not eligible. Gates with a 3.2 weighted GPA correctly returns "Needs weighted GPA 3.3+ (yours: 3.20)".
- Autofill: 18 fields filled on the practice form, including a state dropdown, a gender dropdown, a citizenship radio button and a first-gen dropdown. The parent email, essay, password, certify checkbox and Submit were correctly left alone.
- Persistence: answers survive a reload. Conditional questions (e.g. tribal enrollment) appear when relevant.
- Phone: every tab is exactly 390px wide, with no sideways scroll.

## Step 10: Iterate (next versions)

- Browser extension version of autofill (handles multi-page forms and doesn't need regenerating).
- Pull scholarship listings from a maintained data source, filtered by state.
- Built-in AI essay tailoring with the user's own API key.
- Reminder emails/notifications before deadlines.
- Shared counselor view for a whole school.

---

## Step 11: Second review and redesign (round 2)

An outside review (GPT) went through every scholarship and the code. Before changing anything, we checked its claims against published sources in October 2026. It was right on almost everything, with two exceptions: Golden Door Scholars doesn't include Indiana, and the review missed that Cameron Impact moved to high school juniors.

**What changed**

| Problem found | Fix |
|---|---|
| A deadline month alone can send you to a round that already closed | Each award now stores real `opens` / `closes` dates (or several `rounds`). Closed rounds are labeled and kept out of the apply queue. Undated awards say "date not posted yet" instead of guessing "this month". |
| Wrong rules on many awards (e.g. Cooke now needs a 3.75 GPA; Gates dropped its race requirement; APIA is open to all backgrounds; Horatio Alger's $25,000 award is juniors-only; Elks amounts changed) | All 41 entries updated; 9 added (NHS, Coolidge, Marine Corps Scholarship Foundation, Goldwater, Truman, Udall, HACER, Dream Award); directories like UNCF, Bold.org and state grants moved to a separate "Directories to search" list. |
| GPA was converted or swapped (weighted ↔ unweighted, 100-point → 4.0) | Uses only the exact GPA you entered. 100-point scales ask you for your transcript's 4.0 equivalent. |
| Pell eligibility was guessed from income | Only your FAFSA answer counts. Otherwise "Maybe". |
| Skipped answers counted as "not eligible" | Skipped = Maybe. Only an explicit "No" / "None" rules you out. |
| Age checked against today | Checked against the deadline when one is posted. |
| Ranking used headline maximums ($250,000 contests, drawings) | Ranks by a realistic typical award; drawings never enter the queue. |
| Autofill mixed clues from different labels, substituted related values, guessed date order | Reads one source at a time (autocomplete hint, label, placeholder, name, id); fills a text date only when the format is stated; never puts an income range in an exact-amount box; skips "eligible non-citizen", mailing (when different), parent and billing fields; shows a list of what it filled and how many fields it left for you. |
| New questions needed | College GPA, prior 4-year college, mailing address same?, LGBTQ+ ally option, Marine-parent option, "None of these" memberships. |

**Round 2 test results** (headless Chromium): 3.2 weighted GPA fails Gates; a 3.5 unweighted with Pell unknown is "Maybe" for Gates; a 100-point GPA is "Maybe" with a request for the 4.0 equivalent; an ally is eligible for Point; a skipped membership is "Maybe" and "None" is "Not eligible"; a Texas DACA student is correctly excluded from Golden Door. Autofill filled 19 fields on the practice form and correctly left the parent email, eligible-non-citizen question, exact-income box, essay, password and checkbox alone. A "Birth date (MM/DD/YYYY)" box initially got only the month; that bug was fixed and retested. No sideways scrolling at 390px.

**Still true:** award details change every year. Each card says when its date was checked; confirm on the official site before applying.

### Second opinion

To have another AI review this plan, paste this file into it with:

> "Act as a senior product engineer. Critique this design for a scholarship auto-apply tool. Find missing requirements, risky assumptions, legal/ToS problems, and features that would save the student the most time. Rank your suggestions by impact."
