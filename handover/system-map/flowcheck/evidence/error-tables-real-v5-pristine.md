**real-v5/mf-form** (committed files, before the patches)

| node | type | onError | retry | alwaysOutputData | flag |
|---|---|---|---|---|---|
| Receive | webhook | (default: stop) | no | no | - |
| Item | set | (default: stop) | no | no | - |
| Valid | set | (default: stop) | no | no | - |
| Claim | postgres | (default: stop) | no | yes | - |
| Claimed | if | (default: stop) | no | no | - |
| IsProcessing | if | (default: stop) | no | no | - |
| SubInput | set | (default: stop) | no | no | - |
| RunSub | executeWorkflow | (default: stop) | no | no | - |
| ReplyRan | respondToWebhook | (default: stop) | no | no | - |
| ReplyReview | respondToWebhook | (default: stop) | no | no | - |
| Stored | postgres | (default: stop) | no | yes | - |
| ReplyStored | respondToWebhook | (default: stop) | no | no | - |

**real-v5/mf-hook** (committed files, before the patches)

| node | type | onError | retry | alwaysOutputData | flag |
|---|---|---|---|---|---|
| Receive | webhook | (default: stop) | no | no | - |
| Item | set | (default: stop) | no | no | - |
| Valid | set | (default: stop) | no | no | - |
| Claim | postgres | (default: stop) | no | yes | - |
| Claimed | if | (default: stop) | no | no | - |
| IsProcessing | if | (default: stop) | no | no | - |
| SubInput | set | (default: stop) | no | no | - |
| RunSub | executeWorkflow | (default: stop) | no | no | - |
| ReplyRan | respondToWebhook | (default: stop) | no | no | - |
| ReplyReview | respondToWebhook | (default: stop) | no | no | - |
| Stored | postgres | (default: stop) | no | yes | - |
| ReplyStored | respondToWebhook | (default: stop) | no | no | - |

**real-v5/mf-recovery** (committed files, before the patches)

| node | type | onError | retry | alwaysOutputData | flag |
|---|---|---|---|---|---|
| Every30s | scheduleTrigger | (default: stop) | no | no | - |
| ClaimStuck | postgres | continueRegularOutput | no | no | - |
| StuckRow | if | (default: stop) | no | no | - |
| RunSub | executeWorkflow | continueRegularOutput | no | no | - |
| MarkFailed | postgres | continueRegularOutput | no | no | - |
| AlertClaim | postgres | continueRegularOutput | no | no | - |
| AlertRow | if | (default: stop) | no | no | - |
| AlertSend | emailSend | continueErrorOutput | no | no | - |
| AlertBackoff | postgres | continueRegularOutput | no | no | - |
| AlertMark | postgres | continueRegularOutput | no | no | - |

**real-v5/mf-sub-crm-mail** (committed files, before the patches)

| node | type | onError | retry | alwaysOutputData | flag |
|---|---|---|---|---|---|
| SubIn | executeWorkflowTrigger | (default: stop) | no | no | - |
| Qualify | httpRequest | continueErrorOutput | yes x2 | no | - |
| LabelOk | if | (default: stop) | no | no | - |
| CrmUpsert | hubspot | continueErrorOutput | yes x2 | no | - |
| SetCrmId | postgres | (default: stop) | no | yes | - |
| CrmIdOk | if | (default: stop) | no | no | - |
| OwnsClaim1 | if | (default: stop) | no | no | - |
| MailClaim | postgres | (default: stop) | no | yes | - |
| MailRowBack | if | (default: stop) | no | no | - |
| SendMail | emailSend | continueErrorOutput | no | no | - |
| MarkDone | postgres | (default: stop) | no | yes | - |
| MarkUnknownA | postgres | (default: stop) | no | yes | - |
| MarkUnknownB | postgres | (default: stop) | no | yes | - |
| UnknownNewA | if | (default: stop) | no | no | - |
| UnknownNew | if | (default: stop) | no | no | - |
| DoneOwned | if | (default: stop) | no | no | - |
| OutDone | set | (default: stop) | no | no | - |
| OutUnknown | set | (default: stop) | no | no | - |
| OutStage | set | (default: stop) | no | no | - |
| OutLost | set | (default: stop) | no | no | - |
