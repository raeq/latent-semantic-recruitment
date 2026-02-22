# Contemporaneous Evidence Manifest

## Purpose

This document catalogues the contemporaneous evidence establishing the discovery timeline and authorship of latent semantic recruitment (LSR) and the novel axis principle. All evidence is contained within the local git repository at this path and in the Claude conversation transcripts stored locally on the author's machine.

## Discovery Timeline

### Date: 21 February 2026

All discovery work occurred in a single extended collaborative session (Session 027, second and third context windows) between Richard Quinn (human collaborator) and Claude Opus 4 (AI collaborator, Anthropic).

The git commit history provides cryptographically timestamped evidence of the order of discovery:

| Time (UTC) | Commit | Event |
|---|---|---|
| 20:31:58 | `91d41d5` | Phases 20-21 added (verb-action register mismatch, dialogue-world coherence) |
| 20:41:28 | `793d723` | Phase 22 added (contradictory framing within a beat) |
| 20:43:39 | `8213965` | Phase 23 added (overspecified props) |
| 21:27:10 | `10557a7` | **Phase 24 added: Latent semantic recruitment** |
| 21:44:20 | `6347cc4` | **Novel axis principle added to Signature Techniques** |

### Key Discovery Sequence (from conversation transcript)

1. Human collaborator submitted external prose sample (~1,000 words, Mauretania passage) for audit
2. AI collaborator performed initial audit (Phases 1-14): 10 flags identified
3. Human collaborator performed independent close reading: 7 additional flags identified → Phases 15-23 created
4. Human collaborator's third reading pass identified "bit" and "droppings" as dual-meaning words recruited by the active biological register
5. Human collaborator proposed the AI-tell hypothesis: the recruitment was a product of the token probability distribution, not authorial intent
6. AI collaborator provided mechanistic explanation grounded in transformer architecture
7. Phase 24 (latent semantic recruitment) formalized and committed
8. Human collaborator proposed the novel axis principle as an active countermeasure
9. AI collaborator tested the principle with the bird/brain experiment (4 attempts, 3 successful novel-axis, 1 default-axis failure)
10. Novel axis principle formalized and committed

## Evidence Sources

### 1. Git Repository
- **Location:** `/Users/subzero/Library/Mobile Documents/com~apple~CloudDocs/Ribbonworld/.git/`
- **Contents:** Full commit history with SHA-256 hashes, timestamps, and diffs
- **Key files modified:** `_claude/STYLE_GUIDE.md` (all phase additions, novel axis principle)
- **Integrity:** Each commit hash is a cryptographic proof of the content at that timestamp

### 2. Conversation Transcripts
- **Location:** Stored locally by the Claude desktop application
- **Format:** JSONL with timestamps per message
- **Contents:** The full collaborative session including:
  - The external prose sample submitted for audit
  - All editorial observations by both collaborators
  - The discovery dialogue for LSR (human identifies "bit" and "droppings," AI explains mechanism)
  - The novel axis principle proposal and bird/brain experiment
  - The academic paper drafting process
- **Session identifiers:** Session 027 (windows 2 and 3)

### 3. Style Guide (STYLE_GUIDE.md)
- **Location:** `_claude/STYLE_GUIDE.md` in the repository
- **Contents:** The full 24-phase revision protocol, each phase with search criteria, action, test, and calibration notes
- **Phase 24:** Complete description of latent semantic recruitment with four-step audit procedure
- **Novel axis principle:** Complete description with positive and negative examples

### 4. Academic Paper Build Scripts
- **Location:** `paper.js`, `paper_v2.js`, `paper_v3.js`, `paper_v4.js` in the repository
- **Contents:** JavaScript build scripts (docx-js) for each version of the academic paper
- **Version history:** v1 (initial), v2 (audit corrections + math + appendix), v3 (algorithmic generation extension), v4 (universal domain generalization + general method + prior art)

## Authorship

- **Human collaborator:** Richard Quinn (raeq237823@gmail.com)
- **AI collaborator:** Claude Opus 4, Anthropic

The human collaborator provided: perceptual detection of the phenomenon, the AI-tell hypothesis, the novel axis principle concept, editorial domain expertise, and strategic direction for the formalization.

The AI collaborator provided: mechanistic explanation, mathematical formalization, the bird/brain experiment, formal codification of the audit procedure, domain generalization, prior art analysis, and paper composition.

## Preservation Instructions

To preserve this evidence for patent filing:

1. **Git bundle:** Create a git bundle of the full repository: `git bundle create ribbonworld-evidence.bundle --all`
2. **Transcript export:** Export the Claude conversation transcripts from the desktop application
3. **Timestamp verification:** The git commit timestamps can be independently verified against the conversation transcript timestamps
4. **Notarization (optional):** The git bundle and transcript exports can be notarized via a digital notary service to establish a legally defensible timestamp

## Notes

- The external prose sample (Mauretania passage) was submitted by the human collaborator for editorial analysis. Its authorship is external to this collaboration.
- The paper versions (v1-v4) were generated on 21-22 February 2026 in the same extended session.
- No portion of this work has been published, shared, or disclosed outside the collaborators' local machines as of the date of this manifest.
