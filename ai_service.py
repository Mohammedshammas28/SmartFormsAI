"""
AI Service — SmartForms
Primary  : Google Gemini API (free tier, works everywhere after deployment)
Fallback : Smart Template Engine (pure Python, zero dependencies, always works)
"""

import json
import urllib.request
import urllib.error
from collections import Counter

# ─────────────────────────────────────────────
# Gemini REST API
# ─────────────────────────────────────────────

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash:generateContent"
)


def call_gemini(api_key: str, system_prompt: str, user_message: str) -> dict:
    """Call the Gemini API and return {'success': True, 'content': str} or error."""
    if not api_key:
        return {"success": False, "error": "no_key"}

    payload = json.dumps({
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": user_message}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2048
        }
    }).encode("utf-8")

    url = f"{GEMINI_API_URL}?key={api_key}"
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            print("[AI] Gemini API call succeeded.")
            return {"success": True, "content": text}

    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"[AI] Gemini HTTP error {e.code}: {body[:300]}")
        try:
            err_data = json.loads(body)
            msg = err_data.get("error", {}).get("message", "")
        except Exception:
            msg = body[:200]
        return {"success": False, "error": f"HTTP {e.code}: {msg}"}

    except Exception as e:
        print(f"[AI] Gemini connection error: {e}")
        return {"success": False, "error": str(e)}


# ─────────────────────────────────────────────
# Smart Template Engine — Form Generation
# ─────────────────────────────────────────────

_FORM_TEMPLATES = {
    "registration": {
        "keywords": ["registration", "register", "event", "conference", "seminar", "workshop", "signup", "sign up", "enroll"],
        "title_suffix": "Registration Form",
        "questions": [
            {"question_text": "Full Name", "question_type": "short_text", "is_required": True, "options": []},
            {"question_text": "Email Address", "question_type": "email", "is_required": True, "options": []},
            {"question_text": "Phone Number", "question_type": "phone", "is_required": False, "options": []},
            {"question_text": "Date of Event / Preferred Date", "question_type": "date", "is_required": True, "options": []},
            {"question_text": "Number of Attendees", "question_type": "multiple_choice", "is_required": True, "options": ["1", "2–5", "6–10", "More than 10"]},
            {"question_text": "Dietary Preferences / Special Requirements", "question_type": "long_text", "is_required": False, "options": []},
            {"question_text": "How did you hear about this event?", "question_type": "multiple_choice", "is_required": False, "options": ["Social Media", "Email", "Friend / Colleague", "Website", "Other"]},
            {"question_text": "Any additional comments or questions?", "question_type": "long_text", "is_required": False, "options": []},
        ]
    },
    "feedback": {
        "keywords": ["feedback", "survey", "review", "opinion", "satisfaction", "rating", "experience", "evaluate", "assessment"],
        "title_suffix": "Feedback Survey",
        "questions": [
            {"question_text": "Overall Satisfaction", "question_type": "rating", "is_required": True, "options": []},
            {"question_text": "How likely are you to recommend us to a friend or colleague?", "question_type": "rating", "is_required": True, "options": []},
            {"question_text": "What did you like most?", "question_type": "long_text", "is_required": False, "options": []},
            {"question_text": "What could we improve?", "question_type": "long_text", "is_required": False, "options": []},
            {"question_text": "How was the overall quality?", "question_type": "multiple_choice", "is_required": True, "options": ["Excellent", "Good", "Average", "Below Average", "Poor"]},
            {"question_text": "Would you use our service again?", "question_type": "yes_no", "is_required": True, "options": []},
            {"question_text": "Any other comments or suggestions?", "question_type": "long_text", "is_required": False, "options": []},
        ]
    },
    "job": {
        "keywords": ["job", "application", "apply", "hiring", "career", "employment", "vacancy", "position", "recruit", "resume", "cv"],
        "title_suffix": "Job Application",
        "questions": [
            {"question_text": "Full Name", "question_type": "short_text", "is_required": True, "options": []},
            {"question_text": "Email Address", "question_type": "email", "is_required": True, "options": []},
            {"question_text": "Phone Number", "question_type": "phone", "is_required": True, "options": []},
            {"question_text": "Position Applying For", "question_type": "short_text", "is_required": True, "options": []},
            {"question_text": "Years of Relevant Experience", "question_type": "multiple_choice", "is_required": True, "options": ["Less than 1 year", "1–3 years", "3–5 years", "5–10 years", "10+ years"]},
            {"question_text": "Highest Level of Education", "question_type": "multiple_choice", "is_required": True, "options": ["High School", "Bachelor's Degree", "Master's Degree", "PhD", "Other"]},
            {"question_text": "Key Skills (comma-separated)", "question_type": "long_text", "is_required": True, "options": []},
            {"question_text": "When can you start?", "question_type": "date", "is_required": False, "options": []},
            {"question_text": "Why are you interested in this position?", "question_type": "long_text", "is_required": True, "options": []},
        ]
    },
    "contact": {
        "keywords": ["contact", "inquiry", "enquiry", "message", "get in touch", "reach", "support", "help", "question"],
        "title_suffix": "Contact Form",
        "questions": [
            {"question_text": "Full Name", "question_type": "short_text", "is_required": True, "options": []},
            {"question_text": "Email Address", "question_type": "email", "is_required": True, "options": []},
            {"question_text": "Phone Number", "question_type": "phone", "is_required": False, "options": []},
            {"question_text": "Subject", "question_type": "short_text", "is_required": True, "options": []},
            {"question_text": "Type of Inquiry", "question_type": "multiple_choice", "is_required": True, "options": ["General Question", "Technical Support", "Billing", "Partnership", "Other"]},
            {"question_text": "Your Message", "question_type": "long_text", "is_required": True, "options": []},
            {"question_text": "Preferred contact method?", "question_type": "multiple_choice", "is_required": False, "options": ["Email", "Phone", "Either"]},
        ]
    },
    "order": {
        "keywords": ["order", "purchase", "buy", "product", "booking", "reservation", "shop", "request"],
        "title_suffix": "Order Form",
        "questions": [
            {"question_text": "Full Name", "question_type": "short_text", "is_required": True, "options": []},
            {"question_text": "Email Address", "question_type": "email", "is_required": True, "options": []},
            {"question_text": "Phone Number", "question_type": "phone", "is_required": True, "options": []},
            {"question_text": "Delivery Address", "question_type": "long_text", "is_required": True, "options": []},
            {"question_text": "Product / Service Requested", "question_type": "short_text", "is_required": True, "options": []},
            {"question_text": "Quantity", "question_type": "multiple_choice", "is_required": True, "options": ["1", "2–5", "6–10", "10+"]},
            {"question_text": "Special Instructions", "question_type": "long_text", "is_required": False, "options": []},
            {"question_text": "Preferred Delivery Date", "question_type": "date", "is_required": False, "options": []},
        ]
    },
    "quiz": {
        "keywords": ["quiz", "test", "exam", "assessment", "knowledge", "trivia", "questionnaire"],
        "title_suffix": "Quiz",
        "questions": [
            {"question_text": "Your Name", "question_type": "short_text", "is_required": True, "options": []},
            {"question_text": "Email Address", "question_type": "email", "is_required": True, "options": []},
            {"question_text": "Question 1: How familiar are you with this topic?", "question_type": "multiple_choice", "is_required": True, "options": ["Not at all", "Somewhat", "Moderately", "Very familiar", "Expert"]},
            {"question_text": "Question 2: Describe your experience with this subject", "question_type": "long_text", "is_required": True, "options": []},
            {"question_text": "Question 3: True or False — Continuous learning improves performance", "question_type": "yes_no", "is_required": True, "options": []},
            {"question_text": "How would you rate your confidence on this topic?", "question_type": "rating", "is_required": True, "options": []},
            {"question_text": "Any additional thoughts?", "question_type": "long_text", "is_required": False, "options": []},
        ]
    },
    "health": {
        "keywords": ["health", "medical", "patient", "clinic", "hospital", "doctor", "appointment", "symptom", "wellness"],
        "title_suffix": "Health Form",
        "questions": [
            {"question_text": "Full Name", "question_type": "short_text", "is_required": True, "options": []},
            {"question_text": "Date of Birth", "question_type": "date", "is_required": True, "options": []},
            {"question_text": "Email Address", "question_type": "email", "is_required": True, "options": []},
            {"question_text": "Phone Number", "question_type": "phone", "is_required": True, "options": []},
            {"question_text": "Primary Reason for Visit / Complaint", "question_type": "long_text", "is_required": True, "options": []},
            {"question_text": "Do you have any known allergies?", "question_type": "yes_no", "is_required": True, "options": []},
            {"question_text": "If yes, please list your allergies", "question_type": "long_text", "is_required": False, "options": []},
            {"question_text": "Current Medications (if any)", "question_type": "long_text", "is_required": False, "options": []},
            {"question_text": "Preferred Appointment Date", "question_type": "date", "is_required": True, "options": []},
        ]
    },
}

_DEFAULT_QUESTIONS = [
    {"question_text": "Full Name", "question_type": "short_text", "is_required": True, "options": []},
    {"question_text": "Email Address", "question_type": "email", "is_required": True, "options": []},
    {"question_text": "Phone Number", "question_type": "phone", "is_required": False, "options": []},
    {"question_text": "How did you find us?", "question_type": "multiple_choice", "is_required": False, "options": ["Social Media", "Search Engine", "Friend / Referral", "Advertisement", "Other"]},
    {"question_text": "How would you rate your experience?", "question_type": "rating", "is_required": True, "options": []},
    {"question_text": "Additional Comments", "question_type": "long_text", "is_required": False, "options": []},
]


def _detect_template(prompt: str) -> str:
    """Return the best matching template key for the given prompt."""
    prompt_lower = prompt.lower()
    best_key = None
    best_score = 0
    for key, tpl in _FORM_TEMPLATES.items():
        score = sum(1 for kw in tpl["keywords"] if kw in prompt_lower)
        if score > best_score:
            best_score = score
            best_key = key
    return best_key if best_score > 0 else None


def generate_form_from_template(prompt: str) -> dict:
    """Generate a form using the built-in template engine (no API needed)."""
    template_key = _detect_template(prompt)
    template = _FORM_TEMPLATES.get(template_key) if template_key else None

    # Build a clean title from the prompt
    prompt_clean = prompt.strip().rstrip(".")
    title = prompt_clean[:60] if len(prompt_clean) <= 60 else prompt_clean[:57] + "..."
    if template:
        title = title or template["title_suffix"]

    questions = template["questions"] if template else _DEFAULT_QUESTIONS
    description = f"Auto-generated form for: {prompt_clean}"

    return {
        "success": True,
        "data": {
            "title": title,
            "description": description,
            "questions": [dict(q) for q in questions],
        },
        "source": "template"
    }


# ─────────────────────────────────────────────
# Smart Template Engine — Response Analysis
# ─────────────────────────────────────────────

def analyze_responses_template(form_title: str, questions: list, responses_data: list) -> dict:
    """Generate a structured analysis report using pure Python stats (no API needed)."""
    total = len(responses_data)
    if total == 0:
        return {"success": False, "error": "No responses to analyze."}

    sections = {
        "ratings": [],
        "choices": [],
        "texts": [],
        "yes_no": [],
    }

    for q in questions:
        qtype = q.get("question_type", "short_text")
        qtext = q.get("question_text", "")
        q_answers = []

        for resp in responses_data:
            for ans in resp.get("answers", []):
                if ans.get("question_id") == q["id"] and ans.get("answer_value"):
                    q_answers.append(ans["answer_value"])

        if not q_answers:
            continue

        if qtype == "rating":
            try:
                nums = [float(v) for v in q_answers if v.strip().isdigit()]
                if nums:
                    avg = sum(nums) / len(nums)
                    sections["ratings"].append({"q": qtext, "avg": round(avg, 2), "count": len(nums)})
            except Exception:
                pass

        elif qtype in ("multiple_choice", "checkboxes", "dropdown"):
            dist = Counter(q_answers)
            sections["choices"].append({"q": qtext, "dist": dict(dist), "count": len(q_answers)})

        elif qtype == "yes_no":
            dist = Counter(q_answers)
            sections["yes_no"].append({"q": qtext, "dist": dict(dist)})

        else:  # short_text, long_text, email, phone, date, etc.
            sections["texts"].append({"q": qtext, "samples": q_answers[:3], "count": len(q_answers)})

    # Determine overall sentiment from ratings
    all_ratings = [r["avg"] for r in sections["ratings"]]
    if all_ratings:
        overall_avg = sum(all_ratings) / len(all_ratings)
        if overall_avg >= 4.0:
            sentiment = "Positive 😊"
            sentiment_pct = f"~{int(overall_avg / 5 * 100)}% positive"
        elif overall_avg >= 3.0:
            sentiment = "Neutral 😐"
            sentiment_pct = "Mixed responses"
        else:
            sentiment = "Negative 😟"
            sentiment_pct = f"~{int((5 - overall_avg) / 5 * 100)}% dissatisfied"
    else:
        sentiment = "Neutral 😐"
        sentiment_pct = "No rating questions found"

    # Build markdown report
    lines = [
        f"## Executive Summary",
        f"",
        f"This report analyzes **{total} response(s)** collected for the form **\"{form_title}\"**. "
        f"The data was processed automatically using SmartForms' built-in analytics engine.",
        f"",
        f"## Sentiment Analysis",
        f"",
        f"**Overall Sentiment: {sentiment}**",
        f"",
        f"{sentiment_pct}. Based on {len(all_ratings)} rating question(s) across all responses.",
        f"",
        f"## Key Insights",
        f"",
        f"- **Total Responses Collected:** {total}",
    ]

    for r in sections["ratings"]:
        lines.append(f"- **{r['q']}:** Average rating **{r['avg']}/5** across {r['count']} responses")

    for c in sections["choices"]:
        top = max(c["dist"], key=c["dist"].get)
        top_pct = round(c["dist"][top] / c["count"] * 100)
        lines.append(f"- **{c['q']}:** Most common answer — \"{top}\" ({top_pct}%)")

    for yn in sections["yes_no"]:
        yes_count = yn["dist"].get("Yes", yn["dist"].get("yes", 0))
        yes_pct = round(yes_count / total * 100)
        lines.append(f"- **{yn['q']}:** {yes_pct}% answered Yes")

    lines += [
        f"",
        f"## Trends & Patterns",
        f"",
    ]

    if sections["choices"]:
        for c in sections["choices"]:
            dist_str = ", ".join([f'"{k}": {v}' for k, v in sorted(c["dist"].items(), key=lambda x: -x[1])])
            lines.append(f"- **{c['q']}** distribution: {dist_str}")
    else:
        lines.append("- Insufficient structured data to identify strong trends.")

    if sections["texts"]:
        lines.append("")
        lines.append("**Sample open-ended responses:**")
        for t in sections["texts"][:2]:
            if t["samples"]:
                sample_list = "; ".join([f'"{s[:80]}"' for s in t["samples"]])
                lines.append(f"- *{t['q']}*: {sample_list}")

    lines += [
        f"",
        f"## Recommendations",
        f"",
    ]

    recommendations = [
        f"1. **Continue monitoring responses** — with {total} response(s) so far, more data will reveal stronger trends.",
    ]

    if sections["ratings"]:
        low_ratings = [r for r in sections["ratings"] if r["avg"] < 3.5]
        high_ratings = [r for r in sections["ratings"] if r["avg"] >= 4.0]
        if low_ratings:
            recommendations.append(f"2. **Focus on improvement** — \"{low_ratings[0]['q']}\" scored below average ({low_ratings[0]['avg']}/5). Investigate root causes.")
        if high_ratings:
            recommendations.append(f"3. **Leverage strengths** — \"{high_ratings[0]['q']}\" scored highly ({high_ratings[0]['avg']}/5). Highlight this in communications.")

    if len(recommendations) < 3:
        recommendations.append("2. **Increase response volume** — share the form on more channels to get statistically significant data.")
        recommendations.append("3. **Follow up** with respondents who left open-ended feedback for deeper qualitative insights.")
    recommendations.append(f"{len(recommendations) + 1}. **Export the data** to CSV for deeper analysis in spreadsheet tools.")

    lines += recommendations
    lines += [
        f"",
        f"---",
        f"*Report generated automatically by SmartForms Analytics Engine. {total} responses analyzed.*"
    ]

    return {"success": True, "content": "\n".join(lines), "source": "template"}


# ─────────────────────────────────────────────
# Public API — Form Generation
# ─────────────────────────────────────────────

GEMINI_FORM_SYSTEM = """You are an expert form designer. Your sole purpose is to create forms based on user requests.

If the user asks for something unrelated to creating a form (like writing a resume, writing code, answering general questions, or casual chat), DO NOT generate a form. Instead, return EXACTLY this JSON:
{
    "error": "I can only help you create forms. Please describe the form you'd like to build."
}

Otherwise, generate a well-structured form and return ONLY valid JSON with this exact structure:
{
    "title": "Form Title",
    "description": "Brief description of the form",
    "questions": [
        {
            "question_text": "Question text here",
            "question_type": "short_text|long_text|email|phone|multiple_choice|checkboxes|dropdown|rating|yes_no|date",
            "is_required": true,
            "options": ["Option 1", "Option 2"]
        }
    ]
}

Guidelines:
- Generate 6-12 relevant questions
- Use varied question types appropriate to the content
- For rating questions, no options needed (1-5 scale)
- For yes_no questions, no options needed
- Make questions clear and professional
- Return ONLY the JSON, no markdown, no explanation"""


def generate_form_from_prompt(api_key: str, prompt: str) -> dict:
    """
    Generate a form from a natural language prompt.
    Uses Gemini API if key is available, otherwise falls back to template engine.
    """
    prompt_lower = prompt.lower().strip()
    
    # Pre-filter obvious non-form requests
    rejection_phrases = [
        "create a resume", "write a resume", "prepare a resume", 
        "write an essay", "tell me a joke", "write code", 
        "generate code", "build a website", "write a story",
        "who is", "what is", "where is", "when is", "why is", 
        "how do", "tell me about", "can you explain"
    ]
    if any(phrase in prompt_lower for phrase in rejection_phrases) or prompt_lower in ["resume", "cv"]:
        return {
            "success": False, 
            "error": "I can only help you create forms. Please describe the form you'd like to build.", 
            "source": "system"
        }

    # Try Gemini first
    if api_key:
        result = call_gemini(api_key, GEMINI_FORM_SYSTEM, f"Create a form for: {prompt}")
        if result["success"]:
            try:
                content = result["content"].strip()
                # Strip markdown fences if present
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                form_data = json.loads(content)
                if "error" in form_data:
                    return {"success": False, "error": form_data["error"], "source": "gemini"}
                return {"success": True, "data": form_data, "source": "gemini"}
            except json.JSONDecodeError as e:
                print(f"[AI] Gemini returned invalid JSON, falling back to template. Error: {e}")
        else:
            print(f"[AI] Gemini failed ({result['error']}), falling back to template engine.")

    # Fallback: template engine
    print("[AI] Using built-in template engine.")
    return generate_form_from_template(prompt)


# ─────────────────────────────────────────────
# Public API — Response Analysis
# ─────────────────────────────────────────────

GEMINI_ANALYSIS_SYSTEM = """You are an expert data analyst specializing in survey analysis and business intelligence.
Analyze the form response data and provide comprehensive insights.

Structure your response with these EXACT sections using markdown:

## Executive Summary
[2-3 sentences summarizing overall findings]

## Sentiment Analysis
[Analyze the overall sentiment - Positive/Neutral/Negative with percentage estimates and reasoning]

## Key Insights
[5-7 bullet points with the most important findings]

## Trends & Patterns
[Notable patterns, correlations, or trends in the data]

## Recommendations
[3-5 actionable recommendations based on the data]

Be specific, data-driven, and professional. Reference actual numbers and percentages where possible."""


def analyze_responses(api_key: str, form_title: str, questions: list, responses_data: list) -> dict:
    """
    Analyze form responses and return a markdown insight report.
    Uses Gemini API if key is available, otherwise falls back to built-in stats engine.
    """
    if not responses_data:
        return {"success": False, "error": "No responses to analyze."}

    # Try Gemini first
    if api_key:
        # Build summary for Gemini
        summary_parts = [f"Form: {form_title}", f"Total Responses: {len(responses_data)}", "\nQuestions and Answers Summary:"]
        for q in questions:
            q_answers = []
            for resp in responses_data:
                for ans in resp.get("answers", []):
                    if ans.get("question_id") == q["id"] and ans.get("answer_value"):
                        q_answers.append(ans["answer_value"])
            summary_parts.append(f"\nQ: {q['question_text']} ({q['question_type']})")
            if q_answers:
                if q["question_type"] in ("multiple_choice", "dropdown", "yes_no", "rating", "checkboxes"):
                    counts = Counter(q_answers)
                    summary_parts.append(f"Distribution: {dict(counts)}")
                else:
                    summary_parts.append(f"Sample responses ({len(q_answers)} total): {'; '.join(q_answers[:3])}")
            else:
                summary_parts.append("No responses")

        data_summary = "\n".join(summary_parts)
        result = call_gemini(api_key, GEMINI_ANALYSIS_SYSTEM, f"Please analyze this form response data:\n\n{data_summary}")

        if result["success"]:
            return {"success": True, "content": result["content"], "source": "gemini"}
        else:
            print(f"[AI] Gemini analysis failed ({result['error']}), falling back to template engine.")

    # Fallback: built-in stats analysis
    print("[AI] Using built-in template analysis engine.")
    return analyze_responses_template(form_title, questions, responses_data)


# ─────────────────────────────────────────────
# Public API — Email Drafting
# ─────────────────────────────────────────────

GEMINI_EMAIL_DRAFT_SYSTEM = """You are a world-class HR Communications Director and expert copywriter.
Your task is to draft a highly professional, engaging, and polished company email based on the user's prompt.

The email must feel personal, authentic, and clear. Avoid robotic or overly generic template phrases.

You MUST output ONLY a valid JSON object in the following exact format, with no other text, markdown blocks, or commentary around it:
{
  "subject": "A compelling, clear, and professional subject line",
  "body": "The email body text. Use double newlines (\\n\\n) to separate paragraphs."
}

Important constraints for the "body":
1. You MUST address the recipient using the `{name}` placeholder at the very beginning (e.g., 'Dear {name},' or 'Hi {name},' depending on the tone).
2. The email must have a clean, logical structure:
   - A warm, engaging opening sentence.
   - A detailed body section explaining the core message clearly. If appropriate, use styled plain-text bullet points (e.g., '• Point 1\\n• Point 2').
   - A clear call-to-action or next steps (if applicable).
   - A warm and professional closing statement.
   - A professional signature block (e.g., 'Best regards,\\nHR Operations Team' or similar).
3. The tone should match the context: warm and welcoming for onboarding/celebrations, clear and direct for announcements, polite yet urgent for reminders/deadlines."""


def draft_email_template(prompt: str) -> dict:
    """Generate an email draft using the built-in template engine (no API needed)."""
    p_lower = prompt.lower()
    
    # 1. Determine a good subject line based on keywords
    if any(kw in p_lower for kw in ["welcome", "onboarding", "new hire", "join"]):
        subject = "Welcome to the Team!"
    elif any(kw in p_lower for kw in ["reminder", "deadline", "due date"]):
        subject = "Action Required: Upcoming Deadline / Reminder"
    elif any(kw in p_lower for kw in ["meeting", "sync", "call", "schedule", "tomorrow", "calendar"]):
        subject = "Meeting Announcement & Schedule Update"
    elif any(kw in p_lower for kw in ["holiday", "celebration", "festival", "event", "closure", "office"]):
        subject = "Notice: Holiday Schedule & Office Update"
    elif any(kw in p_lower for kw in ["policy", "procedure", "update", "handbook"]):
        subject = "Important Update: Policy & Guidelines"
    elif any(kw in p_lower for kw in ["survey", "feedback", "appraisal", "review"]):
        subject = "Your Feedback Requested: Team Development & Alignment"
    else:
        # Generate a clean subject from the prompt prefix
        words = prompt.split()
        if len(words) > 5:
            subject = "HR Update: " + " ".join(words[:5]) + "..."
        else:
            subject = "HR Update: " + prompt
            
    # Remove common prefix commands from the prompt to make it a natural sentence
    clean_prompt = prompt.strip()
    prefixes_to_remove = [
        "draft an email about", "draft a welcome email about", "draft a welcome email for",
        "draft an email to", "draft a reminder about", "draft a meeting request for",
        "write an email about", "write an email to", "write a reminder about",
        "send an email about", "send a reminder about", "tell employees that",
        "draft a", "draft an", "write a", "write an", "email about", "remind everyone that",
        "remind employees that", "inform everyone that", "inform employees that"
    ]
    
    for prefix in sorted(prefixes_to_remove, key=len, reverse=True):
        if clean_prompt.lower().startswith(prefix):
            clean_prompt = clean_prompt[len(prefix):].strip()
            
    # Capitalize the first letter of the cleaned prompt
    if clean_prompt:
        clean_prompt = clean_prompt[0].upper() + clean_prompt[1:]
        
    # Ensure it ends with a period if not ending with punctuation
    if clean_prompt and clean_prompt[-1] not in ['.', '!', '?']:
        clean_prompt += '.'

    # 2. Build the email body incorporating the clean prompt details
    if any(kw in p_lower for kw in ["welcome", "onboarding", "new hire", "join"]):
        body = (
            "Dear {name},\n\n"
            "We are absolutely thrilled to welcome you to our organization! Your arrival marks an exciting new chapter for our department, and we are confident that your skills, background, and perspective will make a tremendous impact here.\n\n"
            f"Here is a brief update regarding your upcoming transition: {clean_prompt}\n\n"
            "Over the next few days, we will guide you through our onboarding process, introduce you to the team, and help you get settled into your role. We want to ensure you have all the tools, resources, and support needed to succeed from day one.\n\n"
            "If you have any questions or need anything at all before your official start date, please do not hesitate to reach out to us.\n\n"
            "Once again, welcome to the family! We look forward to achieving great things together.\n\n"
            "Best regards,\n"
            "People & Culture Team"
        )
    elif any(kw in p_lower for kw in ["reminder", "deadline", "due date"]):
        body = (
            "Dear {name},\n\n"
            "This is a quick reminder regarding an important action item or upcoming deadline that requires your attention.\n\n"
            f"Action Required: {clean_prompt}\n\n"
            "To help us keep our operations running smoothly and stay on track, please review the requirements and complete this task at your earliest convenience.\n\n"
            "If you have already completed this, please disregard this message. If you encounter any issues or need extra support to meet the deadline, please let us know so we can assist you.\n\n"
            "Thank you for your prompt attention and cooperation.\n\n"
            "Best regards,\n"
            "HR Operations Team"
        )
    elif any(kw in p_lower for kw in ["meeting", "sync", "call", "schedule", "tomorrow", "calendar"]):
        body = (
            "Dear {name},\n\n"
            "We have scheduled an upcoming meeting to sync and align on our latest initiatives. Your presence and input are highly valued.\n\n"
            f"Meeting Details & Context: {clean_prompt}\n\n"
            "Please check your calendar for the invite link. If you have any agenda items you would like to add, or if you have a scheduling conflict, please reach out as soon as possible so we can adjust accordingly.\n\n"
            "Looking forward to a productive discussion.\n\n"
            "Warm regards,\n"
            "HR Coordination Team"
        )
    elif any(kw in p_lower for kw in ["holiday", "celebration", "festival", "event", "closure", "office"]):
        body = (
            "Dear {name},\n\n"
            "As we approach the upcoming holiday season or special event, we wanted to share some details and office schedule updates with you.\n\n"
            f"Announcements & Details: {clean_prompt}\n\n"
            "We hope this occasion gives you a wonderful opportunity to unwind, rest, and celebrate with your loved ones. Thank you for your incredible hard work that makes events like these possible.\n\n"
            "Have a fantastic time, and stay safe!\n\n"
            "Warmest wishes,\n"
            "The HR Team"
        )
    elif any(kw in p_lower for kw in ["survey", "feedback", "appraisal", "review"]):
        body = (
            "Dear {name},\n\n"
            "We are constantly working to improve our workplace culture and operational efficiency, and your feedback is a vital part of that journey.\n\n"
            f"Feedback / Survey Details: {clean_prompt}\n\n"
            "Please take a few minutes to share your honest thoughts, suggestions, and feedback. Your insights help us make meaningful updates that benefit everyone in the organization.\n\n"
            "Thank you for contributing to our continuous improvement.\n\n"
            "Best regards,\n"
            "People Operations"
        )
    elif any(kw in p_lower for kw in ["policy", "procedure", "update", "handbook"]):
        body = (
            "Dear {name},\n\n"
            "Please be advised of an important update to our company policies and operational guidelines.\n\n"
            f"Policy Update Details: {clean_prompt}\n\n"
            "We ask that you review these changes carefully to ensure complete alignment across all teams. If you have any questions or require clarification on how these updates apply to your role, please reach out to us.\n\n"
            "Thank you for your cooperation and commitment to maintaining our professional standards.\n\n"
            "Sincerely,\n"
            "HR Compliance & Policy Team"
        )
    else:
        body = (
            "Dear {name},\n\n"
            "We are reaching out to share an important company-wide update and announcement with you.\n\n"
            f"Details: {clean_prompt}\n\n"
            "We appreciate your dedication, focus, and the hard work you bring to our organization every single day. If you have any questions or feedback regarding this announcement, please feel free to reach out to the HR team.\n\n"
            "Sincerely,\n"
            "The HR Team"
        )

    return {"success": True, "subject": subject, "body": body, "source": "template"}


def draft_email(api_key: str, prompt: str) -> dict:
    """Draft an email from a prompt. Uses Gemini if available, otherwise falls back."""
    # Ensure api_key is valid and not a placeholder or string representation of null/none
    if api_key and api_key.strip().lower() not in ('none', 'null', 'undefined', 'your_api_key_here', 'api_key_here'):
        result = call_gemini(api_key, GEMINI_EMAIL_DRAFT_SYSTEM, f"Draft an email based on: {prompt}")
        if result["success"]:
            try:
                content = result["content"].strip()
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                data = json.loads(content)
                if "subject" in data and "body" in data:
                    return {"success": True, "subject": data["subject"], "body": data["body"], "source": "gemini"}
            except Exception as e:
                print(f"[AI] Failed to parse generated email JSON: {e}")
                
    return draft_email_template(prompt)
