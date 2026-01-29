# 🌿 GatherGrove Backend

<p align="center">
  <a href="https://codecov.io/gh/bcarls03/gathergrove-backend">
    <img src="https://codecov.io/gh/bcarls03/gathergrove-backend/branch/main/graph/badge.svg" alt="codecov">
  </a>
  <a href="https://github.com/bcarls03/gathergrove-backend/actions/workflows/tests.yml">
    <img src="https://github.com/bcarls03/gathergrove-backend/actions/workflows/tests.yml/badge.svg" alt="Run Tests">
  </a>
</p>

**Backend API for GatherGrove** — The operating system for real-world gatherings.

Built with **FastAPI + Firebase (Auth & Firestore)** | Python 3.12+ | RESTful API Architecture

> **⚙️ AI Tools Notice**  
> AI assistants working on this codebase **must follow [`AI-PROGRAMMING-RULES.md`](./AI-PROGRAMMING-RULES.md)**.  
> Start each session by reading this file. It defines maintainer mode, file creation policies, and editing constraints.

---

## 🌿 Canonical Strategy

**GatherGrove — Canonical Strategy (Final, Integrated)**  
*A calm operating system for real-world neighborhood coordination*

### 1) North Star and Positioning

**Purpose (one sentence):** GatherGrove helps neighbors discover each other and gather in real life — without feeds, noise, or public posting.

**Positioning anchor:** If Nextdoor is where neighbors talk, GatherGrove is where neighbors actually gather.

**Brand line:** Where neighbors gather

GatherGrove is not a social network. It is not a messaging platform. It is not a marketplace.  
**It is a coordination system for real life.**

### 2) Core Philosophy: The Three Invariants

These are architectural laws. If a feature violates one, it does not ship.

1. **Instant Utility** — Every user experiences value within 60 seconds. No dead feeds. Ever.
2. **Earned Trust** — Trust and verification are progressive, reversible, and optional — never a gate.
3. **Calm Relevance** — Expansion never imports noise. The product must remain quiet, useful, and non-performative.

### 3) Product Constitution: The Mental Model

This governs every UX decision and every future expansion:

- **People are primary**
- **Groups provide context**
- **Events activate connection**

**Translation:** GatherGrove is not a place to post. It is a system to coordinate real-world moments. Everything else exists only to support events.

### 4) Groups: Universal but Invisible

GatherGrove uses a single flexible Group construct to represent real-world structures — but groups are never the navigation model.

**Groups are:**
- not identities
- not destinations
- containers for context only

**Group types (present or latent):**
- Neighborhoods
- Households
- Extended families
- Activity clusters
- Interest clusters

**Critical constraint:** Only Neighborhoods and Households are exposed in early product. All other groups may exist internally without becoming walls, feeds, or surfaces.

This permanently prevents: feeds, posting walls, group spam, social-graph creep.

### 5) Household Model: Linked, Not Forced (Person-First Architecture)

**Core rule:** You do not onboard a household. You onboard a person — who may optionally link into a household.

**Non-negotiable constraints:**
- Each adult has their own account
- A person may exist with zero households
- Households are joined only by invitation or approval
- No shared logins
- No auto-linking
- No forced merges

**Why this matters:** This structure supports couples joining later, separation/divorce, custody realities, roommates or multi-generational homes, changing life stages, and future group types without rewriting identity.

Consent is enforced structurally, not socially.

### 6) Two-Layer Location Model (Core Moat)

**Layer 1: Nearby (Home Zone) — Default**

Purpose: instant value + cold-start immunity
- Approximate location only
- Default ~0.5 miles
- Auto-widens to 3–5 miles if density is low
- Honest framing: "Widening your search until your area gets busier."

*Invariant protected: Instant Utility*

**Layer 2: Verified Neighborhoods — Optional**

Purpose: high-trust named context + future community tooling
- Never required for value
- Progressive, reversible verification
- Hardened governance

*Invariant protected: Earned Trust*

### 7) Onboarding: Calm, Person-First, Trust-Safe (≤60 seconds)

**Design goal:** Deliver immediate value fast while building trust through clarity and reversibility.

**Core pattern:** Draft → Preview → Go Live (optional)  
Nothing becomes visible without explicit confirmation.

**Initial onboarding flow:**
1. **Access (Person only)** — OAuth (Apple / Google). Guardrails: no contacts import, no public posting, consent-gated messaging.
2. **Location (Home Zone)** — City / State / ZIP. Approximate distance only.
3. **Household intent (not structure)** — Family with kids, Singles/Couples, Empty Nesters. Stored as intent, not identity.
4. **Kids' ages (family only)** — Ages only. No names, photos, schools, or birthdays.
5. **Review & Privacy Checkpoint** — Exact discovery card preview. Clear labeling of what is visible vs never shared. Actions: Go live, Edit, Browse first (no household yet).
6. **Magic Moment (Instant Utility)** — Show 3–5 blurred nearby households. CTA: Browse neighbors or Host an event.
7. **Verified neighborhood prompt (conditional)** — Only when confidence is high. Never blocking.

**Progressive completion (after value):**
- Add household details (optional)
- Interests / tags (signals only)
- Invite another adult
- Adjust discovery preferences
- Join or leave households

No nagging. No gates.

### 8) Couple & Household Linking: Canonical Flow

**Primary (V1 default): Invitation link**
- One adult goes live
- Invites via Settings → Household
- Invitee previews and joins
- No duplication

**Secondary:** Independent signup + conservative suggestion (suggested only when high confidence exists; approval always required).

**Duplicates:** Allowed temporarily. Merges are opt-in, explicit, bilateral.

System never: assumes relationships, auto-links, forces merges, blocks usage, deletes accounts.

Consent is constitutional.

### 9) Events: The Activation Engine

Events are invitations, not announcements.

**Only two types:**
- ⚡ **Happening Now** (auto-expires)
- 📅 **Future Event** (RSVP + reminders)

Events: are host-initiated, are context-bounded, can be shared beyond connections, never create feeds or broadcast surfaces.

Everything else supports events.

### 10) Off-Platform Event Invitations (Integrated Canon)

**Core principle:** Delivery adapts to where the recipient already lives.

**Canonical routing:**
- On GatherGrove → in-app invite
- Not on GatherGrove → SMS

SMS is default for non-users, not everyone.

**Intentional SMS for members:** Hosts may optionally tap: "Also text this invite"

**Constraints:** off by default, one action per event, framed as a reminder, uses host's native SMS app, never auto-sent.

SMS remains powerful without becoming noise.

### 11) RSVP Without Signup (Critical)

Off-platform invitees can: open link, view event, RSVP without creating an account.

RSVP: is tied to the event (not identity), visible to host, fully functional.

Joining GatherGrove is positioned as convenience, not obligation.

### 12) Connections: Trust Gate

- Mutual consent required
- No cold DMs
- Connections unlock conversation, not events

Events remain accessible without social pressure.

### 13) Interests & Tags: Signals Only

Optional, skippable, relevance only, never destinations.

If tags become identity labels, they do not ship.

### 14) Categories: Metadata, Not Navigation

Used only: during creation, as light filters. Never as feeds or hubs.

**V1:** 🏡 Neighborhood, 🎪 Playdate, 👶 Babysitting, 🐶 Pets, 🎉 Celebrations, ✨ Other

### 15) Relevance Bands (Visibility Control)

- **Band A (3–5 mi):** Neighborhood, Celebrations
- **Band B (1–2 mi):** Playdate, Babysitting, Pets
- **Band C (<0.5 mi):** Reserved for Verified Neighborhoods

Prevents accidental over-sharing.

### 16) Babysitting: Trust-First, Not a Marketplace

Split intentionally: babysitting events, babysitting availability signal.

**Rules:** neighborhood-only, no ratings, no payments, no browsing marketplace.

**Positioning:** Neighbors helping neighbors.

### 17) Gender Matching for Playdates

**Principle:** Gender is a match attribute, not a public attribute.

- Public cards show ages only
- Gender used only in discovery logic
- Fully reversible in settings

Trust without exposure.

### 18) Navigation: Four Tabs, Four Questions

- 🏠 **Home** — What I'm already part of (invited events, hosted events, messages from connections; orientation, not discovery)
- 🧭 **Discover** — Who I can gather with (household browsing only; invite or connect; no feeds, no performance)
- 📅 **Calendar** — When I'm committed (reference lens only; exportable; never replaces real calendars)
- 👤 **Me** — My setup & privacy (household, privacy, neighborhoods, account; all control, all reversible)

Nothing else ships.

### 19) Invite Flow: Intent-Preserving by Design

Discovery → Compose → Invite → Share

**Key guarantees:** intent never drifts, clicked household always prioritized, suggested = exactly what user just saw, no surprise selections, scalable to large communities.

This is both UX-safe and engineer-safe.

### 20) Alerts (Pilot-Safe)

- **V1:** Lost Pet only
- Admin-enabled
- Auto-expires
- No comments

Never becomes a complaint board.

### 21) Growth Loop (Mechanical, Not Viral)

Event → Attendance → Connections → Better Discovery → Invites → Density

No hacks. No virality. No engagement manipulation.

### 22) Metrics

**North Star:** Weekly active households with 3+ connections

**Engine metric:** Event → Connection conversion rate

Measures real-world tie formation — not scrolling.

### 23) Monetization (Constitutional)

No ads. No data sales. No engagement optimization.

Revenue follows value, never corrupts trust.

- Consumer PWYW
- Consumer Premium (convenience only)
- B2B Community OS
- Trust Services (opt-in, capped)

Anti-patterns never ship.

### 24) System Summary

- Nearby guarantees instant value
- Person-first identity preserves consent
- Events activate connection
- Invitations gate visibility
- SMS assists without becoming system of record
- Memory improves retention privately
- Verified neighborhoods unlock trust later
- Monetization cannot distort behavior

**This system is intentionally narrow. Its durability comes from what it refuses to become.**

### Strategic Feedback Notes

**Strengths (9/10):**
- Cohesive constitution: invariants + mental model control the product
- Cold-start solved: Home Zone + Magic Moment + events-first
- Trust architecture is structural (person-first accounts, consent gates, reversible verification)
- Off-platform invites routing (in-app for members, SMS for non-users)
- Navigation clean and scale-proof (four tabs tied to four questions)

**Path to 10:**
1. Lock the "magic moment" mechanism that ensures new users see 3–5 relevant households in low-density areas
2. Add explicit guardrails for RSVP-without-signup (rate limits, token rules, host controls)
3. Define "successful host" playbook (templates, invite suggestions, reminder timing, minimum viable event)
4. Express the moat as a single unavoidable advantage (verified neighborhood governance + directory trust model + reversible identity ladder)

---

## 📋 Table of Contents

- [Executive Summary](#-executive-summary)
- [The Core Loop](#-the-core-loop)
- [The One Metric That Matters](#-the-one-metric-that-matters)
- [What GatherGrove Is (and Is NOT)](#-what-gathergrove-is-and-is-not)
- [Information Architecture](#-information-architecture)
- [Competitive Advantage](#-competitive-advantage)
- [SWOT Analysis](#-swot-analysis)
- [Quickstart](#-quickstart)
- [Project Structure](#-project-structure)
- [Core Features](#-core-features)
- [API Routes](#-api-routes)
  - [Authentication](#-authentication)
  - [Users API](#-users-api)
  - [Events API](#-events-api)
  - [Households API](#-households-api)
  - [People API](#-people-api)
  - [Profile API](#-profile-api)
  - [Push Notifications API](#-push-notifications-api)
- [Data Models](#-data-models)
- [Feature Roadmap](#-feature-roadmap)
- [Strategic Decisions](#-strategic-decisions)
- [Authentication & Authorization](#-authentication--authorization)
- [Development](#-development)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Contributing](#-contributing)

---

## 🎯 Executive Summary

### Vision & Purpose

**GatherGrove is a calm neighborhood connection app that helps families:**

1. **Discover** nearby households in the same life stage
2. **Coordinate** simple real-life hangouts without group-text chaos  
3. **Remember** those moments privately (optional, no social pressure)

**Philosophy:** Calm, private, functional — anti-Nextdoor noise, more durable than one-off invite tools.

---

### The Core Problem

**Three Gaps:**

1. **Discovery Gap** — Families don't know who nearby they'd naturally click with (kids' ages, similar life stage, interests)
2. **Coordination Friction** — Group texts/email chains bury details, create confusion, lack "source of truth"
3. **Memory Loss** — Great gatherings happen, but photos/details get lost with no quiet, private archive

**Existing solutions are either:**
- **Too noisy** (Nextdoor = complaints/politics, Facebook = algorithmic feeds)
- **Too isolated** (Partiful, Evite = one-off event tools, no community layer)
- **Too chaotic** (Group texts = buried details, no history)

---

### The Solution: Discovery-First Coordination

**GatherGrove helps families discover nearby households in the same life stage, coordinate simple real-world hangouts, and quietly preserve those moments — without social feeds, noise, or pressure.**

**Core Thesis:**  
**"Discovery is the long-term destination. Events are the short-term entry point."**

- **For new users:** Events deliver first value (RSVP via link, no signup required)
- **For established users:** Discovery becomes the hero (neighborhood graph, meaningful connections)
- **For retention:** Memory creates quiet stickiness (optional, private archive)

**Operating Model:** Discovery → Events → Memory

- **Discovery** creates meaning ("people like us live here")
- **Events** activate and coordinate (turn intent into action)  
- **Memory** creates quiet stickiness (optional, private archive)

---

## 🔄 The Core Loop

GatherGrove is built around a simple, powerful loop:

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  DISCOVER → EVENT → ATTEND → REMEMBER → RECONNECT          │
│      ↑                                              ↓       │
│      └──────────────────────────────────────────────┘       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

1. **DISCOVER** — Find nearby households in same life stage ("8 families with kids your age live here!")
2. **EVENT** — Lightweight coordination (functional, not fancy)
3. **ATTEND** — Real-world gatherings happen (the actual goal)
4. **REMEMBER** — Optional photo archive (visible only to attendees, no pressure)
5. **RECONNECT** — Connections deepen, discovery reveals more neighbors

**The Moat:** Your neighborhood graph becomes irreplaceable. Discovery creates meaning. Events activate it. Memory preserves it.

---

## 🎯 North Star Metrics

### **Primary: Weekly Active Households (WAH) with 3+ Connections**

**Why This Matters:**
- Measures **real neighborhood graph formation** (not vanity MAU)
- 3+ connections = trust density achieved = platform becomes valuable
- Once a household has 3+ connections, they're unlikely to leave

**Target Benchmarks:**
- **Week 1**: 30% of signups form 1+ connection
- **Week 4**: 50% of active users have 3+ connections
- **Month 6**: 70% retention for households with 3+ connections

---

### **Secondary: Event-to-Connection Conversion Rate**

**What % of event attendees form at least one new connection?**

**Why This Matters:**
- Validates core thesis: "Events unlock discovery"
- Helps debug why growth stalls or accelerates
- If conversion is low, discovery UX needs work

**Target:** 40%+ of event attendees request/accept a connection within 7 days

---

## ✅ Product Positioning (IS / IS NOT)

### What GatherGrove IS
- ✅ **Discovery-first neighborhood platform** (find families in same life stage)
- ✅ **Lightweight coordination utility** (functional, not performative)
- ✅ **Private, optional memory layer** (no social pressure, attendees-only)
- ✅ **Calm alternative to social media** (no feeds, no infinite scroll)
- ✅ **Trust-gated communication** (connection requests before messaging)

### What GatherGrove is NOT
- ❌ **A "pretty template" event competitor** (that's Partiful's lane)
- ❌ **A social network** (no feeds, likes, followers, engagement optimization)
- ❌ **A complaint forum** (no open neighborhood posting like Nextdoor)
- ❌ **A chat replacement** (event-specific threads only, no endless DMs)

### Primary User (Wedge Case)
**Families with children (ages ~2-12) living in suburban or dense residential neighborhoods.**

Not excluding others — just declaring the wedge.

### Hard Design Rules We Follow

**What We DON'T Build (Anti-Social-Media by Design):**
- ❌ Public feed of all neighborhood activity
- ❌ Like/reaction buttons (breeds comparison)
- ❌ Follower/friend counts (no vanity metrics)
- ❌ Algorithmic sorting (no engagement optimization)
- ❌ Infinite scroll (content has natural end)
- ❌ "Suggested content" (no time-wasting rabbit holes)
- ❌ Unsolicited messaging (connection requests required first)

**What We DO Build (Calm, Functional, Trust-First):**
- ✅ **Discovery-first interface** (map/list of nearby households)
- ✅ **Gated communication** (connection requests before DMs)
- ✅ **Action-oriented language**: "Discover," "Connect," "Host" (not "Post," "Share," "Like")
- ✅ **Warm visual design**: Earthy greens, soft yellows, "weather radar" calm (not social media blues/pinks)
- ✅ **Private by default**: Discovery visible, communication gated
- ✅ **Time-bound content**: Events expire naturally
- ✅ **Quiet notifications**: Opt-in, essential updates only
- ✅ **Instant opt-out**: Discovery can be turned off without losing core functionality

### The North Star Test
> **"Does this feature help people get offline and see each other?"**  
> **If NO → Don't build it.**

### Competitive Positioning (Explicit)
**Why GatherGrove Wins:**
- **Nextdoor** = noise & complaints
- **Event tools** = one-off coordination
- **Group texts** = chaos
- **GatherGrove** = calm, durable neighborhood graph

---

## 🏗️ Information Architecture

### Identity Model: Individual-First, Groups as Context

**Core Principle:** Individuals are the root of trust. Groups organize people.

```
Individual Account (Primary - Source of Truth)
│
├── Profile (Individual Identity)
│   ├── First/Last Name, Photo
│   ├── Address (used for approximate distance only)
│   ├── Privacy Controls (discovery opt-in, address visibility)
│   └── Interests (adult-level, optional)
│
├── Linked Groups (Flexible Organizational Layer)
│   ├── Household (optional linked group)
│   │   ├── Household Type (Family w/ Kids, Singles/Couples, Empty Nesters)
│   │   ├── Child Summary (age ranges + optional gender, NO NAMES/PHOTOS)
│   │   └── Linked Adults (independent accounts)
│   ├── Neighborhoods (discovery context, not ownership)
│   ├── Extended Family (Phase 2+)
│   ├── Interest Groups (Book Club, Sports Teams, etc.) (Phase 2+)
│   └── Activity Groups (Schools, HOAs, Clubs) (Phase 3+)
│
├── Connections (Trust Graph - Gated Communication)
│   ├── Connection Requests (sent/received)
│   ├── Accepted Connections (mutual consent required)
│   └── Messaging (only with accepted connections)
│
├── Events
│   ├── Hosting (created by me) ✅ IMPLEMENTED
│   ├── Attending (RSVP'd yes) ✅ IMPLEMENTED
│   ├── Invited (pending RSVP) 🚧 PHASE 2
│   └── Past Events (memory timeline) 🚧 PHASE 3
│
└── Discovery (The Hero Experience)
    ├── Neighborhood Map/List ⚠️ PARTIAL
    ├── Filters (household type, kids' ages, distance, interests) 🚧 PHASE 2
    ├── Connection Prompts ("8 families with kids your age") 🚧 PHASE 2
    └── Adaptive Empty States (density-aware) 🚧 PHASE 2
```

**Key Principles:**
- **Individuals retain agency** — No one is listed/grouped without personal consent
- **Groups provide context** — Households, neighborhoods are organizational layers, not primary identity
- **Discovery visible, communication gated** — Anyone can browse, messaging requires connection acceptance
- **Privacy always individual-controlled** — Group membership never overrides personal privacy settings

---

### Groups as Universal Organizing Layer

GatherGrove uses a single, flexible "Group" construct to represent real-world social structures.

**Groups are not hard-coded silos. They are containers for context.**

**Group Types (Now and Later):**
- ✅ **Neighborhoods** (MVP) — Geographic discovery context
- ✅ **Households** (MVP) — Family unit grouping
- 🚧 **Extended Families** (Phase 2) — Multi-household family connections
- 🚧 **Activity Groups** (Phase 2) — Sports teams, clubs, book clubs
- 🚧 **Interest Groups** (Phase 2) — Hiking buddies, dinner clubs
- 🚧 **Organizations** (Phase 3) — HOAs, schools, churches

**This design allows GatherGrove to:**
- Start focused (neighborhood + household)
- Expand naturally (activities, interests, extended families)
- Avoid re-architecting as new use cases emerge

---

### Household as Linked Group (Not Primary Identity)

Households are treated as a **linked group**, not a primary identity.
- Users may **choose** to link themselves to a household
- Adults can join, leave, or update household membership independently
- The household functions as a **directory card for discovery**
- Individual profiles remain the **source of truth**

This preserves:
- Individual consent
- Clear ownership
- Flexibility for non-traditional households

---

## 🔒 Privacy & Trust Framework

### What Parents Are NOT Comfortable With
- ❌ Exact addresses or exact map pins
- ❌ Public visibility outside the community
- ❌ Open/unsolicited messaging
- ❌ Children's names, birthdays, schools, or photos
- ❌ Being listed without explanation or control

### What Parents ARE Comfortable With
- ✅ Approximate distance ("~0.3 miles away")
- ✅ Abstracted/blurred maps ("weather radar" vibe, not Google Maps precision)
- ✅ Real family identity (last names help build trust)
- ✅ Gated messaging (connection request first)
- ✅ Kids represented by **age ranges** + optional gender (never names/photos)
- ✅ Clear explanation + instant opt-out

### Location & Discovery Rules (Non-Negotiable)

**1. Never Show Exact Home Location**
- Use soft dots/clusters and approximate distance labels
- Calm "weather radar" vibe, not Google Maps precision
- Distance shown as "~0.3mi" (approximate)

**2. Discovery Visible, Communication Gated**
- Anyone can browse households (discovery)
- Messaging requires mutual connection acceptance (trust gate)
- No phone/email shown by default

**3. Discovery Can Be Turned Off Instantly**
- App still works without discovery (events, connections remain)
- Opt-out must never feel punitive
- Re-enable anytime

### Connection Requests (Trust Gate)

**How It Works:**
1. User sees interesting household in discovery
2. Sends connection request (with optional message)
3. Recipient accepts/declines
4. Only after acceptance can messaging begin

**Why This Matters:**
- Prevents spam and harassment
- Establishes "mutual intent" before communication
- Creates trust density before opening DMs



```
Event Object
│
├── Basic Info
│   ├── Title, Description ✅ IMPLEMENTED
│   ├── Cover Photo 🚧 PHASE 2 (AI-generated or uploaded)
│   ├── Date/Time (or "Happening Now") ✅ IMPLEMENTED
│   ├── Location (address + map) ✅ IMPLEMENTED
│   └── Host(s) ⚠️ SINGLE HOST ONLY (co-hosting in Phase 2)
│
├── Invitation Settings
│   ├── Visibility (Private Link / Groups / Neighborhood) 🚧 PHASE 2
│   ├── RSVP Deadline 🚧 PHASE 2
│   ├── Capacity (optional) ✅ IMPLEMENTED
│   └── RSVP Questions (dietary restrictions, etc.) 🚧 PHASE 2
│
├── Guest Management
│   ├── Invited List (GatherGrove users + external) 🚧 PHASE 2
│   ├── RSVP Status (Going / Maybe / No / Pending) ✅ IMPLEMENTED
│   ├── Attendee Tracking (who actually showed up) 🚧 PHASE 3
│   └── Event-specific messaging thread 🚧 PHASE 2
│
└── Post-Event (REMEMBER phase) 🚧 PHASE 3
    ├── Photo Album (linked or uploaded)
    ├── Attendee List (preserved permanently)
    ├── Host Notes (recap, highlights)
    └── "Host Again" button (one-tap duplicate)
```

**Legend:**
- ✅ **Implemented** - Live in current backend
- ⚠️ **Partial** - Exists but needs enhancement
- 🚧 **Planned** - Roadmap for Phase 2-3

---

## 🏆 Competitive Advantage

**Why GatherGrove Wins:**

| Competitor | Their Problem | GatherGrove's Solution |
|-----------|---------------|----------------------|
| **Nextdoor** | Noise & complaints, toxic community | Calm discovery, gated communication, events-only |
| **Partiful/Evite** | One-off coordination, no community | Discovery unlocks neighborhood graph, memory creates stickiness |
| **Group texts** | Chaos, no source of truth | Structured events, clear RSVP states, persistent history |
| **Facebook** | Algorithmic feeds, privacy concerns | No feeds, no ads, trust-first design |

**The Moat:** Your neighborhood graph becomes irreplaceable.
- Discovery creates meaning ("people like us live here")
- Events activate connections (turn intent into action)
- Memory preserves relationships (quiet stickiness)

**Defend Against Copycats:**
- **If Facebook launches "Neighbors"** → Emphasize privacy (they can't credibly claim this)
- **If Nextdoor adds events** → Emphasize calm UX (they won't abandon their feed model)
- **If Partiful adds discovery** → Emphasize memory (they haven't built this)

---

## 📊 SWOT Analysis

### Strengths ✅
1. **Discovery-first wedge** — "8 families with kids your age live here" is an instant value unlock
2. **Gated communication** — Connection requests eliminate spam/harassment concerns
3. **Clear differentiation** — Anti-social-media by design (no feeds, no infinite scroll, no noise)
4. **Network effects** — More neighborhood users = better discovery = more valuable connections
5. **Calm UX as moat** — Competitors can't copy "calm" without abandoning their engagement models
6. **Macro tailwinds** — Loneliness epidemic + post-COVID IRL hunger = massive timing advantage

### Weaknesses ⚠️
1. **Chicken-egg problem** — Discovery features only work at 10-15 households per neighborhood
2. **Density-dependent value** — Low-density neighborhoods struggle to show immediate value
3. **Execution risk** — Must nail "weather radar" map UX (calm, not creepy)
4. **Education needed** — Users must understand discovery ≠ unsolicited messaging
5. **Monetization uncertainty** — Premium features need validation before scaling

### Opportunities 🚀
1. **Nextdoor fatigue** — Users tired of complaints/politics, hungry for positive alternative
2. **Gen Z family formation** — New parents seeking neighborhood community (high LTV)
3. **B2B verified communities** — HOAs/schools willing to pay for verified neighborhood tools
4. **Babysitting marketplace** — Natural monetization lever for families (Phase 2)
5. **International expansion** — Social fragmentation is global (UK, Australia, Canada)

### Threats 🚨
1. **Facebook/Nextdoor copies feature** — Distribution advantage if incumbents fix UX
2. **Privacy regulations** — GDPR/CCPA could limit location-based discovery
3. **Moderation burden** — Bad actors could abuse neighborhood discovery at scale
4. **User skepticism** — "Another app?" fatigue (must prove value instantly)
5. **Economic downturn** — Premium subscriptions harder to sell in recession

### Likelihood of Success: 8.0/10 ⭐⭐⭐⭐⭐⭐⭐⭐

**Why This High:**
- ✅ Discovery-first wedge solves validated pain point ("Who lives near me?")
- ✅ Gated communication addresses #1 trust concern (no spam)
- ✅ Calm positioning is defensible (competitors trapped in engagement models)
- ✅ Multiple revenue paths (freemium, babysitting, B2B)
- ✅ Density-aware UX prevents "empty state" problem

**Risks to Watch:**
- Must nail first 60 seconds ("We found 8 families…" must feel magical)
- Connection acceptance rate needs to be >60% (otherwise discovery feels isolating)
- Need 10-15 households/neighborhood to hit critical mass

**Bottom Line:** Discovery-first positioning + gated communication = differentiated wedge that incumbents can't easily copy.

**Key Design Principles:**
- Privacy-first: All data scoped to authenticated neighborhood members
- UTC timestamps throughout for timezone consistency
- In-memory fake Firestore for fast local development and CI testing
- Comprehensive test coverage with pytest

---

## 🚀 Quickstart

### Local Development

**Prerequisites:**
- Python 3.12+ (3.13 supported)
- Firebase Admin SDK credentials (for production mode)

**1️⃣ Clone and Install**
```bash
git clone https://github.com/bcarls03/gathergrove-backend.git
cd gathergrove-backend
pip install -r requirements.txt
```

**2️⃣ Run Development Server**
```bash
# Option A: Use the dev script (sets dev flags automatically)
./scripts/dev.sh

# Option B: Manual start with dev auth
export ALLOW_DEV_AUTH=1
export SKIP_FIREBASE_INIT=1
uvicorn app.main:app --reload --port 8000
```

**3️⃣ Open API Documentation**
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc
- **OpenAPI JSON**: http://127.0.0.1:8000/openapi.json

**4️⃣ Test the API**
```bash
# Health check
curl http://127.0.0.1:8000/health

# Test Firebase/DB connection
curl http://127.0.0.1:8000/firebase

# Check your identity (dev mode)
curl http://127.0.0.1:8000/whoami \
  -H "X-Uid: brian" \
  -H "X-Email: brian@example.com" \
  -H "X-Admin: false"
```

---

## 📁 Project Structure

```
gathergrove-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app, CORS, route registration
│   ├── core/
│   │   └── firebase.py         # Firebase Admin SDK + in-memory fake DB
│   ├── deps/
│   │   └── auth.py             # Authentication dependency (dev/prod modes)
│   ├── models/
│   │   ├── events.py           # Event-related Pydantic models
│   │   └── rsvp.py             # RSVP models and enums
│   └── routes/
│       ├── events.py           # Event creation, listing, RSVPs
│       ├── users.py            # User management and favorites
│       ├── households.py       # Household directory
│       ├── people.py           # People directory (derived from households)
│       ├── profile.py          # User profiles with settings
│       └── push.py             # Push notification token management
├── docs/
│   └── schema.md               # Comprehensive Firestore schema documentation
├── scripts/
│   ├── dev.sh                  # Local development startup script
│   └── validate_events.sh      # Event validation script
├── secrets/
│   └── gathergrove-dev-firebase-adminsdk.json  # Firebase credentials (gitignored)
├── tests/
│   ├── conftest.py             # Pytest fixtures and test setup
│   ├── test_events.py          # Event API tests
│   ├── test_users.py           # User API tests
│   ├── test_households.py      # Household API tests
│   ├── test_people*.py         # People API tests (pagination, filters)
│   └── test_favorites.py       # Favorites functionality tests
├── .github/
│   └── workflows/
│       └── tests.yml           # CI: Python 3.12 & 3.13 test matrix
├── requirements.txt            # Python dependencies
├── pytest.ini                  # Pytest configuration
├── openapi.json                # Generated OpenAPI schema
└── README.md                   # This file
```

---

## 🎨 Core Product Areas

### 1. Discovery (Neighborhood View - The Hero)

**This is the primary value proposition for established users.**

**Features:**
- Map/list view of nearby households
- Filters: household type, kids' age ranges, distance radius, interests
- Household cards showing:
  - Last name, approximate distance ("~0.3mi")
  - Household type (Family w/ Kids, etc.)
  - Child age ranges + optional gender (NO names/photos)
  - Adult interests (optional)
- **Adaptive Empty States** (density-aware):
  - High density → "8 families with kids your age!" (hero CTA)
  - Low density → "You're early 🎉" + invite prompts
- **Connection Requests** (see Connections section)

**Privacy Guardrails:**
- Never show exact addresses (soft dots/clusters on map)
- Distance shown as approximate ("~0.3mi")
- "Weather radar" calm vibe, not Google Maps precision
- Discovery can be turned off instantly (app still works)

---

### 2. Connections (Trust Gate)

**Gated communication prevents spam and establishes mutual intent.**

**Flow:**
1. User discovers interesting household via map/list
2. Sends connection request (with optional message)
3. Recipient accepts/declines
4. Only after acceptance can messaging begin

**Why This Matters:**
- Prevents unsolicited messaging (top parent concern)
- Creates "mutual intent" before DMs
- Builds trust density in neighborhood graph

**States:**
- Pending (request sent, awaiting response)
- Accepted (can message)
- Declined (no further action)

---

### 3. Events (Coordination + Growth Engine)

**Lightweight event creation — functional, not fancy.**

**Event Categories** (8 total):
1. **🏡 Neighborhood** — Block parties, driveway hangs, cul-de-sac meetups
2. **🎪 Playdate** — Park meetups, family fun
3. **🤝 Help & Favors** — Borrow tools, rides, **babysitting requests** (see Babysitting section)
4. **🐶 Pets** — Dog playtimes, pet sitting, lost/found
5. **🍽️ Food & Dining** — Potlucks, dinners, restaurant outings
6. **🎉 Celebrations** — Birthdays, holidays, milestones
7. **⚽ Sports & Activities** — Pickup games, workouts, adventures
8. **✨ Other** — Anything else

**Event Timing Model:**
- **Happening Now**: Events starting within 2 hours (🔴 "Live Now" badge)
  - Badge appears automatically (time-based, not host-controlled)
  - Persists until event end time
- **Future Events**: Scheduled with time-bucket labels
  - 🟢 "This Weekend", 🔵 "Next Week", ⚪ "Future"
- **Single Events List**: One unified view with status badges (no separate tabs)

**Invitation Options:**
- Invite GatherGrove neighbors (via discovery)
- Invite connections (accepted relationships)
- Invite external (shareable link, no signup required to RSVP)

**RSVP States:**
- `going`: Confirmed attendance (counts toward capacity)
- `maybe`: Tentative
- `declined`: Not attending

**Shareable Event Links:**
- Text/email links for non-members
- RSVP without signup (soft-entry growth)
- "Created with GatherGrove" footer (viral attribution)

---

### 4. Memory (Optional, Private)

**Quiet post-event prompt — no social pressure.**

**Flow:**
1. Event ends
2. Quiet prompt: "Add photo / link album / skip"
3. Photos visible only to attendees
4. No feed, no likes, no public sharing

**Why This Matters:**
- Creates emotional stickiness
- Preserves moments without performative pressure
- Builds switching costs (your memories live here)

**Phase 1 Scope:**
- Manual photo upload or Google Photos link
- Attendee-only visibility
- Simple grid view

---

### 5. Onboarding Strategy (Progressive, Trust-First)

**Goal:** Collect only what's needed, when it's needed. Minimize friction while building trust.

**Authentication:**
- Apple Sign-In / Google Sign-In (secure auth only, not for importing social graphs)
- Identity remains individual-first, privacy-controlled, independent of external platforms

**Step 1: Personal Identity** (Required)
- First and last name
- Optional photo
- Address (used only for approximate distance)
- Discovery enabled by default, with instant opt-out

**Step 2: Household Context** (Required)
User selects household unit:
- Family w/ Kids
- Singles / Couples
- Empty Nesters

This determines:
- Which discovery filters apply
- Whether child-related fields are shown

**Step 3: Child Information** (Family Only, Required)
- Child age (required for meaningful discovery)
- Child gender (optional: Male / Female / Prefer not to say)
- **NO child names, birthdays, schools, or photos**

**Step 4: Interests** (Optional, Skippable)
- Adult interests (per individual)
- Child interests (per child, parent-entered)
- Controlled vocabulary (no free text)

**Step 5: Privacy Review** (Required)
Plain-language preview showing:
- What others can see
- What is never shown
- How to opt out instantly

**Step 6: Immediate Value** 🎉
**"We found X families near you…"**

Discovery reinforces why the information was worth sharing.

---

### 6. Babysitting (MVP → Future Monetization Lever)

**Purpose:** Enable trusted, local babysitting discovery within the neighborhood — starting simple, private, opt-in.

**MVP Scope:**
- During household setup, families with children can optionally mark a child as: **"Available for Babysitting"**
- This is a visibility flag only (no payments, scheduling, or reviews in MVP)
- Babysitting framed as neighborly help signal, not marketplace

**How It Works (High-Level):**

**1. Opt-In Flag**
- Household toggles "Available for Babysitting" for eligible children
- Child shown only as **Age + Gender** (no name), consistent with GatherGrove privacy standards

**2. Discovery**
- New "Babysitters" filter within People tab
- Allows families to quickly see nearby households with babysitting availability

**3. Requests**
- Babysitting requests flow through existing "Help & Favors" category
- All coordination happens via GatherGrove messaging (no public posts)

**Guardrails & Trust (MVP):**
- Fully opt-in
- Neighborhood-only visibility
- No ratings, reviews, or transactions in MVP

**Future Expansion (Post-MVP / Premium):**
- Optional verification badges (age confirmation, parental consent)
- Reviews/references within neighborhood
- Priority visibility or trust indicators as premium monetization lever

**Positioning Principle:**
> Babysitting in GatherGrove is about trusted neighbors helping neighbors, not building a gig marketplace.

GatherGrove does not facilitate unsupervised introductions or payments in MVP.

---

### 7. Growth Model (Soft-Entry, Not Pushy)

**Primary Growth Paths:**
1. **Discovery-first signup** (immediate value: "8 families found!")
2. **Event link invites** to non-members (RSVP without signup)
3. **Word-of-mouth** after real hangouts ("We met on GatherGrove")

**Principles:**
- No contact scraping
- No spammy invites
- Signup happens when it clearly adds value (messaging, discovery, future invites)

**Viral Coefficient Math:**
- Target: 1.5+ (each user brings 1.5+ new users)
- Current model: Each user invites 5 people:
  - 3 neighbors (via discovery prompts)
  - 2 external friends (via event links)
- Conversion rates needed:
  - 30% of invitees sign up
  - 50% of signups create a connection or attend event
- Math: 5 invites × 0.30 conversion × 0.50 activation = 0.75
- **Need to optimize to reach 1.5 for true viral growth**

**Levers to Pull:**
- Increase invite prompts (currently 1, test 2-3)
- Improve event link conversion (A/B test landing page)
- Boost signup → connection creation (smart defaults, prompts)

---

### 8. Empty Discovery Handling (Must-Have)

**Never show "No neighbors found" as a dead end.**

**Instead, show adaptive CTAs based on density:**

**Low Density (0-5 households):**
```
🎉 You're early!

Be the first to bring GatherGrove to your neighborhood:
1. Invite a neighbor
2. Create an event (invite anyone)
3. Share your event link
```

**Medium Density (6-15 households):**
```
Great start! 8 families nearby.

Help grow your neighborhood:
- Invite 2 more neighbors
- Host an event this weekend
```

**High Density (15+ households):**
```
🎉 We found 23 families near you with kids your age!

[View Discovery Map]
```

**Principle:** Discovery should show potential (teaser counts, progress state), not emptiness.

---

## 🔌 API Routes

### 🔐 Authentication

All routes (except `/health` and `/`) require authentication.

**Development Mode** (`ALLOW_DEV_AUTH=1` or `SKIP_FIREBASE_INIT=1`):
- Use headers: `X-Uid`, `X-Email`, `X-Admin`
- Example:
  ```bash
  -H "X-Uid: brian" \
  -H "X-Email: brian@example.com" \
  -H "X-Admin: false"
  ```

**Production Mode**:
- Use Firebase ID token: `Authorization: Bearer <firebase_id_token>`
- Admin status determined by custom claim: `{ "admin": true }`

### 👤 Users API

**Base Path**: `/users`

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/users` | Create/update own user (upsert) | Owner |
| `PATCH` | `/users/me` | Partially update own user | Owner |
| `GET` | `/users/me` | Get own user document | Owner |
| `GET` | `/users/{user_id}` | Get specific user by ID | Owner/Admin |
| `PATCH` | `/users/{uid}` | Update user by UID | Owner/Admin |
| `GET` | `/users` | List all users (paginated) | Admin |
| `GET` | `/users/me/favorites` | List favorited households | Owner |
| `POST` | `/users/me/favorites/{household_id}` | Add household to favorites | Owner |
| `DELETE` | `/users/me/favorites/{household_id}` | Remove from favorites | Owner |

**Key Features**:
- `isAdmin` field ignored unless caller has `admin: true` token claim (prevents privilege escalation)
- Auto-timestamps: `createdAt` (on create), `updatedAt` (always)
- Favorites stored as array of household IDs on user document

**Example: Create User**
```bash
curl -X POST http://127.0.0.1:8000/users \
  -H "Content-Type: application/json" \
  -H "X-Uid: brian" -H "X-Email: brian@example.com" -H "X-Admin: false" \
  -d '{"name":"Brian Carlberg","isAdmin":false}'
```

### 📅 Events API

**Base Path**: `/events`

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/events` | Create event (caller becomes host) | User |
| `GET` | `/events` | List events (filterable, paginated) | User |
| `GET` | `/events/{event_id}` | Get event by ID | User |
| `PATCH` | `/events/{event_id}` | Update event | Host/Admin |
| `PATCH` | `/events/{event_id}/cancel` | Soft-cancel event | Host/Admin |
| `DELETE` | `/events/{event_id}` | Hard-delete event | Host/Admin |
| `GET` | `/events/{event_id}/rsvp` | Get RSVP summary + user status | User |
| `POST` | `/events/{event_id}/rsvp` | RSVP to event | User |
| `DELETE` | `/events/{event_id}/rsvp` | Remove RSVP (leave event) | User |
| `GET` | `/events/{event_id}/attendees` | List all attendees (bucketed) | User |
| `GET` | `/events/{event_id}/attendees/going` | List going attendees | User |

**Query Parameters** (`GET /events`):
- `type`: `now` | `future` (filter by time window)
- `neighborhood`: Filter to single neighborhood
- `category`: `neighborhood` | `playdate` | `help` | `pet` | `other`
- `limit`: 1-50 (default 20)
- `nextPageToken`: Opaque pagination cursor

**Time Window Logic**:
- `type=now`: `startAt <= now < (endAt OR expiresAt)`
- `type=future`: `startAt > now`
- Omitted: Both now and future (excludes expired)
- **Always excludes**: Events where `expiresAt <= now`

**RSVP Status**:
- `going`: Confirmed attendance (counts toward capacity)
- `maybe`: Tentative
- `declined`/`cant`: Not attending

**Example: Create Future Event**
```bash
curl -X POST http://127.0.0.1:8000/events \
  -H "Content-Type: application/json" \
  -H "X-Uid: brian" -H "X-Email: brian@example.com" -H "X-Admin: false" \
  -d '{
    "type": "future",
    "title": "Neighborhood Potluck",
    "details": "Bring a dish to share!",
    "startAt": "2025-12-28T18:00:00Z",
    "endAt": "2025-12-28T21:00:00Z",
    "neighborhoods": ["Bay Hill", "Eagles Point"],
    "category": "neighborhood",
    "capacity": 20
  }'
```

**Example: RSVP to Event**
```bash
curl -X POST http://127.0.0.1:8000/events/{event_id}/rsvp \
  -H "Content-Type: application/json" \
  -H "X-Uid: brian" -H "X-Email: brian@example.com" -H "X-Admin: false" \
  -d '{"status":"going"}'
```

### 🏡 Households API

**Base Path**: `/households`

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/households` | List households (filterable) | User |
| `POST` | `/households` | Create/update own household | Owner |

**Query Parameters**:
- `neighborhood`: Filter by neighborhood name
- `household_type` or `type`: Filter by type (checks both `type` and `householdType` fields)

**Household Types** (legacy + new):
- Legacy: `family`, `emptyNest`, `singleCouple`
- New: `Family w/ Kids`, `Empty Nesters`, `Single/Couple`, etc.

**Field Normalization**:
- `adultNames`: Always returned as array of strings
- `kids`/`Kids`: Case-insensitive handling
- Sorted by `lastName` (case-insensitive), then by ID

### 👥 People API

**Base Path**: `/people`

The People API is a **derived view from households** with enhanced filtering capabilities.

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/people` | List people/households (advanced filters) | User |
| `POST` | `/people/{household_id}/favorite` | Add household to favorites | User |
| `DELETE` | `/people/{household_id}/favorite` | Remove from favorites | User |

**Query Parameters**:
- `neighborhood`: Single neighborhood filter
- `type`: `family` | `empty_nesters` | `singles_couples`
- `ageMin`: Minimum child age (0-18)
- `ageMax`: Maximum child age (0-18)
- `search`: Last name prefix search (case-insensitive)
- `pageSize`: 1-50 (default 20)
- `pageToken`: Opaque base64-encoded cursor

**Age Filter Logic**:
- Returns households where **any child** falls within `[ageMin, ageMax]`
- Both parameters optional
- Defaults: `ageMin=0`, `ageMax=18`

**Example: Find Families with Young Kids**
```bash
curl "http://127.0.0.1:8000/people?type=family&ageMin=3&ageMax=7&neighborhood=Bay%20Hill" \
  -H "X-Uid: brian" -H "X-Email: brian@example.com" -H "X-Admin: false"
```

**Response Shape**:
```json
{
  "items": [
    {
      "id": "h123",
      "lastName": "Smith",
      "type": "family",
      "neighborhood": "Bay Hill",
      "adultNames": ["John Smith", "Jane Smith"],
      "childAges": [5, 7],
      "householdType": "Family w/ Kids"
    }
  ],
  "nextPageToken": "eyJjdXJzb3IiOiJoMTIzIn0="
}
```

### 🧑‍💼 Profile API

**Base Path**: `/profile`

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/profile` | Get own profile (creates if missing) | User |
| `PATCH` | `/profile` | Update profile settings | User |
| `GET` | `/profile/favorites` | Get favorites list (household IDs) | User |
| `PUT` | `/profile/favorites/{household_id}` | Add to favorites | User |
| `DELETE` | `/profile/favorites/{household_id}` | Remove from favorites | User |
| `GET` | `/profile/overrides` | Get include/exclude lists | User |
| `PUT` | `/profile/overrides` | Update include/exclude lists | User |

**Profile Fields**:
- `display_last_name`: Override household last name display
- `visibility`: `neighbors` (default) | `private` | `public`
- `bio`: Free-text about section (max 500 chars)
- `favorites`: Array of household IDs
- `neighbors_include`: Always show these households
- `neighbors_exclude`: Hide these households
- `notifications_enabled`: Push notification toggle

**Example: Update Profile**
```bash
curl -X PATCH http://127.0.0.1:8000/profile \
  -H "Content-Type: application/json" \
  -H "X-Uid: brian" -H "X-Email: brian@example.com" -H "X-Admin: false" \
  -d '{
    "bio": "Love neighborhood events!",
    "visibility": "neighbors",
    "notifications_enabled": true
  }'
```

### 🔔 Push Notifications API

**Base Path**: `/push`

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/push/register` | Register/update device push token | User |
| `GET` | `/push/tokens` | List own registered tokens | User |
| `DELETE` | `/push/tokens/{token}` | Delete a push token | User |

**Token Registration**:
```json
{
  "token": "ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]",
  "platform": "ios"
}
```

**Platforms**: `ios`, `android`, `web`, `unknown`

**Security**:
- Tokens scoped to authenticated user (UID from token claim)
- `uid` field in request body ignored (prevents token theft)
- Admin debug mode: `allow_uid_override=true` query param (admin-only)

---

## 📊 Data Models

### Firestore Collections

#### `users` Collection
**Document ID**: `{uid}` (Firebase Auth UID)

```typescript
{
  uid: string              // Firebase Auth UID
  email: string            // User email
  name: string             // Display name
  isAdmin: boolean         // Informational only (use token claim)
  favorites: string[]      // Array of household IDs
  createdAt: timestamp     // UTC
  updatedAt: timestamp     // UTC
}
```

#### `events` Collection
**Document ID**: Auto-generated

```typescript
{
  // ===== CORE FIELDS (✅ Implemented) =====
  id: string
  type: "now" | "future"
  title: string
  details?: string
  startAt: timestamp       // UTC, required for future
  endAt?: timestamp        // UTC
  expiresAt?: timestamp    // UTC, defaults to startAt+24h for "now"
  capacity?: number        // Optional attendance cap
  neighborhoods: string[]  // e.g. ["Bay Hill", "Eagles Point"]
  category?: "neighborhood" | "playdate" | "help" | "pet" | "food" | "celebration" | "sports" | "other"
  hostUid: string          // Event creator
  status?: "active" | "canceled"
  canceledAt?: timestamp
  canceledBy?: string
  createdAt: timestamp
  updatedAt: timestamp
  
  // ===== PHASE 2: Enhanced Event Structure (🚧 Planned) =====
  coverImage?: string          // URL to AI-generated or uploaded image
  coHosts?: string[]           // Array of user IDs (multi-host support)
  visibility?: "private" | "link_only" | "neighborhood" | "public"
  shareableLink?: string       // Public RSVP page URL (no login required)
  rsvpDeadline?: timestamp     // UTC deadline for RSVPs
  rsvpQuestions?: Array<{      // Custom questions for attendees
    question: string
    required: boolean
  }>
  
  // ===== PHASE 2: Invitation Tracking (🚧 Planned) =====
  invitedUserIds?: string[]    // Explicit invite list (GatherGrove users)
  invitedExternal?: Array<{    // External invites (non-users)
    name: string
    phone?: string
    email?: string
  }>
  
  // ===== PHASE 3: Post-Event Capture (🚧 Planned) =====
  photoAlbumUrl?: string       // Link to Google Photos or uploaded album
  hostNotes?: string           // Post-event recap
  actualAttendees?: string[]   // Who actually showed up (vs RSVPs)
  memoryCard?: {               // Auto-generated memory card
    dateStamp: string
    attendeeCount: number
    photoCollageUrl?: string
  }
  
  // ===== PHASE 3: Viral Loop Tracking (🚧 Planned) =====
  createdFrom?: "duplicate" | "new"  // Track "Host Again" usage
  originalEventId?: string           // If duplicated from another event
  viralMetrics?: {
    invitesSent: number
    rsvpsFromNonUsers: number
    conversionsToSignup: number
  }
}
```

**Business Rules**:
- `type: "future"` → `startAt` required
- `type: "now"` → `startAt` defaults to `now()`, `expiresAt` defaults to `startAt + 24h`
- Capacity enforced only for `status: "going"` RSVPs
- Canceled events remain readable but RSVP operations return 409

#### `event_attendees` Collection
**Document ID**: `{event_id}_{uid}` (composite key)

```typescript
{
  eventId: string          // Reference to events/{id}
  uid: string              // Reference to users/{uid}
  status: "going" | "maybe" | "declined"
  rsvpAt: timestamp        // UTC
}
```

**Notes**:
- `declined` stored internally, exposed as `cant` in API
- Upsert semantics: POST updates existing RSVP

#### `households` Collection
**Document ID**: `{household_id}` or `{uid}`

```typescript
{
  id: string
  lastName: string         // Or householdLastName
  type?: string            // Legacy: family/emptyNest/singleCouple
  householdType?: string   // New: "Family w/ Kids", etc.
  neighborhood: string     // Or neighborhoodName/neighborhoodCode
  adultNames: string[]     // Adult names in household
  children?: Array<{       // Child records
    age: number
    sex?: "M" | "F"
  }>
  kids?: any               // Alternative children field
  createdAt: timestamp
  updatedAt: timestamp
}
```

**Field Variations** (all supported via normalization):
- Neighborhood: `neighborhood`, `neighborhoodName`, `neighborhoodCode`, `neighborhoodId`
- Type: `type`, `householdType`, `kind`
- Children: `children`, `Kids`, `kids`

#### `profiles` Collection
**Document ID**: `{uid}`

```typescript
{
  // ===== CORE FIELDS (✅ Implemented) =====
  uid: string
  email: string
  display_last_name?: string
  visibility: "neighbors" | "private" | "public"
  bio?: string
  favorites: string[]          // Household IDs
  neighbors_include: string[]  // Always show
  neighbors_exclude: string[]  // Always hide
  notifications_enabled: boolean
  created_at: timestamp
  updated_at: timestamp
  
  // ===== PHASE 2: Enhanced Profile & Connections (🚧 Planned) =====
  householdType?: "family_with_kids" | "empty_nesters" | "singles_couples"
  childAgeRanges?: string[]    // e.g. ["0-2", "3-5", "6-8"] NOT exact ages
  interests?: string[]         // Tags: ["hiking", "board_games", "cooking"]
  addressVisibility?: "exact" | "approximate" | "hidden"  // Default: approximate
  
  linkedHousehold?: {          // Optional household linking
    spouseUid?: string         // Partner's account
    childrenUids?: string[]    // Children's accounts (if they have their own)
  }
  
  groupMemberships?: Array<{   // Multi-context memberships
    groupId: string
    groupType: "family" | "hoa" | "friend_group" | "team" | "club" | "custom"
    role?: "member" | "admin"
    joinedAt: timestamp
  }>
  
  // ===== PHASE 3: Memory Timeline Preferences (🚧 Planned) =====
  memoryTimelineEnabled?: boolean
  memoryNotifications?: boolean  // "Your BBQ was 1 year ago today!"
  premiumTier?: "free" | "premium" | "verified"
  premiumSince?: timestamp
}
```

**Privacy Rules (Critical):**
- **Kids' Privacy**: `childAgeRanges` ONLY, never store exact ages, names, or photos of minors
- **Location Privacy**: Default to `addressVisibility: "approximate"` (~0.3mi radius)
- **Discovery Opt-In**: Neighborhood discovery requires explicit consent

#### `pushTokens` Collection
**Document ID**: `{uid}_{token_hash}` or similar

```typescript
{
  uid: string              // Owner
  token: string            // Device push token
  platform: "ios" | "android" | "web" | "unknown"
  registeredAt: timestamp
  updatedAt: timestamp
}
```

### Pydantic Models (API Layer)

Located in `app/models/` and route files:

**Event Models**:
- `EventIn`: Create event request
- `EventPatch`: Partial update request
- `RSVPIn`: RSVP status update
- `EventRsvpHousehold`: Attendee household info
- `EventRsvpBuckets`: Attendees grouped by status

**User Models**:
- `UserIn`: User creation request
- `UserPatch`: Partial user update

**Profile Models**:
- `ProfileUpdate`: Profile update request
- `ProfileOut`: Profile response

---

## �️ Feature Roadmap

### **MVP (Months 1-3): The Core Loop** ✅ IN PROGRESS

**Goal:** Prove the viral loop works (30% of invitees create their own event within 30 days)

**Must-Have Features:**
1. ✅ **Event Creation**
   - 5 beautiful templates (BBQ, birthday, dinner, playdate, casual hangout)
   - 60-second creation flow
   - Location autocomplete + map preview
   
2. ✅ **Zero-Friction RSVP**
   - Public event pages (no login required)
   - Name + optional contact capture
   - Social proof (show who's attending)
   - Viral footer: "Created with GatherGrove"
   
3. ✅ **Smart Invitations**
   - Copy link for SMS/WhatsApp
   - Import phone contacts
   - Email invites (fallback)
   
4. ✅ **Basic Onboarding**
   - Google/Apple OAuth signup
   - Optional profile (location, household type, interests)
   - No forced fields
   
5. ✅ **Event Status**
   - "Happening Now" vs. "Future" badges
   - Push notifications for RSVPs
   - Calendar sync (Google/iCal)

**Success Metrics:**
- 30% of invitees create their own event within 30 days
- 50%+ RSVP rate on invitations
- 40%+ month-over-month user growth

---

### **Phase 2 (Months 4-9): Neighborhood Network Effects** 🚧 PLANNED

**Goal:** Unlock community discovery, prove retention

**New Features:**
1. 🚧 **Neighborhood Discovery**
   - Map view of nearby GatherGrove users
   - Advanced filtering (kids' ages, interests, distance)
   - Anonymized until connection request accepted
   
2. 🚧 **Group Management**
   - Create custom groups (soccer team, book club, etc.)
   - One-tap invite entire group to events
   - Group chat (event-specific only)
   
3. 🚧 **Post-Event Capture**
   - Photo upload (direct or Google Photos link)
   - Automatic attendee list preservation
   - Memory card auto-generation
   - "Host Again" button
   
4. 🚧 **Babysitting Feature**
   - Nested in "Help & Favors" event category
   - Profile opt-in checkbox
   - Discovery filter in People tab
   - Trust/Safety: Verified profiles (premium)
   
5. 🚧 **Enhanced Messaging**
   - In-app event threads (not open DMs)
   - "Text Host" button (opens native SMS)
   - Push notifications for event updates
   
6. 🚧 **Calendar Intelligence**
   - Import availability from Google/iCal
   - "Find a Date" scheduling tool (Doodle-style)
   - Suggest optimal event times

**Success Metrics:**
- 60%+ of users with 5+ neighborhood connections
- 50%+ of events have post-event photos uploaded
- 65%+ 6-month retention

---

### **Phase 3 (Months 10-18): Stickiness & Monetization** 📋 FUTURE

**Goal:** Build the moat, prove revenue model

**New Features:**
1. 📋 **Memory Timeline**
   - Free users: last 12 months
   - Premium: unlimited access
   - Searchable event history
   - Anniversary reminders ("Your BBQ was 1 year ago today!")
   - Export photo albums
   
2. 📋 **Premium Features** ($7.99/month or $79/year)
   - Unlimited event history access
   - Advanced analytics (RSVP trends, popular times)
   - Custom branding (for power users/businesses)
   - Priority support
   
3. 📋 **Discovery Delight**
   - "Neighbor Roulette" (random intro to compatible neighbor)
   - "Neighbor of the Week" spotlight (opt-in)
   - Suggested meetups (AI-powered based on availability)
   
4. 📋 **Business Integrations**
   - OpenTable reservations (affiliate revenue)
   - Venmo/Cash App links (potluck reimbursements)
   - Local venue partnerships (sponsored event suggestions)
   
5. 📋 **Recurring Events**
   - Weekly playdate, monthly dinner series
   - Auto-RSVP for regulars
   - Attendance tracking over time

**Success Metrics:**
- 8-12% premium conversion rate
- $8-12 LTV/CAC ratio
- $500K+ MRR (monthly recurring revenue)

---

### **Phase 4 (Year 2+): Scale & Expansion** 🔮 VISION

**Goal:** Become default platform for IRL gatherings

**Future Features:**
1. 🔮 **B2B White-Label** (HOAs, schools, companies pay for custom instances)
2. 🔮 **International Expansion** (UK, Canada, Australia)
3. 🔮 **Creator Tools** (influencers/local organizers host public events)
4. 🔮 **AI Event Assistant** ("Plan a kid-friendly dinner for 6 families next week")
5. 🔮 **Reputation System** (verified neighbors, trusted hosts)

**Current Focus:** We're in **Phase 1** (MVP). All development effort is laser-focused on proving the viral loop works. Features outside Phase 1 scope are explicitly deferred.

---

## 🎯 Strategic Decisions

### Decision 1: Keep "Happening Now" vs. "Future Events"?
**Answer:** ✅ YES, but merge into single feed with status indicators

**Rationale:**
- "Happening Now" is a killer differentiator (Partiful doesn't have this)
- But separate tabs create cognitive load
- **Solution:** Single chronological feed with visual badges:
  - 🔴 "Live Now" (pulsing red badge, top priority)
  - 🟢 "This Weekend"
  - 🔵 "Next Week"
  - ⚪ "Future"

---

### Decision 2: In-App Messaging vs. SMS?
**Answer:** ✅ HYBRID — Event-specific in-app + SMS fallback

**The Model:**
1. **For Invitations:** Always SMS/Email first (reaches non-users instantly)
2. **For Event Coordination:** In-app messaging (keeps conversation contextualized)
3. **For Direct Neighbor Intros:** In-app only initially (prevents spam)

**Why This Works:**
- Low friction (don't force app for basic RSVP)
- High value (in-app messaging for event logistics is actually useful)
- Respectful (no unsolicited neighbor texts)

---

### Decision 3: Individual vs. Household Sign-Up?
**Answer:** ✅ INDIVIDUAL accounts, with optional household linking

**Rationale:**
- Household-first model was too rigid
- Reality: Spouses have different social preferences, event interests
- But household context is VERY useful for filtering

**The Model:**
1. Primary: Everyone signs up as individual
2. Optional: Link to household (spouse, kids)
3. Smart Filtering: When inviting, can choose:
   - "Invite Sarah" (individual)
   - "Invite Sarah's household" (includes spouse)
   - "Invite all families with kids 4-6" (household-aware)

---

### Decision 4: How to Avoid "Social Media" Feel?
**Answer:** ✅ Intentional constraints in design & features

**The Design Language:**
- **Typography:** Friendly sans-serif (like Airbnb, not corporate)
- **Illustrations:** Hand-drawn style for empty states (less pressure than photos)
- **Colors:** Nature-inspired palette (forest green, golden hour yellow, sky blue)
- **Motion:** Gentle, purposeful (confetti on RSVP yes, subtle pulse on "Live Now")
- **Copy:** Warm, human, never corporate ("Let's gather!" not "Create engagement")

---

### Decision 5: Neighborhood Codes (HOA/Verification)?
**Answer:** ✅ NO forced codes, opt-in neighborhood discovery

**The Flow:**
1. **At Signup:** User provides address (for proximity, not verification)
2. **Initial State:** Can create events, invite anyone (no restrictions)
3. **After 2-3 Events:** Prompt appears: "Discover who else nearby uses GatherGrove"
4. **Neighborhood Unlock:** See anonymized map, filter, send connection requests

**For HOAs (Optional Premium Feature):**
- HOA admins can create "verified neighborhoods"
- Members get badge: "✓ Oak Ridge HOA"
- This becomes a B2B upsell ($500-2K/year per HOA)

**Why This Works:**
- Zero friction at signup
- Organic discovery (people opt in when ready)
- Premium path for organized communities

---

### Decision 6: Kids' Privacy & Representation?
**Answer:** ✅ Age ranges only, no names/photos of minors

**The Model:**
1. **Profile Setup:** Parents indicate kids' ages (not names)
   - "I have kids ages: 6, 9"
   - System converts to ranges: "Ages 5-7, 8-10"
2. **Filtering:** Other parents can search:
   - "Families with kids ages 4-6"
   - Results show: "Sarah (2 kids: ages 4-6)"
   - **NO names, photos, or identifying info of children**
3. **Event Invitations:** Parents represent their household
   - Event shows: "Sarah + household" or "Sarah (family of 4)"
   - Kids attend with parents, never independently listed

**Why This Matters:**
- Protects minors from public exposure
- Still enables core use case (finding age-appropriate playmates)
- Complies with COPPA (Children's Online Privacy Protection Act)

---

## �🔒 Authentication & Authorization

### Development Mode

**Enabled when**:
- `ALLOW_DEV_AUTH=1`
- `SKIP_FIREBASE_INIT=1`
- `SKIP_FIREBASE=1` (legacy)
- `CI=true`

**Header-Based Auth**:
```bash
-H "X-Uid: brian"
-H "X-Email: brian@example.com"
-H "X-Admin: false"  # or "true"
```

**Behavior**:
- No Firebase Admin SDK initialization
- In-memory fake Firestore database
- Headers optional (defaults to safe dev identity)
- Fast startup, no cloud dependencies

### Production Mode

**Firebase ID Token Required**:
```bash
-H "Authorization: Bearer <firebase_id_token>"
```

**Token Verification**:
1. Extract token from `Authorization: Bearer` header
2. Verify with `firebase_admin.auth.verify_id_token()`
3. Extract claims: `uid`, `email`, `admin`
4. Return 401 for invalid/expired tokens

**Admin Access**:
- `isAdmin` field on user document is **informational only**
- Real admin status from token custom claim: `{ "admin": true }`
- Set via Firebase Admin SDK or Functions
- Prevents privilege escalation attacks

**Access Control Patterns**:
```python
# Owner-only
if claims["uid"] != target_uid:
    raise HTTPException(status_code=403)

# Owner or admin
if claims["uid"] != target_uid and not claims.get("admin"):
    raise HTTPException(status_code=403)

# Host-only (events)
if event["hostUid"] != claims["uid"] and not claims.get("admin"):
    raise HTTPException(status_code=403)
```

---

## 🛠️ Development

### Environment Variables

| Variable | Values | Description |
|----------|--------|-------------|
| `ALLOW_DEV_AUTH` | `"1"` | Enable dev header auth |
| `SKIP_FIREBASE_INIT` | `"1"` | Skip Firebase Admin init |
| `SKIP_FIREBASE` | `"1"` | Legacy skip Firebase flag |
| `CI` | `"true"` | CI environment indicator |
| `GOOGLE_APPLICATION_CREDENTIALS` | `path` | Firebase credentials JSON |
| `FIREBASE_CRED_PATH` | `path` | Alternative cred path |
| `CORS_ORIGIN` | `url` | Single extra CORS origin |
| `CORS_EXTRA_ORIGINS` | `url,url` | Comma-separated CORS origins |
| `DEV_UID` | `string` | Default dev user ID |
| `DEV_EMAIL` | `string` | Default dev email |
| `DEV_ADMIN` | `"true"/"false"` | Default dev admin status |

### Firebase Setup (Production)

1. **Create Firebase Project**: https://console.firebase.google.com
2. **Download Service Account Key**:
   - Project Settings → Service Accounts
   - Generate New Private Key
   - Save to `secrets/gathergrove-dev-firebase-adminsdk.json`
3. **Set Environment Variable**:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/secrets/gathergrove-dev-firebase-adminsdk.json"
   ```
4. **Create Firestore Database**:
   - Enable Firestore in Firebase Console
   - Set security rules (see `docs/security-rules.firestore` if available)

### CORS Configuration

**Default Allowed Origins**:
```python
[
  "http://localhost:3000",   # React dev server
  "http://127.0.0.1:3000",
  "http://localhost:5173",   # Vite dev server
  "http://127.0.0.1:5173"
]
```

**Add Extra Origins**:
```bash
# Single origin
export CORS_ORIGIN="http://192.168.1.100:5173"

# Multiple origins
export CORS_EXTRA_ORIGINS="http://192.168.1.100:5173,https://myapp.com"
```

### Helper Scripts

**`scripts/dev.sh`**: Start dev server with dev mode enabled
```bash
#!/usr/bin/env bash
set -euo pipefail
export ALLOW_DEV_AUTH=1
export SKIP_FIREBASE_INIT=1
export CI=true
python -m uvicorn app.main:app --port 8000 --reload
```

**`scripts/validate_events.sh`**: Validate event data (if implemented)

### Code Style & Linting

**Tools in `requirements.txt`**:
- `black`: Code formatter
- `ruff`: Fast linter
- `mypy` (implied): Type checking

**Run Formatter**:
```bash
black app/ tests/
```

**Run Linter**:
```bash
ruff check app/ tests/
```

---

## 🧪 Testing

### Test Structure

```
tests/
├── conftest.py              # Fixtures, dev mode setup
├── test_events.py           # Event CRUD, RSVPs, pagination
├── test_users.py            # User CRUD, admin checks
├── test_users_favorites.py  # Favorites operations
├── test_households.py       # Household listing, filters
├── test_people.py           # People API basic tests
├── test_people_pagination.py  # Pagination edge cases
├── test_people_filters_extra.py  # Age filters, search
└── test_favorites.py        # Additional favorites tests
```

### Running Tests

**All Tests**:
```bash
pytest
pytest -v  # Verbose
pytest -q  # Quiet
```

**Specific Test Files**:
```bash
pytest tests/test_events.py
pytest tests/test_users.py -v
```

**By Keyword**:
```bash
pytest -k "test_rsvp"
pytest -k "users or events"
pytest -k "not pagination"
```

**With Coverage**:
```bash
pytest --cov=app --cov-report=html
pytest --cov=app --cov-report=term-missing
```

**Coverage Report Location**: `htmlcov/index.html`

### Test Configuration

**`pytest.ini`**:
```ini
[pytest]
pythonpath = .
testpaths = tests
filterwarnings =
    ignore:The `dict` method is deprecated:DeprecationWarning
```

### Test Fixtures

**`conftest.py` provides**:
- `client`: TestClient with non-admin default identity
- `set_claims(uid, email, admin)`: Change authenticated user
- `seed_households()`: Populate test household data

**Example Test**:
```python
def test_create_event(client, set_claims):
    set_claims(uid="host1", admin=False)
    resp = client.post("/events", json={
        "type": "future",
        "title": "Test Event",
        "startAt": "2025-12-30T18:00:00Z",
        "neighborhoods": ["Bay Hill"]
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Test Event"
    assert data["hostUid"] == "host1"
```

### CI/CD Pipeline

**GitHub Actions** (`.github/workflows/tests.yml`):
- **Triggers**: Push to `main`, PRs to `main`
- **Matrix**: Python 3.12 (required) & 3.13 (allowed to fail)
- **Steps**:
  1. Checkout code
  2. Setup Python with pip cache
  3. Install dependencies + pytest
  4. Run tests with coverage
  5. Upload coverage to Codecov (Python 3.12 only)

**Environment**:
```yaml
env:
  SKIP_FIREBASE_INIT: "1"
  ALLOW_DEV_AUTH: "1"
  USE_FAKE_DB: "1"
  PYTHONPATH: "."
  PYTHONDONTWRITEBYTECODE: "1"
```

---

## 🚢 Deployment

### Production Checklist

**1. Environment Configuration**
- [ ] Set `GOOGLE_APPLICATION_CREDENTIALS` to service account key path
- [ ] Remove or set to `"0"`: `ALLOW_DEV_AUTH`, `SKIP_FIREBASE_INIT`
- [ ] Configure production CORS origins
- [ ] Set secure secrets management (e.g., AWS Secrets Manager, GCP Secret Manager)

**2. Database Setup**
- [ ] Create production Firestore database
- [ ] Deploy Firestore security rules
- [ ] Set up Firestore indexes (if needed for complex queries)
- [ ] Configure backups

**3. Authentication**
- [ ] Configure Firebase Authentication providers
- [ ] Set custom claims for admin users:
  ```python
  from firebase_admin import auth
  auth.set_custom_user_claims(uid, {"admin": True})
  ```

**4. Application Deployment**
- [ ] Deploy to production environment (Cloud Run, ECS, Kubernetes, etc.)
- [ ] Configure health check endpoint: `/health`
- [ ] Set up logging and monitoring
- [ ] Configure auto-scaling

**5. Security**
- [ ] Enable HTTPS only
- [ ] Set up rate limiting (e.g., nginx, API gateway)
- [ ] Configure Firebase App Check (optional)
- [ ] Review and test authentication flows
- [ ] Audit admin user access

### Deployment Targets

**Google Cloud Run** (recommended):
```bash
gcloud run deploy gathergrove-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_APPLICATION_CREDENTIALS=/app/secrets/firebase.json
```

**Docker**:
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
COPY secrets/ ./secrets/
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/secrets/firebase.json
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**AWS ECS/Fargate**: Deploy via CloudFormation or Terraform with task definition pointing to ECR image

### Monitoring

**Health Endpoints**:
- `GET /health` → `{"status": "ok"}`
- `GET /firebase` → Validates Firestore connection

**Recommended Metrics**:
- Request rate, latency (p50, p95, p99)
- Error rate (4xx, 5xx)
- Firebase Admin SDK latency
- Active connections
- Memory/CPU usage

**Logging**:
- Application logs: `uvicorn` outputs to stdout
- Firestore operations: Firebase Admin SDK logs
- Authentication failures: Custom logging in `auth.py`

---

## 👥 Contributing

### Development Workflow

1. **Fork & Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/gathergrove-backend.git
   cd gathergrove-backend
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Changes**
   - Write code following existing patterns
   - Add/update tests for new functionality
   - Update documentation as needed

4. **Run Tests**
   ```bash
   pytest
   black app/ tests/
   ruff check app/ tests/
   ```

5. **Commit & Push**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   git push origin feature/your-feature-name
   ```

6. **Open Pull Request**
   - Target: `main` branch
   - Include: Description, testing notes, breaking changes (if any)
   - Wait for CI to pass

### Coding Standards

**Style**:
- Use `black` for formatting (line length 100)
- Follow PEP 8 naming conventions
- Type hints encouraged (but not enforced everywhere)

**Strategic Constraints (Must Follow):**
- **Events-First**: Every feature must serve event creation/attendance/memory
- **No Social Media Patterns**: No feeds, likes, follower counts, or algorithmic sorting
- **Privacy-First**: Opt-in everything, approximate distances, age ranges only for kids
- **Viral by Design**: Every user-facing page should have "Created with GatherGrove" footer
- **Time-Bound Content**: Events expire naturally (no perpetual content)
- **North Star Test**: "Does this help people get offline and see each other?" If NO → Don't build

**The One Metric That Matters:**
All code changes should ultimately drive: **% of RSVP recipients who create their own event**

**Architecture Patterns**:
- **Routes**: Thin handlers, delegate to helper functions
- **Models**: Pydantic for request/response validation
- **Auth**: Always use `Depends(verify_token)` for authenticated routes
- **Database**: Use `db.collection(...).document(...).set/get/update` patterns
- **Timestamps**: Always UTC via `datetime.now(timezone.utc)`
- **Errors**: Use FastAPI `HTTPException` with appropriate status codes

**Git Commit Messages**:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions/updates
- `refactor:` Code refactoring
- `chore:` Maintenance tasks

### Key Files to Review

When modifying functionality, check these files:
- `app/main.py`: Route registration, CORS
- `app/deps/auth.py`: Authentication logic
- `app/core/firebase.py`: Database initialization
- `docs/schema.md`: Firestore schema documentation
- `tests/conftest.py`: Test fixtures and setup

---

## 📝 Additional Documentation

### **Strategy & Vision**
- **[🌿 Product Strategy 2025](docs/strategy-2025.md)** - Complete strategic vision (30+ pages) *(To be created)*
- **[🎯 The One Metric](docs/one-metric.md)** - Why 30% RSVP→Creator conversion defines success *(To be created)*
- **[🍼 Babysitting Feature](docs/babysitting-feature.md)** - Strategic force multiplier guide *(To be created)*
- **[🚫 What We DON'T Build](docs/anti-patterns.md)** - Avoiding "social media" drift *(To be created)*

### **Technical Documentation**
- **Firestore Schema**: See `docs/schema.md` for complete data model documentation
- **OpenAPI Spec**: Auto-generated at `/openapi.json` or http://127.0.0.1:8000/openapi.json
- **API Docs**: Interactive Swagger UI at `/docs`

### **Architecture Evolution**
- **[📋 Executive Summary](docs/summary.md)** - Extensibility proposal overview
- **[📖 Full Proposal](docs/extensibility-proposal.md)** - Complete technical proposal (30 pages)
- **[🏗️ Architecture Diagrams](docs/architecture-diagram.md)** - Visual comparison of current vs. future state
- **[✅ Phase 1 Implementation Guide](docs/phase1-implementation-checklist.md)** - Step-by-step checklist
- **[🔌 API Examples](docs/api-examples-new-features.md)** - Real-world examples (smart targeting, AI images, public events)
- **[🤔 Review Guide](docs/review-guide.md)** - Key questions for stakeholder review

---

## 🐛 Known Issues & Limitations

- **Pagination**: Cursor tokens are opaque base64 strings (not human-readable)
- **Real-time Updates**: Not supported (requires polling or webhooks)
- **File Uploads**: Not implemented (would need Cloud Storage integration)
- **Search**: Limited to prefix matching on last name (no full-text search)
- **Transactions**: Most operations are non-transactional (eventual consistency)

---

## 📄 License

See `LICENSE` file for details.

---

## 📧 Contact & Support

**Maintainer**: Brian Carlberg  
**Repository**: https://github.com/bcarls03/gathergrove-backend  
**Issues**: https://github.com/bcarls03/gathergrove-backend/issues

---

**Built with ❤️ for neighborhood communities**

*Last Updated: December 2025 | Version 0.1.0*
