### OUT/built/pristine/film-v5/mf-form.json
- nodes: 12; connections: 11; triggers: Receive
- FAIL: Receive: webhook without authentication
- save settings: saveDataSuccessExecution=none, saveDataErrorExecution=none, saveManualExecutions=False, executionOrder=v1, errorWorkflow=None
- webhooks: Receive POST /mf-form auth=none
- $env reads: none
- credentials: Claim [postgres] postgres=n8n-publish-pg; Stored [postgres] postgres=n8n-publish-pg

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

Write nodes (mail or CRM) and the external-call nodes upstream of each:

| write node | type | its onError | upstream external nodes (name: onError) |
|---|---|---|---|

### OUT/built/pristine/film-v5/mf-hook.json
- nodes: 12; connections: 11; triggers: Receive
- FAIL: Receive: webhook without authentication
- save settings: saveDataSuccessExecution=none, saveDataErrorExecution=none, saveManualExecutions=False, executionOrder=v1, errorWorkflow=None
- webhooks: Receive POST /mf-hook auth=none
- $env reads: none
- credentials: Claim [postgres] postgres=n8n-publish-pg; Stored [postgres] postgres=n8n-publish-pg

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

Write nodes (mail or CRM) and the external-call nodes upstream of each:

| write node | type | its onError | upstream external nodes (name: onError) |
|---|---|---|---|

### OUT/built/pristine/film-v5/mf-recovery.json
- nodes: 10; connections: 9; triggers: Every30s
- FAIL: none
- save settings: saveDataSuccessExecution=none, saveDataErrorExecution=none, saveManualExecutions=False, executionOrder=v1, errorWorkflow=None
- webhooks: none
- $env reads: none
- credentials: ClaimStuck [postgres] postgres=n8n-publish-pg; MarkFailed [postgres] postgres=n8n-publish-pg; AlertClaim [postgres] postgres=n8n-publish-pg; AlertSend [emailSend] smtp=mf-mail-smtp; AlertBackoff [postgres] postgres=n8n-publish-pg; AlertMark [postgres] postgres=n8n-publish-pg

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

Write nodes (mail or CRM) and the external-call nodes upstream of each:

| write node | type | its onError | upstream external nodes (name: onError) |
|---|---|---|---|
| AlertSend | emailSend | continueErrorOutput | AlertClaim: continueRegularOutput |

### OUT/built/pristine/film-v5/mf-sub-crm-mail.json
- nodes: 20; connections: 26; triggers: SubIn
- FAIL: none
- save settings: saveDataSuccessExecution=none, saveDataErrorExecution=none, saveManualExecutions=False, executionOrder=v1, errorWorkflow=None
- webhooks: none
- $env reads: MF_STAGE_URL (Qualify); MF_STAGE_TIMEOUT_MS (Qualify); MF_CRM_URL (CrmUpsert)
- credentials: SetCrmId [postgres] postgres=n8n-publish-pg; MailClaim [postgres] postgres=n8n-publish-pg; SendMail [emailSend] smtp=mf-mail-smtp; MarkDone [postgres] postgres=n8n-publish-pg; MarkUnknownA [postgres] postgres=n8n-publish-pg; MarkUnknownB [postgres] postgres=n8n-publish-pg

| node | type | onError | retry | alwaysOutputData | flag |
|---|---|---|---|---|---|
| SubIn | executeWorkflowTrigger | (default: stop) | no | no | - |
| Qualify | httpRequest | continueErrorOutput | yes x2 | no | - |
| LabelOk | if | (default: stop) | no | no | - |
| CrmUpsert | httpRequest | continueErrorOutput | yes x2 | no | - |
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

Write nodes (mail or CRM) and the external-call nodes upstream of each:

| write node | type | its onError | upstream external nodes (name: onError) |
|---|---|---|---|
| Qualify | httpRequest | continueErrorOutput | none |
| CrmUpsert | httpRequest | continueErrorOutput | Qualify: continueErrorOutput |
| SendMail | emailSend | continueErrorOutput | CrmUpsert: continueErrorOutput; MailClaim: (stop) +alwaysOutputData; Qualify: continueErrorOutput; SetCrmId: (stop) +alwaysOutputData |

