# Orchestra consult panel

Run only if this turn names a consult or those models. Use the `agent-orchestra`
wrappers directly; OpenCode lanes run sequentially. This panel deliberately
overrides the orchestra's default consult pair: never Kimi K3, skip Sol /
ChatGPT. If `agent-orchestra` renames a model, follow its routing reference and
keep these exclusions.

```text
ORCH=/Users/sharquilleandrew/Documents/development/github-local/agent-skills-repository/skills/engineering/agent-orchestra/scripts
"$ORCH/consult-opencode.sh" --sealed --model opencode-go/glm-5.3-flash --reasoning max --timeout 240 -- "<brief>"
"$ORCH/consult-opencode.sh" --sealed --model opencode-go/deepseek-v4.1-flash --variant max --timeout 240 -- "<brief>"
"$ORCH/consult-opencode.sh" --sealed --model opencode-go/minimax-m3 --variant max --timeout 240 -- "<brief>"
"$ORCH/consult-opencode.sh" --sealed --model opencode-go/muse-spark-1.3-contributor --variant max --timeout 240 -- "<brief>"
```

DeepSeek is `deepseek-v4.1-flash`, not `deepseek-v4-flash`. Muse Spark 1.3 is
the OpenCode Go contributor model. If Muse rejects `--variant max`, retry
without variant and report the miss.

Sealed briefs. No `01-University-Records`, no Drive dumps, no secrets, no
homework keys. Verify every consultant claim against the section `ocr-*.txt` (or the
original screenshots **in place**) before writing.

Skip the panel on a routine screenshot drop unless the user names it.
