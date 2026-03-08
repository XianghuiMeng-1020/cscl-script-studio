#!/usr/bin/env python3
"""Generate 20 different demo syllabus files for load/upload testing."""
import os

OUTDIR = os.path.join(os.path.dirname(__file__), 'demo_files_20')
os.makedirs(OUTDIR, exist_ok=True)

TOPICS = [
    "Introduction to Data Science",
    "Collaborative Learning in STEM",
    "Ethics in AI",
    "Digital Literacy",
    "Climate Change and Society",
    "Public Health Basics",
    "Creative Writing Workshop",
    "Introduction to Psychology",
    "Sustainable Design",
    "Urban Planning",
    "Marine Biology",
    "Economics for Everyone",
    "History of Technology",
    "Philosophy of Mind",
    "Statistics for Research",
    "Multicultural Education",
    "Game Design Fundamentals",
    "Environmental Policy",
    "Human-Computer Interaction",
    "Critical Thinking and Argumentation",
]

def gen_content(i: int, topic: str) -> str:
    return f"""# Course Syllabus – Demo File {i+1}

## {topic}

This is a unique demo syllabus for load testing user {i+1}.
Course code: DEMO-{i+1:02d}
Topic: {topic}

## Learning objectives
- Understand core concepts of {topic.lower()}.
- Apply collaborative learning techniques in group tasks.
- Reflect on evidence and justify decisions.

## Assessment
- Participation: 20%
- Group project: 40%
- Final reflection: 40%

## Schedule (sample)
Week 1: Introduction and formation of groups.
Week 2–4: Thematic modules with peer feedback.
Week 5: Synthesis and presentation.

---
Generated for concurrent upload test. Minimum length for TEXT_TOO_SHORT validation.
"""

def main():
    for i, topic in enumerate(TOPICS):
        ext = '.md' if i % 2 == 0 else '.txt'
        path = os.path.join(OUTDIR, f'demo_syllabus_{i+1:02d}{ext}')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(gen_content(i, topic))
        print(path)
    print(f"Created {len(TOPICS)} files in {OUTDIR}")

if __name__ == "__main__":
    main()
