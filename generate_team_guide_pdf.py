import os
import pymupdf

def build_team_pdf():
    pdf_path = os.path.abspath("SkillGraph_Team_Roles_and_Codebase_Guide.pdf")
    
    html = """
    <style>
        @page {
            size: A4;
            margin: 32pt 36pt 32pt 36pt;
        }
        body {
            font-family: sans-serif;
            font-size: 9pt;
            line-height: 1.4;
            color: #1e1e1e;
        }
        h1 {
            font-size: 18pt;
            color: #0f172a;
            margin-bottom: 2pt;
            padding-bottom: 3pt;
            border-bottom: 2pt solid #0284c7;
        }
        .subtitle {
            font-size: 10pt;
            color: #475569;
            margin-top: 0;
            margin-bottom: 12pt;
        }
        h2 {
            font-size: 12.5pt;
            color: #0369a1;
            margin-top: 12pt;
            margin-bottom: 4pt;
            border-bottom: 1pt solid #cbd5e1;
            padding-bottom: 2pt;
        }
        h3 {
            font-size: 10pt;
            color: #1e293b;
            margin-top: 8pt;
            margin-bottom: 3pt;
        }
        p {
            margin-top: 2pt;
            margin-bottom: 4pt;
        }
        ul, ol {
            margin-top: 2pt;
            margin-bottom: 4pt;
            padding-left: 16pt;
        }
        li {
            margin-bottom: 2pt;
        }
        code {
            font-family: monospace;
            background-color: #f1f5f9;
            color: #0f172a;
            padding: 1pt 3pt;
            font-size: 8pt;
            border-radius: 2pt;
        }
        pre {
            background-color: #f8fafc;
            border: 1pt solid #e2e8f0;
            padding: 5pt 7pt;
            font-family: monospace;
            font-size: 7.5pt;
            line-height: 1.3;
            margin: 4pt 0;
            border-radius: 3pt;
        }
        .callout {
            background-color: #f0fdf4;
            border-left: 3pt solid #16a34a;
            padding: 5pt 8pt;
            margin: 6pt 0;
            font-size: 8.5pt;
        }
        .qa-box {
            background-color: #fefce8;
            border-left: 3pt solid #ca8a04;
            padding: 5pt 8pt;
            margin: 5pt 0;
            font-size: 8.5pt;
        }
        .file-box {
            background-color: #f8fafc;
            border: 1pt solid #cbd5e1;
            border-radius: 3pt;
            padding: 4pt 6pt;
            margin-bottom: 4pt;
        }
        .file-name {
            font-weight: bold;
            color: #0369a1;
            font-size: 8.5pt;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 6pt 0;
            font-size: 8pt;
        }
        th, td {
            border: 1pt solid #cbd5e1;
            padding: 4pt 5pt;
            text-align: left;
        }
        th {
            background-color: #f1f5f9;
            font-weight: bold;
            color: #0f172a;
        }
        .member-header {
            background-color: #0369a1;
            color: white;
            padding: 4pt 8pt;
            border-radius: 3pt;
            font-size: 11pt;
            font-weight: bold;
            margin-top: 14pt;
            margin-bottom: 6pt;
        }
    </style>

    <h1>SkillGraph: 4-Member Team Codebase Division & Oral Exam Defense Guide</h1>
    <div class="subtitle">Complete File Ownership, Technical Explanations, Internal Mechanics, and Teacher Q&A Preparation</div>

    <div class="callout">
        <strong>Objective:</strong> Every team member has an equal, specialized ownership of Frontend (HTML/CSS/JS), Backend (Routers/Services/Schemas), Data/Models, and Automated Tests. When the teacher asks any member to explain a file, that member can explain the code line-by-line, its architectural purpose, and defend it with confidence.
    </div>

    <h2>1. Master Team Division Matrix</h2>
    <table>
        <tr>
            <th>Member</th>
            <th>Role & Specialization</th>
            <th>Frontend Files</th>
            <th>Backend Files (API & Services)</th>
            <th>Database & Tests</th>
        </tr>
        <tr>
            <td><strong>Member 1</strong><br/>(You / Lead)</td>
            <td><strong>Platform Architecture, Auth & Resume Ingestion</strong></td>
            <td><code>index.html</code>, <code>dashboard.html</code>,<br/><code>app.js</code>, <code>dashboard.js</code>,<br/><code>dashboard.css</code></td>
            <td><code>main.py</code>, <code>config.py</code>, <code>auth.py</code> (API/Svc/Sch),<br/><code>resume.py</code> (API/Sch),<br/><code>resume_parser.py</code></td>
            <td><code>database.py</code>,<br/><code>models/user.py</code>, <code>resume.py</code>,<br/><code>test_auth.py</code>, <code>test_resume.py</code>,<br/><code>test_database.py</code>, <code>test_health.py</code></td>
        </tr>
        <tr>
            <td><strong>Member 2</strong></td>
            <td><strong>Resume Quality Advisor & Coding Signal Harvesters</strong></td>
            <td><code>resume-review.html</code>, <code>coding.html</code>,<br/><code>resume-review.js</code>, <code>coding.js</code></td>
            <td><code>profiles.py</code> (API/Sch),<br/><code>coding_profiles.py</code>,<br/><code>resume_advisor.py</code> (API/Svc/Sch)</td>
            <td><code>test_resume_advisor.py</code>,<br/><code>test_coding_profiles.py</code></td>
        </tr>
        <tr>
            <td><strong>Member 3</strong></td>
            <td><strong>Skill Taxonomy, Role Gap Analysis & Job Market Analytics</strong></td>
            <td><code>analytics.html</code>, <code>roles.html</code>,<br/><code>analytics.js</code>, <code>roles.js</code></td>
            <td><code>skills.py</code>, <code>roles.py</code>, <code>job_descriptions.py</code> (API/Svc/Sch),<br/><code>skill_extractor.py</code>, <code>skill_analyzer.py</code>,<br/><code>role_discovery.py</code>, <code>market_insights.py</code>,<br/><code>job_market_analytics.py</code></td>
            <td><code>models/job_description.py</code>, <code>analysis.py</code>,<br/><code>role_profiles.json</code>, <code>skill_aliases.json</code>, <code>verified_market_data.json</code>,<br/><code>test_skills.py</code>, <code>test_role_discovery.py</code>,<br/><code>test_job_description.py</code>, <code>test_job_market_analytics.py</code></td>
        </tr>
        <tr>
            <td><strong>Member 4</strong></td>
            <td><strong>Roadmap Generation, Design System & DevOps Infrastructure</strong></td>
            <td><code>roadmap.html</code>, <code>roadmap.js</code>,<br/><code>variables.css</code>, <code>style.css</code>,<br/><code>components.css</code>, <code>roadmap.css</code>,<br/><code>config.js</code>, <code>api.js</code>, SVG icons</td>
            <td><code>roadmap.py</code> (API/Svc/Sch),<br/><code>roadmap_generator.py</code></td>
            <td><code>models/roadmap.py</code>, <code>progress.py</code>,<br/><code>Dockerfile</code>, <code>.dockerignore</code>, <code>run.bat</code>,<br/><code>test_roadmap.py</code>, <code>test_frontend_integration.py</code>,<br/><code>test_workflow.py</code></td>
        </tr>
    </table>

    <div class="member-header">MEMBER 1: Platform Architecture, Auth & Resume Parsing</div>
    <p><strong>Primary Focus:</strong> Application bootstrap, ASGI security/CORS, user authentication lifecycle, file byte security, and raw resume extraction.</p>

    <h3>Files to Read & Master:</h3>
    <div class="file-box">
        <div class="file-name">backend/app/main.py & backend/app/config.py</div>
        <p><strong>What it does:</strong> The central FastAPI application factory. <code>config.py</code> uses <code>pydantic_settings.BaseSettings</code> to load environment variables (SECRET_KEY, CORS_ORIGINS, DATABASE_URL) with safe fallbacks. <code>main.py</code> configures CORS middleware, declares the async <code>lifespan()</code> context manager that initializes database tables, registers all 7 API routers, and mounts the <code>/frontend</code> directory as static files.</p>
    </div>
    <div class="file-box">
        <div class="file-name">backend/app/database.py, models/user.py, models/resume.py</div>
        <p><strong>What it does:</strong> <code>database.py</code> configures SQLAlchemy's <code>create_engine</code> and <code>sessionmaker</code> with SQLite connection settings (disabling same-thread checks for async compatibility). <code>models/user.py</code> defines the User table with hashed passwords. <code>models/resume.py</code> defines the Resume table with foreign key linking to User, storing raw extracted text, parsed skill JSON, and timestamps.</p>
    </div>
    <div class="file-box">
        <div class="file-name">backend/app/services/resume_parser.py & api/resume.py</div>
        <p><strong>What it does:</strong> Implements safe file ingestion. Checks <em>magic bytes</em>: PDF files must start with <code>%PDF-</code> and DOCX with <code>PK\x03\x04</code>. If someone renames an .exe or malware file to .pdf, it is rejected immediately. It extracts plain text using <code>pymupdf</code> for PDFs and <code>python-docx</code> for Word documents, normalizes whitespace, and extracts detected skills.</p>
    </div>
    <div class="file-box">
        <div class="file-name">frontend/index.html, dashboard.html, js/app.js, js/dashboard.js</div>
        <p><strong>What it does:</strong> <code>index.html</code> is the landing page with mobile drawer toggle and CTA navigation. <code>dashboard.html</code> provides the drag-and-drop resume upload zone, file reader, readiness hero scorecard, and radar chart. <code>dashboard.js</code> listens for file upload events, calls <code>API.resume.upload()</code>, and renders skill tags dynamically.</p>
    </div>

    <div class="qa-box">
        <strong>Expected Teacher Questions for Member 1:</strong><br/>
        <strong>Q: How do you prevent users from uploading malicious executable files disguised as PDFs?</strong><br/>
        <em>Answer:</em> In <code>resume_parser.py</code>, we don't rely on the file extension string. We inspect the first few bytes (the "magic bytes"). Valid PDFs start strictly with <code>b'%PDF-'</code>. Valid Word DOCX files are zip archives starting with <code>b'PK\x03\x04'</code>. If magic bytes don't match, we raise an <code>HTTP 400 Bad Request</code>.<br/>
        <strong>Q: How does authentication work without sessions?</strong><br/>
        <em>Answer:</em> In <code>services/auth.py</code>, we hash passwords using <code>passlib</code> with bcrypt. Upon successful login, we generate an HMAC-SHA256 JSON Web Token (JWT) containing the user ID and expiration time. The frontend stores this token and sends it in the <code>Authorization: Bearer &lt;token&gt;</code> header.
    </div>

    <div class="member-header">MEMBER 2: Resume Quality Advisor & Coding Signal Harvesters</div>
    <p><strong>Primary Focus:</strong> AI candidate evaluation, Google XYZ bullet rewriting, GitHub REST API, LeetCode GraphQL, and DSA Interview Readiness.</p>

    <h3>Files to Read & Master:</h3>
    <div class="file-box">
        <div class="file-name">backend/app/services/resume_advisor.py & schemas/resume_advisor.py</div>
        <p><strong>What it does:</strong> Audits resume text across 4 weighted dimensions:
        <ol>
            <li><strong>Metric Quantification (0-25):</strong> Identifies metrics ($ values, %, numbers, scale) representing impact.</li>
            <li><strong>Action Verb Strength (0-25):</strong> Checks for power verbs (<em>architected, spearheaded, accelerated</em>) vs weak passive verbs (<em>worked on, helped, responsible for</em>).</li>
            <li><strong>Keyword Density (0-25):</strong> Calculates density of canonical tech skills.</li>
            <li><strong>Fluff Penalty (0-25):</strong> Penalizes non-technical buzzwords (<em>go-getter, guru, hard worker</em>).</li>
        </ol>
        Generates concrete <em>Things to Add</em>, <em>Things to Remove</em>, and optimizes weak bullets using Google's XYZ formula: <em>"Accomplished [X] as measured by [Y], by doing [Z]"</em>.</p>
    </div>
    <div class="file-box">
        <div class="file-name">backend/app/services/coding_profiles.py & api/profiles.py</div>
        <p><strong>What it does:</strong> Uses asynchronous <code>httpx.AsyncClient</code>:
        <ul>
            <li><strong>GitHub:</strong> Queries <code>https://api.github.com/users/{handle}</code> and <code>/repos</code> to fetch public repo counts, stargazers, and primary languages.</li>
            <li><strong>LeetCode:</strong> Queries LeetCode's public GraphQL endpoint (<code>https://leetcode.com/graphql</code>) with the <code>matchedUser</code> query to retrieve solved problem counts categorized into Easy, Medium, and Hard.</li>
            <li><strong>DSA Readiness Index:</strong> Computes a 0–100 score: <code>Readiness = (Easy * 0.15 + Medium * 0.55 + Hard * 0.30) / TargetThreshold * 70 + GitHubActivity * 30</code>.</li>
        </ul></p>
    </div>
    <div class="file-box">
        <div class="file-name">frontend/resume-review.html, coding.html, js/resume-review.js, js/coding.js</div>
        <p><strong>What it does:</strong> <code>resume-review.html</code> renders the 0-100 gauge, 4 score breakdown progress bars, addition/removal pill tags, and before/after bullet comparison cards. <code>coding.html</code> renders dual profile inputs, SVG readiness meters, LeetCode Easy/Med/Hard breakdown bars, and interview recommendations.</p>
    </div>

    <div class="qa-box">
        <strong>Expected Teacher Questions for Member 2:</strong><br/>
        <strong>Q: How do you extract LeetCode data if there is no official REST API?</strong><br/>
        <em>Answer:</em> In <code>coding_profiles.py</code>, we send an asynchronous GraphQL <code>POST</code> request to <code>https://leetcode.com/graphql</code> with the query <code>getUserProfile($username)</code>. It queries LeetCode's public schema to return <code>submitStats.acSubmissionNum</code>, giving exact counts of solved Easy, Medium, and Hard problems without requiring user passwords.<br/>
        <strong>Q: Explain the Google XYZ resume bullet formula.</strong><br/>
        <em>Answer:</em> In <code>resume_advisor.py</code>, weak bullets like <em>"Worked on database speed"</em> lack metrics and context. We detect the missing metric and transform it to: <em>"Accomplished 40% reduction in database query latency [X] as measured by Datadog APM [Y], by implementing Redis caching and compound indexing [Z]"</em>.
    </div>

    <div class="member-header">MEMBER 3: Skill Taxonomy, Gap Analysis & Job Market Analytics</div>
    <p><strong>Primary Focus:</strong> Skill ontology matching, role requirement benchmarks, traditional vs emerging roles, and cross-role co-occurrence analytics.</p>

    <h3>Files to Read & Master:</h3>
    <div class="file-box">
        <div class="file-name">backend/app/services/skill_extractor.py & skill_analyzer.py</div>
        <p><strong>What it does:</strong> <code>skill_extractor.py</code> normalizes text and matches against canonical skills using word-boundary regular expressions (e.g. <code>\bReact\b</code>). It uses <code>skill_aliases.json</code> so that "Postgres" maps to "PostgreSQL" and "K8s" maps to "Kubernetes". <code>skill_analyzer.py</code> calculates match percentages against target roles: <code>Coverage = (matched_core * 2 + matched_secondary) / (total_core * 2 + total_secondary)</code>.</p>
    </div>
    <div class="file-box">
        <div class="file-name">backend/app/services/role_discovery.py & job_market_analytics.py</div>
        <p><strong>What it does:</strong> <code>role_discovery.py</code> manages 10 traditional and emerging roles stored in <code>role_profiles.json</code> (including <em>Harness Engineer</em>, <em>Forward Deployed Engineer</em>, and <em>Agentic AI Engineer</em>). <code>job_market_analytics.py</code> aggregates skill frequencies across all roles and computes co-occurrence pairs (e.g. Python + FastAPI appears in 60% of backend roles).</p>
    </div>
    <div class="file-box">
        <div class="file-name">frontend/analytics.html, roles.html, js/analytics.js, js/roles.js</div>
        <p><strong>What it does:</strong> <code>analytics.html</code> renders interactive market demand bar charts, high-signal skill pairings, and empirical role benchmark tables. <code>roles.html</code> renders the 10 role cards, skill category filters (Languages, Frameworks, Cloud, ML), and the interactive dual-role comparison tool.</p>
    </div>

    <div class="qa-box">
        <strong>Expected Teacher Questions for Member 3:</strong><br/>
        <strong>Q: How do you prevent false-positive skill matches (e.g., matching the skill 'Go' inside the word 'Good')?</strong><br/>
        <em>Answer:</em> In <code>skill_extractor.py</code>, we compile regexes using word boundary anchors: <code>r'(?i)\b' + re.escape(alias) + r'\b'</code>. For short 1-2 letter acronyms like 'C' or 'R', we require strict uppercase tokenization or contextual word boundaries so plain English words never trigger false skill matches.<br/>
        <strong>Q: What is a Harness Engineer and why is it included?</strong><br/>
        <em>Answer:</em> Harness Engineers specialize in automated testing harnesses, CI/CD orchestration, load generation frameworks, and chaos engineering. They are crucial in modern platform engineering to ensure software reliability before deployment.
    </div>

    <div class="member-header">MEMBER 4: Roadmap Engine, Design System & DevOps Infrastructure</div>
    <p><strong>Primary Focus:</strong> DAG prerequisite resolution, 6-week milestone scheduling, Paper & Ink OKLCH design system, unified API client, and Docker containerization.</p>

    <h3>Files to Read & Master:</h3>
    <div class="file-box">
        <div class="file-name">backend/app/services/roadmap_generator.py & api/roadmap.py</div>
        <p><strong>What it does:</strong> Takes candidate skill gaps and constructs a personalized 6-week learning roadmap. Uses a Directed Acyclic Graph (DAG) topological dependency sort:
        <ul>
            <li><strong>Weeks 1–2 (Foundation):</strong> Core language prerequisites and fundamental concepts.</li>
            <li><strong>Weeks 3–4 (Core Frameworks):</strong> Application frameworks, databases, and API development.</li>
            <li><strong>Weeks 5–6 (System Integration & Capstone):</strong> Production deployment, CI/CD, and mock interview questions.</li>
        </ul>
        Stores weekly tasks in SQLite and tracks completion checkboxes via <code>models/progress.py</code>.</p>
    </div>
    <div class="file-box">
        <div class="file-name">frontend/css/variables.css, style.css, components.css, roadmap.css</div>
        <p><strong>What it does:</strong> The <em>Paper & Ink</em> design system. Uses modern CSS OKLCH color spaces (<code>--background: oklch(0.98 0.01 85)</code> for warm parchment and <code>--foreground: oklch(0.20 0.02 55)</code> for deep ink). Fully responsive layout with CSS Grid and Flexbox, custom typography hierarchy (Fraunces serif headings, Inter body, JetBrains Mono code).</p>
    </div>
    <div class="file-box">
        <div class="file-name">frontend/js/api.js, config.js, roadmap.js & Dockerfile</div>
        <p><strong>What it does:</strong> <code>api.js</code> is the centralized API client wrapping <code>fetch()</code> with automatic token injection and error handling. <code>Dockerfile</code> is a multi-stage production build using <code>python:3.13-slim</code>, exposing port 8000 with volume mount <code>/app/data</code> for persistent SQLite storage.</p>
    </div>

    <div class="qa-box">
        <strong>Expected Teacher Questions for Member 4:</strong><br/>
        <strong>Q: How does the roadmap generator decide the sequence of skills across the 6 weeks?</strong><br/>
        <em>Answer:</em> In <code>roadmap_generator.py</code>, skills have prerequisite relationships. You cannot learn FastAPI before Python, or Kubernetes before Docker. We perform topological dependency sorting to schedule prerequisites into Weeks 1–2, core frameworks into Weeks 3–4, and production capstone projects into Weeks 5–6.<br/>
        <strong>Q: Why did you build the frontend in Vanilla JS and CSS instead of React or Tailwind?</strong><br/>
        <em>Answer:</em> To achieve zero runtime overhead, instant page loads, and complete independence from complex build tooling (no Node.js/npm dependencies). Native HTML5/CSS3 with OKLCH design variables provides modern, high-fidelity design without framework bloat.
    </div>

    <h2>5. Oral Defense Strategy & Teacher Presentation Walkthrough</h2>
    <ol>
        <li><strong>Start with Live System Proof:</strong> Member 1 boots the server using <code>run.bat</code> and displays <code>http://127.0.0.1:8000/docs</code> and <code>/api/health</code>.</li>
        <li><strong>Pass the Baton:</strong>
            <ul>
                <li><strong>Member 1:</strong> Demonstrates landing page (<code>index.html</code>) and uploads a sample resume on <code>dashboard.html</code>.</li>
                <li><strong>Member 2:</strong> Shows the <code>resume-review.html</code> audit score and explains the LeetCode GraphQL fetcher on <code>coding.html</code>.</li>
                <li><strong>Member 3:</strong> Shows the market trend analytics on <code>analytics.html</code> and explains the role comparison on <code>roles.html</code>.</li>
                <li><strong>Member 4:</strong> Demonstrates the generated 6-week plan on <code>roadmap.html</code>, checks off a completed task, and explains the Docker architecture.</li>
            </ul>
        </li>
        <li><strong>Conclude with Test Suite:</strong> Run <code>python -m pytest tests -q</code> showing all <strong>172 passed tests in ~8 seconds</strong>.</li>
    </ol>
    """

    story = pymupdf.Story(html=html)
    writer = pymupdf.DocumentWriter(pdf_path)
    more = 1
    page_num = 1
    while more:
        device = writer.begin_page(pymupdf.Rect(0, 0, 595, 842))
        more, _ = story.place(pymupdf.Rect(32, 32, 563, 810))
        story.draw(device)
        writer.end_page()
        page_num += 1

    writer.close()
    print(f"Generated Team Guide PDF: {pdf_path} (Pages: {page_num - 1})")

if __name__ == "__main__":
    build_team_pdf()

