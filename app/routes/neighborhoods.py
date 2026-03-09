# app/routes/neighborhoods.py
from fastapi import APIRouter, Query
from app.core.firebase import db

router = APIRouter(tags=["neighborhoods"])


def _normalize_for_grouping(text: str) -> str:
    """
    Normalize neighborhood name for grouping/matching only.
    Used to aggregate similar variants (e.g., "Bay Hill" and "Bayhill").
    Does NOT mutate stored data.
    """
    import re
    # lowercase, strip, collapse whitespace, remove spaces for grouping
    normalized = text.lower().strip()
    normalized = re.sub(r'\s+', ' ', normalized)  # collapse repeated spaces
    normalized = normalized.replace(' ', '')  # remove spaces for grouping key
    return normalized


@router.get("/neighborhoods/suggestions", summary="Get neighborhood suggestions")
def get_neighborhood_suggestions(
    prefix: str = Query(..., min_length=3, max_length=50),
    lat: float = Query(...),
    lng: float = Query(...),
):
    """
    Returns neighborhood suggestions based on nearby households.
    
    Minimal v1:
    - User must type 3+ characters
    - Returns neighborhoods from households within 5 miles
    - Returns name and count only (no distance display yet)
    - Silent graceful failure (returns empty array on error)
    - No auth required (returns only aggregate data, no identities)
    """
    try:
        # Normalize prefix for matching (handles spacing variations)
        prefix_normalized = _normalize_for_grouping(prefix)
        if len(prefix_normalized) < 3:
            return []
        
        # Collect matching neighborhoods with normalization
        coll = db.collection("households")
        # Track normalized key -> {original variants -> count}
        grouped_neighborhoods = {}
        
        for doc in coll.stream():
            data = doc.to_dict()
            if not data:
                continue
            
            neighborhood = data.get("neighborhood")
            h_lat = data.get("latitude")
            h_lng = data.get("longitude")
            
            # Skip if no neighborhood or coordinates
            if not neighborhood or h_lat is None or h_lng is None:
                continue
            
            # Normalize both prefix and neighborhood for matching (handles spacing)
            neighborhood_normalized = _normalize_for_grouping(neighborhood)
            if not neighborhood_normalized.startswith(prefix_normalized):
                continue
            
            # Calculate distance (simplified Haversine)
            distance_mi = _calculate_distance(lat, lng, h_lat, h_lng)
            
            # Only include nearby households (within 5 miles)
            if distance_mi <= 5.0:
                # Use normalized key for grouping
                norm_key = _normalize_for_grouping(neighborhood)
                if norm_key not in grouped_neighborhoods:
                    grouped_neighborhoods[norm_key] = {}
                if neighborhood not in grouped_neighborhoods[norm_key]:
                    grouped_neighborhoods[norm_key][neighborhood] = 0
                grouped_neighborhoods[norm_key][neighborhood] += 1
        
        # Aggregate counts and pick most common variant for each group
        final_neighborhoods = {}
        for norm_key, variants in grouped_neighborhoods.items():
            # Total count across all variants
            total_count = sum(variants.values())
            # Pick the most frequently used original variant as display name
            most_common_variant = max(variants.items(), key=lambda x: x[1])[0]
            final_neighborhoods[most_common_variant] = total_count
        
        # Sort by count descending, limit to 3
        suggestions = [
            {"name": name, "count": count}
            for name, count in sorted(
                final_neighborhoods.items(),
                key=lambda x: -x[1]
            )[:3]
        ]
        
        return suggestions
    
    except Exception as e:
        # Silent graceful failure
        print(f"[WARN] Neighborhood suggestions error: {e}")
        return []


def _calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance in miles using Haversine formula."""
    from math import radians, sin, cos, sqrt, atan2
    
    R = 3958.8  # Earth radius in miles
    
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lng = radians(lng2 - lng1)
    
    a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lng / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    return R * c
