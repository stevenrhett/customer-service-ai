# FLF Discord Bot — AI Enhancement Roadmap

> **Context:** The FLF Discord bot lives in the `flf-web-project` monorepo at `apps/discord`. It's built with discord.js v14 + TypeScript, shares a Supabase PostgreSQL database via `packages/db` (Drizzle ORM), and currently uses OpenAI gpt-4o-mini with a hardcoded 182-line rulebook string for AI responses. This roadmap upgrades the bot's AI grounding, reliability, and feature set across four phases over ~6–8 weeks.

---

## Architecture Overview (Current → Target)

```
CURRENT STATE                           TARGET STATE (Phase 4)
─────────────                           ──────────────────────

User Query                              User Query
    │                                       │
    ▼                                       ▼
┌──────────┐                           ┌──────────────┐
│ ai.ts    │                           │  Classifier  │ ← Rule-based + length heuristics
│ (442 ln) │                           │   (free)     │
│          │                           └──────┬───────┘
│ hardcoded│                              ┌───┴───┐
│ rulebook │                              ▼       ▼
│ string   │                         ┌───────┐ ┌─────────┐
│          │                         │  SLM  │ │  Large  │
│ gpt-4o-  │                         │ mini  │ │ gpt-4o  │
│ mini     │                         └───┬───┘ └────┬────┘
└────┬─────┘                             │          │
     │                                   ▼          ▼
     ▼                              ┌─────────────────┐
 Single Response                    │  RAG Pipeline    │
                                    │  (vector search  │
                                    │   over rulebook) │
                                    └────────┬────────┘
                                             ▼
                                    ┌─────────────────┐
                                    │ Response + Cache │
                                    │ + Thread Context │
                                    └─────────────────┘
```

---

## Phase 1 — Foundation Fixes (Week 1–2)

**Goal:** Fix the two things blocking real reliability — guild mapping persistence and the brittle hardcoded knowledge base.

### 1.1 Persist Guild-to-League Mapping in Supabase

**Problem:** Guild-to-league mapping is in-memory. A bot restart wipes all `/setup` configurations.

**Solution:** Add a `discord_guild` table via `packages/db` and migrate the in-memory map.

```sql
-- New table in packages/db schema
CREATE TABLE discord_guild (
  id            SERIAL PRIMARY KEY,
  guild_id      TEXT NOT NULL UNIQUE,      -- Discord snowflake
  league_id     INTEGER NOT NULL REFERENCES league(id),
  setup_by      TEXT NOT NULL,             -- Discord user ID of commissioner
  created_at    TIMESTAMPTZ DEFAULT NOW(),
  updated_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_discord_guild_guild_id ON discord_guild(guild_id);
```

**Implementation steps:**
1. Add the Drizzle schema in `packages/db/src/schema/discord-guild.ts`
2. Run `drizzle-kit generate` + `drizzle-kit migrate`
3. Update `/setup` command handler to write to DB instead of in-memory map
4. Add a `getLeagueForGuild(guildId)` helper with simple in-memory cache (TTL: 5 min)
5. On bot startup, pre-load all mappings from DB into cache
6. Remove the old in-memory-only map

**Estimated effort:** 2–4 hours

### 1.2 Extract Rulebook into Structured Document Files

**Problem:** The 182-line hardcoded constant in `ai.ts` is hard to maintain, can't be searched semantically, and limits answer quality.

**Solution:** Extract the rulebook into structured markdown files that serve as the source of truth for both the RAG pipeline (Phase 2) and a human-readable reference.

**File structure:**
```
apps/discord/data/knowledge-base/
├── 01-league-overview.md        # League structure, seasons, scoring
├── 02-contracts.md              # REG, RFA, EZ, PEP, CFP, FA — all contract types
├── 03-salary-cap.md             # Cap rules, penalties, cap holds
├── 04-auctions.md               # Auction mechanics, nomination, bidding
├── 05-trading.md                # Trade rules, deadlines, trade review
├── 06-waivers.md                # Waiver wire, priority, FAAB
├── 07-college-draft.md          # Draft order, rounds, rookie contracts
├── 08-faq.md                    # Common questions and clarifications
└── README.md                    # Index + last-updated date
```

**Implementation steps:**
1. Copy content from the hardcoded string in `ai.ts` into the markdown files
2. Supplement with fuller content from `_bmad-input-docs/` (rulebook, domain specs)
3. Add a `loadKnowledgeBase()` function that reads all `.md` files from the directory
4. Replace the hardcoded constant with the loaded content (immediate improvement, no RAG yet)
5. Add a `lastUpdated` field to `README.md` so you know when docs were last refreshed

**Why markdown?** Human-readable, easy to diff in PRs, and trivial to chunk for RAG later.

**Estimated effort:** 3–5 hours (mostly content extraction and organization)

### 1.3 Refactor `ai.ts` — Separate Concerns

**Problem:** `ai.ts` is 442 lines mixing prompt construction, context building, LLM calls, and response formatting.

**Solution:** Split into focused modules:

```
src/lib/
├── ai/
│   ├── index.ts              # Public API: generateResponse(), streamResponse()
│   ├── prompts.ts            # System prompt template + builder
│   ├── context-builder.ts    # DB queries for live league context
│   ├── knowledge-base.ts     # Load + search knowledge base files
│   └── llm-client.ts         # OpenAI client wrapper (model selection, retries)
```

**Key changes:**
- `prompts.ts` — Template with `{knowledge_base}` and `{league_context}` placeholders
- `context-builder.ts` — The existing DB query logic (franchises, auction state, trades, contracts) moved here
- `llm-client.ts` — Thin wrapper around OpenAI SDK with retry logic, timeout, and model selection
- `knowledge-base.ts` — Reads markdown files, later becomes the RAG retrieval interface

**Estimated effort:** 3–4 hours

---

## Phase 2 — RAG Pipeline + Hybrid Model Routing (Week 2–4)

**Goal:** Ground AI answers in the full rulebook via vector search, and route complex queries to a stronger model.

### 2.1 Lightweight RAG with In-Process Embeddings

**Why not ChromaDB?** Your knowledge base is small (5K–15K tokens across 6–8 files). A full vector database is overkill. An in-process solution avoids infrastructure complexity.

**Recommended approach:** OpenAI embeddings + cosine similarity search in memory.

```typescript
// src/lib/ai/rag.ts

interface DocumentChunk {
  id: string;
  source: string;       // e.g., "02-contracts.md"
  heading: string;       // e.g., "## RFA Contracts"
  content: string;       // The chunk text
  embedding: number[];   // text-embedding-3-small vector
}

class KnowledgeStore {
  private chunks: DocumentChunk[] = [];

  // Called once at startup (or on /reload-kb admin command)
  async initialize(docsPath: string): Promise<void> {
    const files = await readMarkdownFiles(docsPath);
    const chunks = chunkByHeading(files);        // Split on ## headings
    const embeddings = await batchEmbed(chunks);  // OpenAI batch embed
    this.chunks = chunks.map((c, i) => ({ ...c, embedding: embeddings[i] }));
  }

  // Retrieve top-k relevant chunks for a query
  async search(query: string, k = 4): Promise<DocumentChunk[]> {
    const queryEmbedding = await embed(query);
    return this.chunks
      .map(chunk => ({ chunk, score: cosineSimilarity(queryEmbedding, chunk.embedding) }))
      .sort((a, b) => b.score - a.score)
      .slice(0, k)
      .filter(r => r.score > 0.3)  // Minimum relevance threshold
      .map(r => r.chunk);
  }
}
```

**Cost analysis:**
- `text-embedding-3-small`: $0.02 / 1M tokens
- Initial indexing (15K tokens): ~$0.0003 (one-time, cached)
- Per-query embedding: ~$0.000002 (negligible)
- **Total RAG overhead: effectively free**

**Chunking strategy:**
- Split each markdown file on `##` headings → one chunk per section
- Each chunk includes the file title + heading for context
- Typical chunk: 200–800 tokens (good for embedding quality)
- Estimated total: 30–60 chunks across all files

**Embedding cache:**
- Serialize embeddings to `data/knowledge-base/.cache/embeddings.json`
- Rebuild only when source `.md` files change (check mtime or hash)
- Bot startup: load from cache if valid, re-embed only if stale

**Implementation steps:**
1. Install `openai` (already a dependency) — no new packages needed
2. Create `src/lib/ai/rag.ts` with `KnowledgeStore` class
3. Add `chunkByHeading()` utility (split markdown on `##`)
4. Add `batchEmbed()` wrapper around OpenAI embeddings API
5. Add cosine similarity search (no external library — ~10 lines of math)
6. Initialize `KnowledgeStore` on bot startup
7. Update `generateResponse()` to retrieve relevant chunks instead of injecting entire rulebook
8. Add `/reload-kb` admin command to re-index without restart

### 2.2 Hybrid Model Routing

**Strategy:** Use the cheap model for 80% of queries, escalate to a stronger model for complex reasoning.

```typescript
// src/lib/ai/router.ts

type ModelTier = 'standard' | 'advanced';

interface RoutingDecision {
  tier: ModelTier;
  model: string;
  maxTokens: number;
  reason: string;
}

function classifyQuery(query: string, ragResults: DocumentChunk[]): RoutingDecision {
  const q = query.toLowerCase();
  const standard: RoutingDecision = {
    tier: 'standard',
    model: 'gpt-4o-mini',
    maxTokens: 600,
    reason: 'routine-query',
  };
  const advanced: RoutingDecision = {
    tier: 'advanced',
    model: 'gpt-4o',       // Or claude-sonnet-4-6 via Anthropic API
    maxTokens: 1200,
    reason: '',
  };

  // 1. Multi-part or comparative questions → advanced
  if (/\b(compare|versus|vs\.?|difference between|trade .+ for)\b/.test(q)) {
    return { ...advanced, reason: 'comparative-analysis' };
  }

  // 2. Strategy/opinion questions → advanced
  if (/\b(should i|worth it|strategy|better to|recommend|optimal)\b/.test(q)) {
    return { ...advanced, reason: 'strategy-advice' };
  }

  // 3. Long, complex queries (user explaining a situation) → advanced
  if (query.length > 350) {
    return { ...advanced, reason: 'complex-situation' };
  }

  // 4. Low RAG confidence (no good matches) → advanced for reasoning
  if (ragResults.length === 0 || ragResults[0].score < 0.5) {
    return { ...advanced, reason: 'low-rag-confidence' };
  }

  // 5. Multiple questions in one message → advanced
  if ((query.match(/\?/g) || []).length >= 2) {
    return { ...advanced, reason: 'multi-question' };
  }

  // Default: standard
  return standard;
}
```

**Cost projection (1,000 queries/month):**

| Scenario | Model Split | Est. Monthly Cost |
|----------|-------------|-------------------|
| Current (all gpt-4o-mini) | 100% mini | ~$0.50 |
| Hybrid routing | 80% mini, 20% gpt-4o | ~$0.40 + $0.50 = ~$0.90 |
| All gpt-4o (naive upgrade) | 100% gpt-4o | ~$5.00 |

**The hybrid gives you 10x better answers on hard questions for < 2x the total cost.**

### 2.3 Response Caching

```typescript
// src/lib/ai/cache.ts

interface CacheEntry {
  response: string;
  agentTier: ModelTier;
  cachedAt: number;
  ttl: number;
}

class ResponseCache {
  private cache = new Map<string, CacheEntry>();
  private readonly DEFAULT_TTL = 60 * 60 * 1000; // 1 hour

  private makeKey(query: string, leagueId: number): string {
    // Normalize query for near-duplicate matching
    const normalized = query.toLowerCase().trim().replace(/\s+/g, ' ');
    return createHash('sha256').update(`${leagueId}:${normalized}`).digest('hex');
  }

  get(query: string, leagueId: number): string | null {
    const entry = this.cache.get(this.makeKey(query, leagueId));
    if (!entry) return null;
    if (Date.now() - entry.cachedAt > entry.ttl) {
      this.cache.delete(this.makeKey(query, leagueId));
      return null;
    }
    return entry.response;
  }

  set(query: string, leagueId: number, response: string, tier: ModelTier): void {
    this.cache.set(this.makeKey(query, leagueId), {
      response,
      agentTier: tier,
      cachedAt: Date.now(),
      ttl: this.DEFAULT_TTL,
    });
  }
}
```

**Cache strategy:**
- Key on `leagueId + normalized query` (different leagues get different answers since context differs)
- TTL: 1 hour for static rule questions, skip caching for questions that include live context (standings, scores)
- Don't cache if the response references time-sensitive data

---

## Phase 3 — Discord Feature Expansion (Week 4–6)

**Goal:** Add thread-based conversations, a dedicated support channel, and scheduled alerts.

### 3.1 Thread-Based Multi-Turn Conversations

**Problem:** Each `/ask` or mention is stateless — the bot has no memory of prior messages in a conversation.

**Solution:** Use Discord threads as conversation containers with message history.

```typescript
// src/lib/ai/thread-context.ts

interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
}

async function getThreadHistory(
  thread: ThreadChannel,
  maxMessages = 10
): Promise<ConversationMessage[]> {
  const messages = await thread.messages.fetch({ limit: maxMessages });
  return messages
    .reverse()
    .map(msg => ({
      role: msg.author.bot ? 'assistant' as const : 'user' as const,
      content: msg.content,
    }));
}
```

**Behavior:**
- When a user asks a question in a support channel, the bot creates a thread and replies there
- Subsequent messages in the thread include the thread history as conversation context
- Thread history is capped at 10 messages (~4K tokens) to control costs
- Threads auto-archive after 1 hour of inactivity (Discord default)
- Thread title = first ~80 chars of the user's question

**Implementation steps:**
1. Create `src/lib/ai/thread-context.ts` — fetch + format thread history
2. Modify the AI response flow to detect thread context and inject it into the prompt
3. Update the support channel handler (3.2) to auto-create threads
4. Add thread history as `conversation_history` in the LLM messages array

### 3.2 Dedicated Support Channel with Auto-Response

**Problem:** Users currently must use `/ask`, @mention, or DM the bot. There's no always-on channel.

**Solution:** Allow commissioners to designate a support channel via `/setup`. Any message in that channel triggers an AI response in a thread.

```sql
-- Add to discord_guild table
ALTER TABLE discord_guild ADD COLUMN support_channel_id TEXT;
```

```typescript
// In the main message handler
client.on('messageCreate', async (message) => {
  if (message.author.bot) return;

  const guildConfig = await getGuildConfig(message.guild?.id);

  // Auto-respond in designated support channel
  if (message.channel.id === guildConfig?.supportChannelId) {
    const thread = await message.startThread({
      name: message.content.slice(0, 80),
      autoArchiveDuration: 60,
    });
    const response = await generateResponse(message.content, {
      leagueId: guildConfig.leagueId,
      threadHistory: [],  // New thread, no history yet
    });
    await thread.send(response);
    return;
  }

  // Existing @mention and DM handling...
});
```

**Setup flow:**
```
Commissioner: /setup league:My League support-channel:#flf-help
Bot: ✅ Linked to "My League". I'll auto-respond to questions in #flf-help.
```

### 3.3 Scheduled Alerts & Reminders

**Alerts to implement (priority order):**

| Alert | Trigger | Channel |
|-------|---------|---------|
| **Waiver reminder** | 24h before waiver deadline | Support channel or configurable |
| **Trade deadline** | 48h and 24h before deadline | Support channel |
| **Auction open** | When a new auction starts | Support channel |
| **Weekly scores** | After games complete (Monday/Tuesday) | Support channel |

**Implementation approach:**
```typescript
// src/lib/scheduler.ts
import { CronJob } from 'cron';

function initScheduler(client: Client) {
  // Waiver reminder — every day at 9 AM ET
  new CronJob('0 9 * * *', async () => {
    const guilds = await getAllGuildConfigs();
    for (const guild of guilds) {
      const waiverDeadline = await getNextWaiverDeadline(guild.leagueId);
      if (waiverDeadline && isWithin24Hours(waiverDeadline)) {
        const channel = await client.channels.fetch(guild.supportChannelId);
        await channel.send(`⏰ **Waiver claims close in 24 hours!** Submit your claims before ${formatTime(waiverDeadline)}.`);
      }
    }
  }, null, true, 'America/New_York');
}
```

**New dependency:** `cron` (lightweight, no external service needed)

### 3.4 New Slash Commands

| Command | Description | Priority |
|---------|-------------|----------|
| `/rules [topic]` | Quick rule lookup by topic (contracts, trading, waivers) — uses RAG search | High |
| `/trade-check @team1 @team2` | Analyze a potential trade using advanced model | Medium |
| `/cap [team]` | Show salary cap breakdown for a team | Medium |
| `/reminders [on/off]` | Toggle scheduled alerts for the server | Medium |
| `/reload-kb` | Re-index knowledge base (admin only) | Low |

---

## Phase 4 — Production Hardening (Week 6–8)

**Goal:** Make the bot reliable for daily use with monitoring, error handling, and deployment automation.

### 4.1 Error Handling & Graceful Degradation

```typescript
// src/lib/ai/llm-client.ts

async function callLLM(
  messages: ChatMessage[],
  options: { model: string; maxTokens: number; timeout?: number }
): Promise<string> {
  try {
    const response = await openai.chat.completions.create({
      model: options.model,
      messages,
      max_tokens: options.maxTokens,
      temperature: 0.3,
    }, {
      timeout: options.timeout ?? 15_000,  // 15s timeout
    });
    return response.choices[0].message.content ?? '';
  } catch (error) {
    if (error instanceof APIError && error.status === 429) {
      // Rate limited — retry once after delay
      await sleep(2000);
      return callLLM(messages, options);
    }
    if (options.model !== 'gpt-4o-mini') {
      // Advanced model failed — fall back to standard
      console.warn(`${options.model} failed, falling back to gpt-4o-mini`);
      return callLLM(messages, { ...options, model: 'gpt-4o-mini' });
    }
    throw error;  // Let caller handle with user-friendly message
  }
}
```

**Fallback chain:** `gpt-4o → gpt-4o-mini → cached response → "I'm having trouble right now, please try again."`

### 4.2 Rate Limiting

```typescript
// src/lib/rate-limiter.ts

class UserRateLimiter {
  private buckets = new Map<string, { count: number; resetAt: number }>();

  private readonly LIMITS = {
    queriesPerMinute: 5,
    queriesPerHour: 30,
    advancedModelPerDay: 10,
  };

  check(userId: string, tier: ModelTier): { allowed: boolean; retryAfter?: number } {
    const key = `${userId}:minute`;
    const bucket = this.buckets.get(key);
    const now = Date.now();

    if (!bucket || now > bucket.resetAt) {
      this.buckets.set(key, { count: 1, resetAt: now + 60_000 });
      return { allowed: true };
    }

    if (bucket.count >= this.LIMITS.queriesPerMinute) {
      return { allowed: false, retryAfter: Math.ceil((bucket.resetAt - now) / 1000) };
    }

    bucket.count++;
    return { allowed: true };
  }
}
```

### 4.3 Observability & Monitoring

```typescript
// src/lib/metrics.ts

interface QueryMetrics {
  totalQueries: number;
  byTier: { standard: number; advanced: number };
  cacheHits: number;
  cacheMisses: number;
  avgLatencyMs: number;
  errors: number;
  estimatedCostUsd: number;
}

// Log to stdout in structured JSON — pick up by any log aggregator
function logQuery(event: {
  userId: string;
  guildId: string;
  query: string;        // Truncated for privacy
  tier: ModelTier;
  model: string;
  latencyMs: number;
  cached: boolean;
  tokensUsed: { input: number; output: number };
}) {
  console.log(JSON.stringify({ type: 'query', timestamp: new Date().toISOString(), ...event }));
}
```

**Add a `/bot-stats` admin command** that returns:
- Queries today/this week/this month
- Cache hit rate
- Model tier distribution
- Estimated cost
- Error rate

### 4.4 Deployment Configuration

```dockerfile
# apps/discord/Dockerfile
FROM node:20-slim AS builder
WORKDIR /app
COPY package.json yarn.lock ./
COPY packages/db ./packages/db
COPY apps/discord ./apps/discord
RUN yarn install --frozen-lockfile
RUN yarn workspace @flf/discord build

FROM node:20-slim
WORKDIR /app
COPY --from=builder /app/apps/discord/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY apps/discord/data ./data
CMD ["node", "dist/index.js"]
```

```yaml
# apps/discord/docker-compose.yml (for local dev)
services:
  discord-bot:
    build: .
    env_file: .env
    volumes:
      - ./data:/app/data  # Mount knowledge base for hot-reload
    restart: unless-stopped
```

**Health check endpoint** (optional — useful for Railway/Fly.io):
```typescript
import http from 'http';

http.createServer((req, res) => {
  if (req.url === '/health') {
    res.writeHead(client.isReady() ? 200 : 503);
    res.end(JSON.stringify({ status: client.isReady() ? 'ok' : 'degraded' }));
  }
}).listen(process.env.PORT || 3001);
```

---

## Phase Summary & Timeline

```
Week 1─2: PHASE 1 — Foundation
  ├─ [P0] Persist guild-to-league mapping in Supabase
  ├─ [P0] Extract rulebook into markdown files
  └─ [P1] Refactor ai.ts into focused modules

Week 2─4: PHASE 2 — AI Upgrade
  ├─ [P0] RAG pipeline (embeddings + vector search over rulebook)
  ├─ [P1] Hybrid model routing (mini → gpt-4o escalation)
  └─ [P2] Response caching

Week 4─6: PHASE 3 — Features
  ├─ [P1] Thread-based multi-turn conversations
  ├─ [P1] Dedicated support channel with auto-response
  ├─ [P2] Scheduled alerts (waivers, trades, auctions)
  └─ [P2] New slash commands (/rules, /trade-check, /cap)

Week 6─8: PHASE 4 — Production
  ├─ [P1] Error handling + fallback chain
  ├─ [P2] Rate limiting
  ├─ [P2] Metrics & observability
  └─ [P2] Docker + deployment config
```

**Priority key:** P0 = must-have, P1 = high-value, P2 = nice-to-have

---

## Cost Budget

| Component | Monthly Cost (est.) | Notes |
|-----------|-------------------|-------|
| OpenAI embeddings (indexing) | < $0.01 | One-time per KB update |
| OpenAI embeddings (queries) | < $0.05 | ~1K queries × 100 tokens |
| gpt-4o-mini (80% of queries) | ~$0.40 | 800 queries × ~800 tokens out |
| gpt-4o (20% of queries) | ~$0.50 | 200 queries × ~1000 tokens out |
| **Total** | **~$1.00/month** | vs. ~$0.50 current, for significantly better answers |

At this scale, the cost difference between "all-mini" and "hybrid with gpt-4o" is negligible. The quality improvement is not.

---

## Key Design Decisions

### Why in-process RAG instead of ChromaDB/Pinecone?
Your knowledge base is ~60 chunks. Loading them into memory with embeddings takes < 100KB of RAM and < 1 second. A vector database adds infrastructure complexity, a network hop, and a monthly bill — all for a dataset that fits in a single JSON file. If the KB grows past ~500 chunks, migrate to a proper vector store.

### Why rule-based routing instead of an LLM classifier?
At $0 cost and < 1ms latency, the rule-based classifier handles the obvious cases (strategy questions, comparisons, multi-part queries). It doesn't need to be perfect — routing a simple question to gpt-4o wastes ~$0.005; routing a complex question to mini gives a worse answer. Err toward escalation. If accuracy becomes an issue, upgrade to embedding-based classification (Option B from the hybrid strategy discussion).

### Why not multi-agent routing like customer-service-ai?
The customer-service-ai system routes between billing/technical/policy agents because those domains have fundamentally different retrieval strategies (RAG vs. CAG vs. hybrid). Your bot has one domain (FLF rules) with one retrieval strategy (RAG over the rulebook + live DB context). Multi-agent adds complexity without benefit here. The model tier routing (mini vs. gpt-4o) gives you the quality dial you need.

### Why threads instead of session-based memory?
Discord threads are a natural conversation container — users already understand them, they're visible to other league members (educational), and Discord handles the message storage. Building a custom session manager with Supabase adds DB writes on every message for a feature Discord gives you for free.

---

## Dependencies to Add

```json
{
  "cron": "^3.1.0"
}
```

That's it. The RAG pipeline uses the existing `openai` package. No vector database, no new AI framework, no infrastructure changes.

---

## Migration Checklist

Before starting Phase 2, validate Phase 1:
- [ ] `discord_guild` table exists and `/setup` writes to it
- [ ] Bot survives restart without losing guild mappings
- [ ] Knowledge base markdown files cover all content from the hardcoded string
- [ ] `ai.ts` is split into `src/lib/ai/` modules
- [ ] Existing commands (`/ask`, `/scores`, `/standings`, etc.) still work

Before starting Phase 3, validate Phase 2:
- [ ] RAG retrieves relevant chunks for test queries
- [ ] Hybrid routing correctly escalates complex questions
- [ ] Cache prevents duplicate LLM calls
- [ ] `/reload-kb` re-indexes without restart

Before starting Phase 4, validate Phase 3:
- [ ] Thread conversations maintain context across messages
- [ ] Support channel auto-responds and creates threads
- [ ] Scheduled alerts fire at correct times
- [ ] New slash commands work as expected

---

## Future Considerations (Beyond This Roadmap)

- **Anthropic Claude integration** — If you want Claude as the advanced model, swap `llm-client.ts` to use `@anthropic-ai/sdk`. The routing layer is model-agnostic by design.
- **Buttons & select menus** — Interactive trade review flows, ticket submission. Add after the core AI pipeline is solid.
- **Ephemeral responses** — Use `interaction.reply({ ephemeral: true })` for injury/availability queries. Low effort, add when relevant.
- **Multi-league support** — The guild mapping table already supports multiple leagues per guild (just add another row). The AI context builder already scopes by `leagueId`.
- **Semantic caching** — If exact-match caching has low hit rates, upgrade to embedding-based similarity matching on cached queries. Adds ~$0.000002 per cache lookup.
