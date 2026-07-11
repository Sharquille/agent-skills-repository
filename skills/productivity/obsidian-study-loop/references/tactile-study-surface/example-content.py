META = dict(
    source="Notes/Security+ Ch2 - Malware.md",
    scope="2.3 Malware",
    code="2.3",
    scope_name="Malware",
    generated="2026-07-10T21:30:00-0400",
    title="Security+ 2.3 Malware · Visual review",
    accent="oklch(0.48 0.16 20)",
    kicker="Security+ field note · malicious behavior",
    h1="Classify malware by its deciding behavior.",
    lede="Scope 2.3 organizes families through three lenses: how the code spreads, how it controls a host, and what payload or effect it delivers.",
)

SECTIONS = [
    dict(
        id="classifier",
        nav="Decision lenses",
        title="Three decision lenses",
        lede="A family can use multiple techniques. Start with the scenario’s strongest behavior rather than a secondary trait such as being fileless—running from memory, scripts, or legitimate tools instead of a written executable—or polymorphic—changing its code or signature to evade detection.",
        body="""        <div class="grid-3">
          <article class="card"><span class="tag">How does it replicate?</span><h3>Spread</h3><p><strong>Virus:</strong> host file and execution trigger. <strong>Worm:</strong> autonomous replication and network spread.</p></article>
          <article class="card"><span class="tag">How is the host controlled?</span><h3>Access + command</h3><p>Trojan disguise, RAT interactive remote control, backdoor access, or botnet tasking through C2.</p></article>
          <article class="card"><span class="tag">What effect appears?</span><h3>Payload</h3><p>Encryption, spying, key capture, hiding, resource hijacking, or condition-triggered execution.</p></article>
        </div>
        <div class="contrast"><h3>Malware vs PUP / PUA</h3><p>Malware is malicious by purpose and behavior. A PUP or PUA may be unwanted, bundled, intrusive, or risky without being definitively malicious. Bloatware—preinstalled or bundled software that consumes resources—sits in the same not-quite-malware zone.</p></div>""",
    ),
    dict(
        id="families",
        nav="Families",
        title="Family indicator board",
        lede="Match the symptom to the family’s deciding clue. “Malicious process” is the generic fit when execution is harmful but evidence is not specific enough for a family.",
        body="""        <div class="grid-4">
          <article class="card"><span class="tag">Control</span><h3>Trojan</h3><p>Hidden in something useful-looking; the disguise persuades the user to install it.</p></article>
          <article class="card"><span class="tag">Control</span><h3>RAT</h3><p>Interactive remote administration of one infected host.</p></article>
          <article class="card"><span class="tag">Control</span><h3>Backdoor</h3><p>Access path that bypasses or subverts normal authentication.</p></article>
          <article class="card"><span class="tag">Control</span><h3>Botnet / C2</h3><p>Many compromised hosts receive tasking from attacker-controlled infrastructure.</p></article>
          <article class="card"><span class="tag">Spread</span><h3>Virus</h3><p>Inserted into a host executable; runs when the infected file executes.</p></article>
          <article class="card"><span class="tag">Spread</span><h3>Worm</h3><p>Self-replicates and spreads across processes or network connections.</p></article>
          <article class="card"><span class="tag">Payload</span><h3>Crypto-ransomware</h3><p>Encrypts files and demands payment for a decryption key. The harm is availability; data theft harms confidentiality.</p></article>
          <article class="card"><span class="tag">Payload</span><h3>Crypto-mining</h3><p>Hijacks CPU or GPU resources to generate cryptocurrency.</p></article>
          <article class="card"><span class="tag">Payload</span><h3>Spyware / keylogger</h3><p>Collects user information; a keylogger specifically records keystrokes.</p></article>
          <article class="card"><span class="tag">Payload</span><h3>Rootkit</h3><p>Modifies low-level system behavior or files to conceal its presence.</p></article>
          <article class="card"><span class="tag">Trigger</span><h3>Logic bomb</h3><p>Runs when a defined event or condition occurs.</p></article>
          <article class="card"><span class="tag">Generic</span><h3>Malicious process</h3><p>Unauthorized harmful execution without enough evidence for a narrower family.</p></article>
        </div>""",
    ),
    dict(
        id="pairs",
        nav="Close pairs",
        title="High-confusion pairs",
        lede="The tell line is the smallest clue that changes the best answer.",
        body="""        <div class="grid-2">
          <div class="vs">
            <article class="card"><span class="tag">Virus</span><p>Needs a host file and execution trigger.</p></article>
            <span class="vs-mark">VS</span>
            <article class="card"><span class="tag">Worm</span><p>Replicates and travels on its own across a network.</p></article>
          </div>
          <div class="vs">
            <article class="card"><span class="tag">RAT</span><p>An operator interactively controls one host.</p></article>
            <span class="vs-mark">VS</span>
            <article class="card"><span class="tag">Botnet / C2</span><p>A controller pushes tasking to many infected hosts.</p></article>
          </div>
        </div>""",
    ),
    dict(
        id="delivery",
        nav="Delivery",
        title="Delivery is not the payload",
        lede="Phishing or spear phishing gets a victim to act; the attachment carries a worm, Trojan, ransomware, virus, or another payload.",
        body="""        <div class="grid-3">
          <article class="card"><span class="tag warn">Lure</span><h3>Email + social engineering</h3><p>The message supplies context and pressure. It is a delivery technique, not a malware family.</p></article>
          <article class="card"><span class="tag warn">Disguise</span><h3>Extensions + archives</h3><p>Double extensions, macro-enabled Office files, scripts, PDFs, ZIPs, and ISOs can conceal execution paths.</p></article>
          <article class="card"><span class="tag warn">Reveal</span><h3>Show file extensions</h3><p>The final extension in <code>invoice.pdf.exe</code> exposes the executable payload that the icon may hide.</p></article>
        </div>""",
    ),
    dict(
        id="response",
        nav="Response",
        title="Choose the response verb precisely",
        lede="Isolation, removal, and controlled execution solve different problems.",
        body="""        <div class="grid-3">
          <article class="card"><span class="tag">Isolate</span><h3>Quarantine</h3><p>Prevents normal access or execution while preserving the file for review, evidence, or restoration after a false positive.</p></article>
          <article class="card"><span class="tag">Remove</span><h3>Delete + remediate</h3><p>Removes the file, then stops processes, removes persistence, cleans related artifacts, and verifies the threat cannot return.</p></article>
          <article class="card"><span class="tag">Observe</span><h3>Sandbox</h3><p>Runs suspicious code inside a controlled environment to study behavior. A sandbox is not the same as quarantine.</p></article>
        </div>""",
    ),
    dict(
        id="upkeep",
        nav="Upkeep",
        title="Keep protection current",
        lede="Detection is only as good as its latest update. Signatures, engines, and patches age at different speeds.",
        body="""        <div class="grid-3">
          <article class="card"><span class="tag">Update</span><h3>Signatures + engine</h3><p>Definition updates teach the scanner new known threats; engine and cloud-intelligence updates improve how detection itself works.</p></article>
          <article class="card"><span class="tag">Detect</span><h3>Heuristics + reputation</h3><p>Heuristic detection flags suspicious behavior or characteristics without an exact signature; cloud intelligence adds vendor reputation data.</p></article>
          <article class="card"><span class="tag">Patch</span><h3>OS + applications</h3><p>Patching removes the vulnerabilities malware exploits—protection updates cannot compensate for an unpatched hole.</p></article>
        </div>""",
    ),
]

CUES = [
    ("A hidden kernel driver modifies system behavior. What family fits?",
     "Reference: rootkit—the low-level modification and concealment are the deciding clues."),
    ("One host beacons to a controller, but the scenario does not show interactive administration. RAT or C2?",
     "Reference: C2 or botnet tasking is the stronger fit when direction from a controller is the clue. A RAT needs evidence of interactive remote administration of the host."),
    ("An endpoint tool isolates a suspicious file but keeps it available to analysts. Quarantine, delete, or sandbox?",
     "Reference: quarantine—execution and access are blocked while the object is preserved. Sandbox would run it in a controlled environment."),
    ("Signature update, engine update, or patch—which fixes what?",
     "Reference: signatures add new known threats; engine updates improve the detection software itself; patches remove the vulnerabilities malware exploits. Heuristics and cloud reputation cover what signatures miss."),
]
