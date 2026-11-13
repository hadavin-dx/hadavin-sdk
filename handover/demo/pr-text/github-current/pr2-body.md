<!-- fetched from the public GitHub API at 2026-11-13 ~01:45Z: PR #2 'Demo code 1/3: desk code, scripts, docs, workflows' head pr-1-code (d23cf8f) base main; state open; updated 2026-11-12T20:16:48Z -->
# Demo code 1/3: desk code, scripts, docs, workflows

## **User description**
Part 1 of 3 of the demo code, split so each pull request has 100 files or fewer (a limit of the free code-review tool). The three are stacked: merge them in order. Together the three trees equal the earlier pull request #1 (checked: the final tree is identical). Individual parts alone do not run on their own: the checks that need the other parts stay red until the stack is whole.

This part: the desk code (src), scripts, docs, workflows and project files.

🤖 Generated with [Claude Code](https://claude.com/claude-code)


___

## **CodeAnt-AI Description**
**Create a lead desk to capture, track, and follow up on submissions**

### What Changed
- Accepts lead submissions, recognizes repeat requests and existing contacts, and sends incomplete or conflicting submissions to a review queue.
- Qualifies new leads, adds them to the CRM, and sends follow-up emails; interrupted or uncertain outcomes remain visible for retry or human resolution.
- Adds a web portal to search leads, review request history and follow-up status, move leads through configured stages, and handle review items.
- Supports optional CRM stage and owner updates, reminders, and approval of later submissions with new details.

### Impact
`✅ Fewer duplicate lead records`
`✅ Interrupted follow-ups remain recoverable`
`✅ Stalled submissions surfaced for review`
<details><summary><strong>💡 Usage Guide</strong></summary>

### Checking Your Pull Request
Every time you make a pull request, our system automatically looks through it. We check for security issues, mistakes in how you're setting up your infrastructure, and common code problems. We do this to make sure your changes are solid and won't cause any trouble later.

### Talking to CodeAnt AI
Got a question or need a hand with something in your pull request? You can easily get in touch with CodeAnt AI right here. Just type the following in a comment on your pull request, and replace "Your question here" with whatever you want to ask:
<pre>
<code>@codeant-ai ask: Your question here</code>
</pre>
This lets you have a chat with CodeAnt AI about your pull request, making it easier to understand and improve your code.

#### Example
<pre>
<code>@codeant-ai ask: Can you suggest a safer alternative to storing this secret?</code>
</pre>

### Preserve Org Learnings with CodeAnt
You can record team preferences so CodeAnt AI applies them in future reviews. Reply directly to the specific CodeAnt AI suggestion (in the same thread) and replace "Your feedback here" with your input:
<pre>
<code>@codeant-ai: Your feedback here</code>
</pre>
This helps CodeAnt AI learn and adapt to your team's coding style and standards.

#### Example
<pre>
<code>@codeant-ai: Do not flag unused imports.</code>
</pre>

### Retrigger review
Ask CodeAnt AI to review the PR again, by typing:
<pre>
<code>@codeant-ai: review</code>
</pre>

### Check Your Repository Health
To analyze the health of your code repository, visit our dashboard at [https://app.codeant.ai](https://app.codeant.ai). This tool helps you identify potential issues and areas for improvement in your codebase, ensuring your repository maintains high standards of code health.

</details>

