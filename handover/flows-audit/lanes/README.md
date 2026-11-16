# lanes/ (working files of the audit; the finished audit is ../FLOWS-AUDIT.md)
- <lane>.md : one lane as written (header text plus one table per flow file). Sources of ../FLOWS-AUDIT.md section 3.
- <lane>.header.md : the header text of that lane (already inside <lane>.md).
- <lane>.judge.jsonl : the builder's 13 judgement cells per node; tools/assemble_lane.py joins them with the machine columns.
- <lane>.findings.md : raw findings of the lane (98 in total). ../FINDINGS.md merges them (ids like L1-7 are cited there).
- checkpoint-*.md : progress notes of a builder (time-box), kept as a record.
- L2a-scripts.md, L2a-generator.md : script inventory and generator check, sections 2 of ../FLOWS-AUDIT.md.
- L3-claims.md, L3-stores.md : sections 4 of ../FLOWS-AUDIT.md (claims table and store table).
