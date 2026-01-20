# 🚀 GatherGrove Extensibility Plan

**Current State:** ~25% complete (basic events + RSVPs working)  
**Timeline:** 13-15 weeks to full build  
**Updated:** December 28, 2025

---

## 🎯 The Plan

Transform GatherGrove into an **events-first platform** with 7 new features:

1. **AI-generated event images** (DALL-E 3)
2. **Smart invitations** (by neighborhood, radius, age, groups)
3. **Flexible groups** (HOAs, clubs, families, classrooms)
4. **Public shareable events** (no account needed to RSVP)
5. **Post-event photo albums** (Google Photos → bespoke)
6. **Gamification** (points, badges, leaderboards)
7. **Personalized recommendations** (ML-based)

---

## � Documentation (Read in Order)

1. **[extensibility-proposal.md](./extensibility-proposal.md)** ← **START HERE**
   - Complete technical spec (30 pages)
   - All data models (10 new collections)
   - Gap analysis (what's missing)
   - Migration strategy (backward compatible)

2. **[phase1-implementation-checklist.md](./phase1-implementation-checklist.md)**
   - Step-by-step Phase 1 guide
   - Migration scripts
   - API code examples
   - Testing checklist

3. **[schema.md](./schema.md)**
   - Current Firestore schema (reference only)

---

## ⚡ Quick Reference

### What Works Today
- ✅ Basic events (CRUD, RSVPs, capacity)
- ✅ Households (1:1 with users)
- ✅ Neighborhood filtering
- ✅ Push notifications

### What's Missing
- ⚠️ Smart invitations (0%)
- ⚠️ AI images (0%)
- ⚠️ Public sharing (0%)
- ⚠️ Flexible groups (20%)
- ⚠️ Photo albums (0%)
- ⚠️ Gamification (0%)
- ⚠️ Recommendations (0%)

### Implementation Timeline

| Phase | Weeks | Key Deliverables |
|-------|-------|------------------|
| **1: Foundation** | 1-2 | New collections (`people`, `groups`, `event_invites`) |
| **2: Enhanced Events** | 3-4 | AI images, public pages, Google Photos |
| **3: Smart Invitations** | 5-6 | Criteria engine, geospatial matching |
| **3A: Gamification** | 7-8 | Points, badges, stats page |
| **4: Groups API** | 9-10 | Multi-group membership, leaderboards |
| **4B: Recommendations** | 11-12 | ML event/group suggestions |
| **5: Advanced** | 13+ | Bespoke photos, optimization |

### Cost Estimate
- **Today:** $0/month (free tier)
- **At scale:** $60-200/month (mostly DALL-E 3 images)

---

## 🚦 Next Steps

**Ready to start?**
1. Read [extensibility-proposal.md](./extensibility-proposal.md) (1 hour)
2. Review Phase 1 in [phase1-implementation-checklist.md](./phase1-implementation-checklist.md) (15 min)
3. Begin Phase 1: Create new Firestore collections

**Need to discuss?**
- Timeline: Full 15 weeks or prioritize certain phases?
- Photos: Google Photos (fast) or bespoke (better UX)?
- Gamification: Phase 3A or defer?

---

**All 6 of your use cases are supported. Let's build! 🚀**
