#!/bin/bash
# Seed households via API for in-memory Firestore

echo "🌱 Seeding households via API..."

# Function to create household
create_household() {
  curl -s -X POST http://localhost:8000/households \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer fake-dev-token" \
    -d "$1" > /dev/null && echo "  ✓ Created $2"
}

# Family with kids 1
create_household '{
  "name": "Miller Family",
  "householdType": "family_with_kids",
  "address": "123 Oak Ridge Dr",
  "neighborhood": "Oak Ridge",
  "location_precision": "street",
  "latitude": 45.5152,
  "longitude": -122.6784,
  "bio": "Family with kids who love outdoor activities",
  "kids": [{"name": "Emma", "birthYear": 2018, "birthMonth": 5}]
}' "Miller Family"

# Family with kids 2
create_household '{
  "name": "Johnson Family",
  "householdType": "family_with_kids",
  "address": "456 Oak Ridge Ln",
  "neighborhood": "Oak Ridge",
  "location_precision": "street",
  "latitude": 45.5162,
  "longitude": -122.6794,
  "bio": "Active family with two kids",
  "kids": [{"name": "Liam", "birthYear": 2016, "birthMonth": 8}, {"name": "Sophia", "birthYear": 2019, "birthMonth": 3}]
}' "Johnson Family"

# Family with kids 3
create_household '{
  "name": "Garcia Family",
  "householdType": "family_with_kids",
  "address": "789 Riverside Ave",
  "neighborhood": "Riverside",
  "location_precision": "street",
  "latitude": 45.5142,
  "longitude": -122.6804,
  "bio": "Family loves playing at the park",
  "kids": [{"name": "Noah", "birthYear": 2017, "birthMonth": 11}]
}' "Garcia Family"

# Couple 1
create_household '{
  "name": "Taylor & Morgan",
  "householdType": "couple",
  "address": "321 Riverside Blvd",
  "neighborhood": "Riverside",
  "location_precision": "street",
  "latitude": 45.5132,
  "longitude": -122.6814,
  "bio": "Young couple, no kids yet"
}' "Taylor Couple"

# Single
create_household '{
  "name": "Alex Brown",
  "householdType": "single",
  "address": "654 Hillside Way",
  "neighborhood": "Hillside",
  "location_precision": "street",
  "latitude": 45.5172,
  "longitude": -122.6764,
  "bio": "Single professional, dog lover"
}' "Alex Brown"

echo ""
echo "✅ Done! Check http://localhost:5173/discovery"
