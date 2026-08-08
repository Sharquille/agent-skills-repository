# Inference moves (Reasoning / Logic)

Moves for judging whether a conclusion actually follows from its evidence.
These mostly plug into TRACE's Apply and Check steps.

**Correlation vs. causation.** Two things co-occurring, or one following the
other in time, is evidence for a causal link but never establishes it alone.
*Diagnostic case*: "A store changed its sign and sales doubled the next
month. What can we conclude?" *Common failure*: treating "after" as "because,"
or inventing an unstated mechanism ("the new sign was more captivating") and
presenting it as a recorded fact.

**Falsifiability.** A real explanation implies something you should observe
if it's true, and rules out at least one thing you'd expect *not* to see if
it's true — an explanation compatible with literally any outcome isn't doing
any work. Ask "if my explanation is true, what should I see — and what would
count against it?" before trusting it.
*Diagnostic case*: "A laptop is slower the day after installing a browser
extension. What test would tell you whether the extension is responsible?"
*Common failure*: proposing a "test" that changes multiple variables at once,
which can't isolate the cause either way.

**Controlled comparison / confound isolation.** The cleanest evidence changes
one variable and holds everything else constant. Changing several things at
once (reinstall the OS, update drivers, *and* disable the extension) may fix
the problem but can't say which change did it.
*Diagnostic case*: same laptop scenario — "change only the extension's
enabled state vs. change several settings at once: which gives cleaner
evidence, and why?" *Common failure*: picking the multi-variable option
because it "covers more bases," missing that this destroys interpretability.

**Deduction vs. induction vs. abduction.** Deduction: the conclusion is
guaranteed by the premises (if valid). Induction: the conclusion is made
probable by a pattern of cases, never certain. Abduction: the conclusion is
the best available explanation for an observation, chosen among alternatives
— this is what most everyday "what can we conclude" questions actually call
for, and it's weaker than either learners usually assume.
*Diagnostic case*: "Every swan I've seen is white, so all swans are white" vs.
"If all swans were white, this one would be white; it is; therefore all swans
are white" — which is deduction, which is induction, and what's wrong with
the second one? *Common failure*: not noticing the second commits affirming
the consequent (a valid-*looking* form that isn't).

**Validity vs. soundness.** Soundness requires validity *plus* true
premises, so this only runs one direction: an argument can be valid but
unsound (true logical form, at least one false premise) — but never sound
while invalid. A separate, common trap: an argument can be invalid yet still
have a true conclusion; the conclusion being true doesn't retroactively make
the reasoning that reached it valid.
*Diagnostic case*: "All cats can fly. Tom is a cat. Therefore Tom can fly." —
is this valid? Is it sound? *Common failure*: rejecting the argument's
validity because the conclusion is absurd, instead of separately assessing
form and premise truth.

**Fallacy recognition.** A working set worth being able to name on sight:
post hoc (per correlation-vs-causation above), affirming the consequent,
false dichotomy, ad hominem, straw man, appeal to popularity/authority,
circular reasoning. *Diagnostic case*: "Everyone on the team agrees this
design is the right call, so it must be correct." Name the fallacy, and
state what additional evidence — beyond the team agreeing — would actually
support the claim. *Common failure*: correctly sensing "something's off"
without being able to name the specific move that's invalid (here, appeal
to popularity) — naming it is what makes the detection transferable to a
new case.

**Toulmin argument structure.** A well-formed argument has a claim, grounds
(the evidence), a warrant (the principle licensing the inference from grounds
to claim), and usually a qualifier (how strongly) and a rebuttal (known
exceptions). Most weak arguments have grounds and a claim but never state the
warrant — which is exactly where they're vulnerable.
*Diagnostic case*: take a claim the learner already made in this session and
ask them to state its warrant explicitly. *Common failure*: the warrant, once
stated, turns out to be the actual point of disagreement — treat that as
progress, not a dead end.
