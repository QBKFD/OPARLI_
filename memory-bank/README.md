# Memory Bank - README

## Purpose

This memory-bank system provides **continuity across AI agent sessions**. When a new AI coding assistant starts working on this project, they can read these files to quickly understand the project context, architecture, current status, and priorities.

---

## Files in this Directory

### 1. [projectbrief.md](projectbrief.md)
**Read this FIRST**

Contains:
- Project overview and goals
- Technology stack
- Core features
- Known challenges
- Repository structure

**When to update**: When project goals change or major technology decisions are made.

---

### 2. [techContext.md](techContext.md)
**Read this SECOND**

Contains:
- Detailed architecture documentation
- Service descriptions and data flows
- API endpoints reference
- Database schema
- Agent communication patterns
- Configuration files
- Development workflow

**When to update**: When adding new services, endpoints, or changing architecture.

---

### 3. [systemPatterns.md](systemPatterns.md)
**Read this THIRD**

Contains:
- Specific data flow patterns between agents
- Message formats and communication protocols
- Agent responsibilities and interactions
- Detailed technical workflows

**When to update**: When modifying agent behavior or adding new message types.

---

### 4. [activeContext.md](activeContext.md)
**Read this LAST (but most important for current work)**

Contains:
- Current development phase
- Recent completed work
- Tasks in progress
- Priority list (high/medium/low)
- Known issues and blockers
- Git status summary
- Quick reference commands
- Context for common questions

**When to update**: EVERY TIME you complete a task or start new work. This is the most dynamic file.

---

## How to Use This Memory Bank

### For New AI Agents Starting a Session

1. **Read all files in order** (projectbrief → techContext → systemPatterns → activeContext)
2. **Ask the user**: "What would you like to work on today?"
3. **Verify environment**: Check if services are running (see activeContext.md for commands)
4. **Update activeContext.md**: Add new tasks or move completed ones

### For Continuing Work

1. **Update activeContext.md** as you complete tasks:
   - Move items from "In Progress" to "Completed"
   - Add new issues discovered
   - Update priority list if needed
   - Update the "Last Updated" date

2. **Update other files** when making architectural changes:
   - New service? → Update techContext.md
   - New agent message type? → Update systemPatterns.md
   - Changed project goals? → Update projectbrief.md

---

## Maintenance Guidelines

### Keep It Current
- Update dates regularly
- Remove outdated information
- Mark resolved issues as "✅ Resolved"
- Keep "Recent Work" section to last 5-7 items

### Be Specific
- Use file paths: `backend/services/agent_orchestrator.py`
- Include line numbers when relevant: `main.py:142`
- List actual commands: `curl -X POST http://localhost:8001/api/agents/start`
- Show error messages: Copy-paste actual errors when documenting issues

### Be Concise
- Use bullet points
- Keep paragraphs short (2-3 sentences max)
- Use code blocks for commands
- Use headers for easy scanning

---

## Quick Start for New Agents

```bash
# 1. Navigate to memory-bank
cd /Users/x/Desktop/algo_project/memory-bank

# 2. Read all context files
cat projectbrief.md
cat techContext.md
cat systemPatterns.md
cat activeContext.md

# 3. Check current git status
git status
git log --oneline -10

# 4. Verify services running
docker ps  # Check Kafka
curl http://localhost:8001/  # Check backend API
curl http://localhost:5173/  # Check frontend

# 5. Ask user what they want to work on
```

---

## File Update Checklist

### After Completing a Task
- [ ] Move task from "In Progress" to "Completed" in activeContext.md
- [ ] Add any new issues discovered to "Known Issues"
- [ ] Update "Last Updated" date
- [ ] Update git status summary if needed

### After Adding New Feature
- [ ] Document new API endpoints in techContext.md
- [ ] Update service descriptions if applicable
- [ ] Add to "Recent Work" in activeContext.md
- [ ] Update system patterns if agents affected

### Before Ending Session
- [ ] Ensure activeContext.md reflects current state
- [ ] List any unfinished work in "In Progress"
- [ ] Note any blockers for next session
- [ ] Update priority list if priorities changed

---

## Benefits of This System

1. **No context loss** between AI agent sessions
2. **Faster onboarding** for new agents (human or AI)
3. **Consistent documentation** that stays up-to-date
4. **Clear priorities** so agents know what to work on
5. **Historical record** of decisions and changes

---

## Example Update

```markdown
## activeContext.md - Before Session
### In Progress
1. 🔄 Testing agent system end-to-end

## activeContext.md - After Session
### Completed
1. ✅ Testing agent system end-to-end
   - Initialized all 7 agents
   - Ran manual scan successfully
   - Vision Agent correctly received screenshot
   - Meta Agent made BUY decision with 85% confidence
   - Verified data written to database

### In Progress
2. 🔄 Fixing screenshot timeout issue
   - Issue: Selenium timeout after 30s
   - Solution: Increased timeout to 60s in screenshot_service.py:45
   - Status: Testing in progress
```

---

## Contact & Feedback

This memory-bank system is designed to improve with use. If you find something missing or unclear:
1. Add it to the relevant file
2. Note what was missing in activeContext.md under "Documentation Improvements"
3. The next agent will benefit from your contribution

---

**Remember**: Good documentation is a gift to your future self (and the next AI agent)!
