#!/bin/bash
# Quick curl tests for auth/RBAC (requires running server)

BASE_URL="http://localhost:5001"

echo "=== Test 1: Unauthorized (401) ==="
curl -s -X PUT "$BASE_URL/api/submissions/SUB001/feedback" \
  -H "Content-Type: application/json" \
  -d '{"feedback": "Test", "rubric_scores": {}}' \
  -w "\nHTTP Status: %{http_code}\n" | head -5

echo -e "\n=== Test 2: Login Success ==="
curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "T001", "password": "teacher123"}' \
  -c /tmp/cookies.txt \
  -w "\nHTTP Status: %{http_code}\n" | head -5

echo -e "\n=== Test 3: Authorized (200) ==="
curl -s -X PUT "$BASE_URL/api/submissions/SUB001/feedback" \
  -H "Content-Type: application/json" \
  -d '{"feedback": "Great work!", "rubric_scores": {}}' \
  -b /tmp/cookies.txt \
  -w "\nHTTP Status: %{http_code}\n" | head -5

echo -e "\n=== Test 4: Forbidden (403) - Student accessing teacher endpoint ==="
curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "S001", "password": "student123"}' \
  -c /tmp/cookies_student.txt

curl -s -X PUT "$BASE_URL/api/submissions/SUB001/feedback" \
  -H "Content-Type: application/json" \
  -d '{"feedback": "Test", "rubric_scores": {}}' \
  -b /tmp/cookies_student.txt \
  -w "\nHTTP Status: %{http_code}\n" | head -5

echo -e "\n=== Test 5: Health Check ==="
curl -s "$BASE_URL/api/health" | python3 -m json.tool | grep -E "(auth_mode|rbac_enabled|use_db_storage)"
