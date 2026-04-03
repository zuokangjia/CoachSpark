MATCH_SYSTEM_PROMPT = """You are an expert technical recruiter and career coach.
Your job is to objectively compare a candidate's resume against a job description
and provide actionable insights.

Be specific and evidence-based. Do not give generic advice.
"""

MATCH_USER_PROMPT = """## Job Description
{jd_text}

## Candidate Resume
{resume_text}

## Task
Compare the resume against the job description and return a JSON object with:
- match_percentage: integer 0-100
- strengths: list of things the candidate has that match the JD
- gaps: list of things the JD requires but the resume doesn't show
- suggestions: list of specific, actionable suggestions before applying

## Output Format (JSON only, no markdown)
{{
  "match_percentage": 72,
  "strengths": ["5 years React experience matches requirement", ...],
  "gaps": ["No mention of CI/CD experience", ...],
  "suggestions": ["Add CI/CD projects to resume", ...]
}}
"""
