# Teaching Feedback Support System — User Guide (English)

This guide is written for first-time users. It explains exactly what to click and what to paste, without revealing any local file paths.

---

## 1) Start the System

### 1.1 Prerequisites

- Python 3.8+
- Required Python packages installed (see `requirements.txt` if provided)

### 1.2 Start the backend server

1. Open a terminal (Windows Terminal / PowerShell / VS Code Terminal).
2. Set your current folder to the **project folder** (the folder that contains `app.py`).
3. Run:

```bash
python app.py
```

4. Keep this terminal window open.

**Success sign:** the terminal shows something like:

```text
Running on http://127.0.0.1:5000
```

---

## 2) Open the Web App

Open your browser and visit:

- **Home:** `http://127.0.0.1:5000/`
- **Teacher portal:** `http://127.0.0.1:5000/teacher`
- **Student portal:** `http://127.0.0.1:5000/student`

---

## 3) Initialize Demo Data (Recommended for Testing)

This creates a ready-to-use demo dataset: users, assignments, rubrics, and sample submissions.

### Option A (easiest): use browser Console

1. Open `http://127.0.0.1:5000/`.
2. Press `F12` to open Developer Tools.
3. Click the **Console** tab.
4. Paste the following line and press Enter:

```js
fetch('/api/demo/init', { method: 'POST' }).then(r => r.json()).then(console.log)
```

**Success sign:** you see a JSON response indicating demo data was initialized.

### Option B: use a REST client (curl)

```bash
curl -X POST http://127.0.0.1:5000/api/demo/init
```

---

## 4) Teacher Workflow (Step-by-step)

### Goal

A teacher opens a pending submission, uses AI tools to assist grading, writes feedback, and submits it.

### 4.1 Enter the Teacher Portal

1. Go to: `http://127.0.0.1:5000/teacher`
2. You will see the teacher dashboard.

### 4.2 Open a submission to grade

1. In the left sidebar, click **Pending**.
2. Find any submission card.
3. Click the submission card to open the grading page.

### 4.3 Review the student work

On the grading page:

- The **left panel** shows the student’s submission text.
- The **right panel** contains rubric scoring + feedback tools.

### 4.4 (Optional) Use AI to analyze the student work

1. In the tool buttons area, click **Analyze Work**.
2. Wait a few seconds.

What you should see:

- Word/sentence/paragraph counts
- Structure checks (Title / Introduction / Conclusion)
- Quality indicators (length, structure, vocabulary diversity)

### 4.5 (Optional) Use AI to suggest rubric scores

1. Click **Suggest Scores**.
2. Wait a few seconds.
3. You will see suggested levels for each rubric criterion.

To apply:

- Click **Apply** for one criterion, or
- Click **Apply All Suggestions** to apply all at once.

### 4.6 Set rubric scores manually (if you prefer)

1. In the **Rubric Scoring** section, each criterion has multiple score buttons.
2. Click one option (it becomes highlighted).
3. Repeat for all criteria.

### 4.7 Write the teacher’s feedback

1. Find the **Written Feedback** text box.
2. Type or paste your feedback.

Example feedback you can paste:

```text
Strengths:
- Clear structure and easy-to-follow argument.
- Good use of topic sentences.

Areas to improve:
- Add specific evidence (examples, data, quotes) to support key claims.
- Expand the section that discusses limitations/challenges.

Next steps:
- Include 2–3 concrete examples.
- Improve paragraph transitions for smoother flow.
```

### 4.8 (Optional) Check feedback quality with AI tools

After you have written feedback, you can click:

- **Alignment Check**
  - Checks how well your feedback covers the rubric criteria.

- **Detailed Analysis**
  - Shows criterion coverage details + keyword matches + quality markers.

- **Quality Analysis**
  - Gives quick scoring on specificity, feedforward, and tone.

- **AI Optimize**
  - Generates a rewritten feedback draft.
  - If you like it, click **Apply This Feedback**.

### 4.9 Submit feedback

1. Confirm rubric scores are selected.
2. Confirm the feedback text box is not empty.
3. Click **Submit Feedback**.

**Success sign:** a success notification appears and the submission moves from Pending to Graded.

---

## 5) Student Workflow (Step-by-step)

### Goal

A student submits new work and later views the teacher’s feedback.

### 5.1 Enter the Student Portal

1. Go to: `http://127.0.0.1:5000/student`

### 5.2 Select a student

1. At the top of the page, find the **student selector** drop-down.
2. Select a student (e.g., a demo student).
3. The page updates the student name and list of submissions.

### 5.3 Submit a new assignment

1. Scroll to the section **Submit New Assignment**.
2. In **Select Assignment**, choose one assignment.
3. In the text area, paste your submission.

Example student submission you can paste:

```text
The Future of Artificial Intelligence

Artificial intelligence is rapidly changing our world. From virtual assistants to self-driving cars, AI is becoming part of daily life.

One major benefit is efficiency: AI can process large datasets quickly and help people make better decisions. In healthcare, AI can support early detection by analyzing medical images.

However, AI also raises concerns about job displacement and fairness. Society should invest in education and retraining, and ensure AI systems are transparent and accountable.

In conclusion, AI offers both opportunities and challenges. We should guide its development to benefit everyone.
```

4. Click **Submit Assignment**.

**Success sign:** a success notification appears, and the submission shows up as **Pending**.

### 5.4 View feedback (after grading)

1. In the submissions list, find a submission labeled **Graded**.
2. Click **View Feedback**.
3. A modal opens and shows:

- Visual summary (strengths, improvements)
- Rubric score breakdown
- Written teacher feedback
- (Optional) Video script

### 5.5 Close the feedback modal

Click the **X** button in the top-right of the modal.

---

## 6) Troubleshooting

### 6.1 The page is blank / cannot load

- Make sure the server is still running in the terminal.
- Refresh the page.
- Re-run demo initialization:

```js
fetch('/api/demo/init', { method: 'POST' })
```

### 6.2 AI tools do not respond

- Wait 10–15 seconds; AI calls may take time.
- Check the terminal output for error messages.
- Verify network access if you use an external AI provider.

### 6.3 “Port already in use”

- Another process is using port 5000.
- Stop the other process, or change the port in `app.py`.

---

## 7) Quick Links

- Home: `http://127.0.0.1:5000/`
- Teacher: `http://127.0.0.1:5000/teacher`
- Student: `http://127.0.0.1:5000/student`
