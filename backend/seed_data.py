"""
Seed script to populate database with realistic test data.
Run: python seed_data.py
"""

import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import SessionLocal, engine, Base
from app.db.models import Company, Interview, generate_uuid

Base.metadata.create_all(bind=engine)
db = SessionLocal()
today = date.today()


def add_iv(**kwargs):
    iv = Interview(**kwargs)
    db.add(iv)
    return iv


def create_test_data():
    try:
        companies = []

        # 1. Google - Frontend Engineer (tomorrow round 2)
        google = Company(
            id=generate_uuid(),
            name="Google",
            position="Frontend Engineer",
            status="interviewing",
            applied_date=today - timedelta(days=14),
            next_event_date=today + timedelta(days=1),
            next_event_type="interview",
            jd_text="5+ years frontend experience. Deep knowledge of React, TypeScript, and web performance.",
        )
        db.add(google)
        db.flush()
        companies.append(google)

        add_iv(
            id=generate_uuid(),
            company_id=google.id,
            round=1,
            interview_date=today - timedelta(days=7),
            format="video",
            interviewer="Alice Wang",
            raw_notes="React hooks and closure. useEffect cleanup OK but closure trap failed.",
            ai_analysis={
                "questions": [
                    {
                        "question": "useEffect cleanup timing vs componentWillUnmount",
                        "your_answer_summary": "Cleanup runs before next render and on unmount. Differs from componentWillUnmount as it responds to any dependency change.",
                        "score": 8,
                        "assessment": "Accurate answer covering dependency array impact. Missed React 18 StrictMode double-invoke behavior.",
                        "improvement": "Study React 18 StrictMode dev-only double invoke for useEffect.",
                    },
                    {
                        "question": "Output: for(var i=0;i<3;i++){setTimeout(()=>console.log(i),0)}",
                        "your_answer_summary": "Three 3s because var is function-scoped and setTimeout is async.",
                        "score": 5,
                        "assessment": "Knew result but missed closure capturing reference vs value.",
                        "improvement": "Explain closure reference capture vs value, and how let block scope solves this.",
                    },
                    {
                        "question": "Most challenging frontend project",
                        "your_answer_summary": "Internal low-code platform with drag-and-drop, custom DSL and render engine.",
                        "score": 8,
                        "assessment": "Solid project experience with clear architecture description.",
                        "improvement": "Add quantifiable metrics like improved ops efficiency by 40 percent.",
                    },
                ],
                "weak_points": ["Closure in loops", "React StrictMode behavior"],
                "strong_points": [
                    "React Hooks deep understanding",
                    "Project architecture experience",
                ],
                "next_round_prediction": [
                    "System Design",
                    "Browser rendering pipeline",
                    "Performance optimization",
                ],
                "interviewer_signals": [
                    "Interviewer asked 3 DSL details, team likely has similar needs",
                    "Closure trap not followed up, probably considered a basic requirement",
                    "Left 10 minutes for questions, good sign for passing",
                ],
            },
            expected_result_date=today - timedelta(days=5),
            result_status="passed",
        )

        add_iv(
            id=generate_uuid(),
            company_id=google.id,
            round=2,
            interview_date=today + timedelta(days=1),
            format="onsite",
            interviewer="Bob Chen",
            ai_analysis={},
            expected_result_date=today + timedelta(days=5),
            result_status="pending",
        )

        # 2. Tencent - Web Developer (result overdue)
        tencent = Company(
            id=generate_uuid(),
            name="Tencent",
            position="Web Developer",
            status="interviewing",
            applied_date=today - timedelta(days=20),
            jd_text="Proficient in Vue.js ecosystem. Node.js backend experience. Understanding of microservices architecture.",
        )
        db.add(tencent)
        db.flush()
        companies.append(tencent)

        add_iv(
            id=generate_uuid(),
            company_id=tencent.id,
            round=1,
            interview_date=today - timedelta(days=8),
            format="video",
            interviewer="Charlie Liu",
            raw_notes="Node.js event loop phases incomplete. Confused setImmediate vs nextTick.",
            ai_analysis={
                "questions": [
                    {
                        "question": "Node.js Event Loop phases in order",
                        "your_answer_summary": "Named timers, poll, check. Missed close callbacks and I/O callbacks.",
                        "score": 4,
                        "assessment": "Only named main phases. Confused setImmediate with process.nextTick.",
                        "improvement": "Master all 6 phases: timers, pending callbacks, idle/prepare, poll, check, close callbacks.",
                    },
                    {
                        "question": "Promise vs Observable differences and use cases",
                        "your_answer_summary": "Promise is single async, Observable is stream that emits multiple times.",
                        "score": 7,
                        "assessment": "Core difference clear. Missed backpressure concept.",
                        "improvement": "Study backpressure mechanism and Observable advantages.",
                    },
                    {
                        "question": "Microservices projects and challenges",
                        "your_answer_summary": "Split monolith into 5 microservices. Mentioned service discovery and API Gateway.",
                        "score": 6,
                        "assessment": "Has practical experience but description is shallow.",
                        "improvement": "Prepare specific microservice incident case studies.",
                    },
                ],
                "weak_points": ["Node.js Event Loop", "Microservices troubleshooting"],
                "strong_points": [
                    "Reactive programming concepts",
                    "Service decomposition experience",
                ],
                "next_round_prediction": [
                    "System Architecture",
                    "High-concurrency design",
                ],
                "interviewer_signals": [
                    "Event loop is basic, poor answer may fail round 1",
                    "Few follow-ups on microservices, role focuses on frontend",
                ],
            },
            expected_result_date=today - timedelta(days=3),
            result_status="pending",
        )

        # 3. Alibaba - Senior Frontend (unreviewed, 3 days ago)
        alibaba = Company(
            id=generate_uuid(),
            name="Alibaba",
            position="Senior Frontend Engineer",
            status="interviewing",
            applied_date=today - timedelta(days=10),
            jd_text="Expert in React ecosystem. Deep understanding of webpack/vite. Web performance optimization.",
        )
        db.add(alibaba)
        db.flush()
        companies.append(alibaba)

        add_iv(
            id=generate_uuid(),
            company_id=alibaba.id,
            round=1,
            interview_date=today - timedelta(days=3),
            format="video",
            interviewer="David Zhang",
            raw_notes="React performance and Webpack. useMemo, React.memo, virtual list but missed time slicing.",
            ai_analysis={},
            expected_result_date=today + timedelta(days=2),
            result_status="pending",
        )

        # 4. ByteDance - Frontend Architect (rejected, 2 rounds)
        bytedance = Company(
            id=generate_uuid(),
            name="ByteDance",
            position="Frontend Architect",
            status="closed",
            applied_date=today - timedelta(days=30),
            jd_text="Deep understanding of React source code. System design for frontend infrastructure.",
        )
        db.add(bytedance)
        db.flush()
        companies.append(bytedance)

        add_iv(
            id=generate_uuid(),
            company_id=bytedance.id,
            round=1,
            interview_date=today - timedelta(days=20),
            format="video",
            interviewer="Eva Li",
            raw_notes="React Fiber and Diff. Fiber: linked list and time slicing but missed priority. Diff: key and same-level but double-ended unclear.",
            ai_analysis={
                "questions": [
                    {
                        "question": "What problem does React Fiber solve? Core design?",
                        "your_answer_summary": "Changed recursive rendering to linked list, can interrupt and resume.",
                        "score": 6,
                        "assessment": "Core idea correct but missed Lane priority model and Fiber node flags.",
                        "improvement": "Study Lane priority model and Fiber node pointer relationships.",
                    },
                    {
                        "question": "React Diff algorithm optimization strategies",
                        "your_answer_summary": "Key importance, same-level comparison, type replacement.",
                        "score": 5,
                        "assessment": "Basic strategies correct but lacked double-ended diff understanding.",
                        "improvement": "Study full Diff algorithm with minimum move operations.",
                    },
                ],
                "weak_points": ["React Fiber internals", "React Diff algorithm"],
                "strong_points": [
                    "Project architecture experience",
                    "Clear communication",
                ],
                "next_round_prediction": [
                    "System Design",
                    "Performance optimization cases",
                ],
                "interviewer_signals": [
                    "Fiber and Diff are core, shallow answers likely to fail",
                    "Interviewer followed up on Diff twice, hard requirement",
                ],
            },
            expected_result_date=today - timedelta(days=18),
            result_status="passed",
        )

        add_iv(
            id=generate_uuid(),
            company_id=bytedance.id,
            round=2,
            interview_date=today - timedelta(days=12),
            format="onsite",
            interviewer="Frank Wu",
            raw_notes="System design: TikTok feed. Pagination, lazy loading, virtual list but missed prefetch. First screen: only SSR, missed streaming SSR.",
            ai_analysis={
                "questions": [
                    {
                        "question": "Design a short video feed frontend architecture",
                        "your_answer_summary": "Virtual list, pagination, lazy loading, CDN.",
                        "score": 5,
                        "assessment": "Reasonable basics but missing prefetch, offline cache. Not architect-level depth.",
                        "improvement": "Study complete feed architecture with prefetch and cache strategy.",
                    },
                    {
                        "question": "How to optimize first screen load to under 1 second?",
                        "your_answer_summary": "SSR, code splitting, resource compression.",
                        "score": 4,
                        "assessment": "Only standard solutions. Missed streaming SSR, Selective Hydration, Resource Hints.",
                        "improvement": "Study streaming SSR, Partial Prerendering, Edge Rendering.",
                    },
                    {
                        "question": "React Diff optimization for list scenarios",
                        "your_answer_summary": "Use unique keys, avoid index as key.",
                        "score": 5,
                        "assessment": "Same question as round 1, no noticeable improvement.",
                        "improvement": "Should have reviewed Diff algorithm after round 1.",
                    },
                ],
                "weak_points": [
                    "System Design",
                    "React Diff algorithm",
                    "Performance optimization at scale",
                ],
                "strong_points": [
                    "Basic architecture thinking",
                    "Communication skills",
                ],
                "next_round_prediction": [],
                "interviewer_signals": [
                    "React Diff asked again with no improvement, fatal",
                    "System design lacks architect-level depth, likely rejection reason",
                    "Interviewer did not introduce team at end, usually a fail signal",
                ],
            },
            expected_result_date=today - timedelta(days=10),
            result_status="rejected",
        )

        # 5. Meituan - Frontend Dev (just applied)
        meituan = Company(
            id=generate_uuid(),
            name="Meituan",
            position="Frontend Developer",
            status="applied",
            applied_date=today,
            jd_text="Vue.js, Mini-program development, CSS animation, responsive design.",
        )
        db.add(meituan)
        companies.append(meituan)

        # 6. PDD - 3 rounds passed, waiting for offer
        pdd = Company(
            id=generate_uuid(),
            name="PDD",
            position="Senior Frontend Engineer",
            status="interviewing",
            applied_date=today - timedelta(days=25),
            next_event_date=today + timedelta(days=2),
            next_event_type="offer",
            jd_text="React, TypeScript, Node.js. E-commerce experience. Performance optimization.",
        )
        db.add(pdd)
        db.flush()
        companies.append(pdd)

        add_iv(
            id=generate_uuid(),
            company_id=pdd.id,
            round=1,
            interview_date=today - timedelta(days=18),
            format="video",
            ai_analysis={
                "questions": [
                    {
                        "question": "TypeScript generics usage with practical example",
                        "your_answer_summary": "Basic generics with API request wrapper example.",
                        "score": 7,
                        "assessment": "Correct basics with practical example. Missed generic constraints and conditional types.",
                        "improvement": "Study advanced generics: extends constraint, infer inference, conditional types.",
                    },
                ],
                "weak_points": ["Advanced TypeScript"],
                "strong_points": ["Practical API design"],
                "next_round_prediction": ["React internals"],
            },
            result_status="passed",
        )

        add_iv(
            id=generate_uuid(),
            company_id=pdd.id,
            round=2,
            interview_date=today - timedelta(days=10),
            format="video",
            ai_analysis={
                "questions": [
                    {
                        "question": "React state management comparison",
                        "your_answer_summary": "Compared Redux, MobX, Zustand, Context API with use cases.",
                        "score": 8,
                        "assessment": "Comprehensive comparison with project-based recommendations.",
                        "improvement": "Add Recoil and Jotai atomic state management solutions.",
                    },
                ],
                "weak_points": [],
                "strong_points": [
                    "State management expertise",
                    "Technology comparison ability",
                ],
                "next_round_prediction": ["System Design", "Leadership"],
            },
            result_status="passed",
        )

        add_iv(
            id=generate_uuid(),
            company_id=pdd.id,
            round=3,
            interview_date=today - timedelta(days=3),
            format="onsite",
            ai_analysis={
                "questions": [
                    {
                        "question": "How to lead frontend team technical growth?",
                        "your_answer_summary": "Tech sharing, Code Review, tech debt management, onboarding plan.",
                        "score": 7,
                        "assessment": "Clear thinking with management experience. Lacked quantifiable metrics.",
                        "improvement": "Prepare specific team improvement cases with metrics.",
                    },
                ],
                "weak_points": ["Quantifiable leadership results"],
                "strong_points": ["Team management experience", "Technical vision"],
                "next_round_prediction": [],
            },
            expected_result_date=today + timedelta(days=2),
            result_status="pending",
        )

        # 7. JD.com - rejected after round 1
        jingdong = Company(
            id=generate_uuid(),
            name="JD.com",
            position="Frontend Engineer",
            status="closed",
            applied_date=today - timedelta(days=15),
            jd_text="React, Vue, CSS, Webpack, performance optimization.",
        )
        db.add(jingdong)
        db.flush()
        companies.append(jingdong)

        add_iv(
            id=generate_uuid(),
            company_id=jingdong.id,
            round=1,
            interview_date=today - timedelta(days=10),
            format="video",
            ai_analysis={
                "questions": [
                    {
                        "question": "CSS box model, box-sizing values",
                        "your_answer_summary": "content-box and border-box, missed inherit and initial.",
                        "score": 6,
                        "assessment": "Basic values correct but missed CSS keywords. Should be perfect for round 1.",
                        "improvement": "Review CSS fundamentals to avoid losing points on basics.",
                    },
                    {
                        "question": "Webpack loader vs plugin difference",
                        "your_answer_summary": "Loader transforms files, plugin extends functionality. Examples: babel-loader, HtmlWebpackPlugin.",
                        "score": 7,
                        "assessment": "Clear concepts with good examples. Missed tapable and hook mechanism.",
                        "improvement": "Study Webpack plugin system tapable hook mechanism.",
                    },
                    {
                        "question": "Write a debounce function",
                        "your_answer_summary": "Basic version written but missed this binding and immediate option.",
                        "score": 5,
                        "assessment": "Core logic correct but missing edge cases.",
                        "improvement": "When hand-coding, address: this binding, arguments, immediate option, cancel method.",
                    },
                ],
                "weak_points": ["CSS fundamentals", "Hand-coding completeness"],
                "strong_points": ["Webpack concepts", "Clear explanations"],
                "next_round_prediction": [],
                "interviewer_signals": [
                    "CSS basics incomplete, may leave impression of weak fundamentals",
                    "Incomplete hand-coding, frontend round 1 coding is mandatory",
                ],
            },
            result_status="rejected",
        )

        db.commit()
        print("=" * 60)
        print("Test data seeded successfully!")
        print("=" * 60)
        for c in companies:
            ivs = db.query(Interview).filter(Interview.company_id == c.id).all()
            print(f"\n{c.name} ({c.position}) - Status: {c.status}")
            for iv in ivs:
                a = iv.ai_analysis if isinstance(iv.ai_analysis, dict) else {}
                qc = len(a.get("questions", []))
                icon = (
                    "PASS"
                    if iv.result_status == "passed"
                    else "FAIL"
                    if iv.result_status == "rejected"
                    else "WAIT"
                )
                print(f"  Round {iv.round} ({iv.format}) - {qc} questions [{icon}]")

    except Exception as e:
        db.rollback()
        print(f"Error seeding data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_test_data()
