#!/bin/bash
# C1-1 API测试脚本

BASE_URL="http://localhost:5000"

echo "=== C1-1 API测试 ==="
echo ""

echo "1. 测试有效spec示例1：Data Science基础spec"
curl -s -X POST $BASE_URL/api/cscl/spec/validate \
  -H "Content-Type: application/json" \
  -d '{
    "course_context": {
      "subject": "Data Science",
      "topic": "Machine Learning",
      "class_size": 30,
      "mode": "sync",
      "duration": 90
    },
    "learning_objectives": {
      "knowledge": ["Understand ML basics"],
      "skills": ["Apply algorithms"]
    },
    "task_requirements": {
      "task_type": "debate",
      "expected_output": "argument",
      "collaboration_form": "group"
    }
  }' | python3 -m json.tool
echo ""

echo "2. 测试有效spec示例2：Learning Sciences完整spec"
curl -s -X POST $BASE_URL/api/cscl/spec/validate \
  -H "Content-Type: application/json" \
  -d '{
    "course_context": {
      "subject": "Learning Sciences",
      "topic": "Collaborative Learning",
      "class_size": 25,
      "mode": "async",
      "duration": 120
    },
    "learning_objectives": {
      "knowledge": ["Understand collaboration principles"],
      "skills": ["Facilitate group discussions"],
      "disposition": ["Value diverse perspectives"]
    },
    "task_requirements": {
      "task_type": "collaborative_writing",
      "expected_output": "group essay",
      "collaboration_form": "pair"
    },
    "constraints": {
      "tools": ["Google Docs", "Zoom"],
      "timebox": 60
    },
    "rubric_preferences": {
      "criteria": ["Clarity", "Evidence"],
      "emphasis": "Focus on evidence quality"
    }
  }' | python3 -m json.tool
echo ""

echo "3. 测试有效spec示例3：Humanities spec"
curl -s -X POST $BASE_URL/api/cscl/spec/validate \
  -H "Content-Type: application/json" \
  -d '{
    "course_context": {
      "subject": "Humanities",
      "topic": "Literary Analysis",
      "class_size": 20,
      "mode": "sync",
      "duration": 60
    },
    "learning_objectives": {
      "knowledge": ["Understand literary devices"],
      "skills": ["Analyze texts", "Write critiques"]
    },
    "task_requirements": {
      "task_type": "peer_review",
      "expected_output": "peer feedback",
      "collaboration_form": "pair"
    }
  }' | python3 -m json.tool
echo ""

echo "4. 测试无效spec示例1：缺失course_context"
curl -s -X POST $BASE_URL/api/cscl/spec/validate \
  -H "Content-Type: application/json" \
  -d '{
    "learning_objectives": {
      "knowledge": ["Understand ML basics"],
      "skills": ["Apply algorithms"]
    },
    "task_requirements": {
      "task_type": "debate",
      "expected_output": "argument",
      "collaboration_form": "group"
    }
  }' | python3 -m json.tool
echo ""

echo "5. 测试无效spec示例2：空字段"
curl -s -X POST $BASE_URL/api/cscl/spec/validate \
  -H "Content-Type: application/json" \
  -d '{
    "course_context": {
      "subject": "",
      "topic": "Machine Learning",
      "class_size": 30,
      "mode": "sync",
      "duration": 90
    },
    "learning_objectives": {
      "knowledge": [],
      "skills": ["Apply algorithms"]
    },
    "task_requirements": {
      "task_type": "debate",
      "expected_output": "argument",
      "collaboration_form": "group"
    }
  }' | python3 -m json.tool
echo ""

echo "6. 测试无效spec示例3：无效mode值"
curl -s -X POST $BASE_URL/api/cscl/spec/validate \
  -H "Content-Type: application/json" \
  -d '{
    "course_context": {
      "subject": "Data Science",
      "topic": "Machine Learning",
      "class_size": 30,
      "mode": "invalid_mode",
      "duration": 90
    },
    "learning_objectives": {
      "knowledge": ["Understand ML basics"],
      "skills": ["Apply algorithms"]
    },
    "task_requirements": {
      "task_type": "debate",
      "expected_output": "argument",
      "collaboration_form": "group"
    }
  }' | python3 -m json.tool
echo ""

echo "=== 测试完成 ==="
