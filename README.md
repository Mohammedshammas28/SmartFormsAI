# SmartForms AI
**AI-Powered Form Builder & Response Intelligence Platform**
<img width="1898" height="857" alt="image" src="https://github.com/user-attachments/assets/8713885f-0009-4db4-8620-ee2c4491437c" />


## Quick Start

### 1. Install dependencies
```bash
pip install flask
```

### 2. Run the application
```bash
python app.py
```

### 3. Open in browser
```
http://localhost:5000
```

---

## Setup

### Requirements
- Python 3.9+
- Flask 3.x
- SQLite (built-in)
- A free Groq API key for AI features

### Get a Groq API Key (Free)
1. Go to [console.groq.com](https://console.groq.com)
2. Sign up for a free account
3. Generate an API key
4. In SmartForms AI, go to **Settings → AI Configuration** and paste your key

---

## Features

### 🏗️ Form Builder
- 11 question types: Short Text, Long Text, Email, Phone, Multiple Choice, Checkboxes, Dropdown, Rating, Yes/No, Date, File Upload
- Drag-and-drop reordering
- Inline question editing
- Required field toggle
- Live preview

### 🤖 AI Form Generator
- Describe what you need in plain English
- AI generates a complete form with appropriate question types
- Example: *"Create an employee satisfaction survey with questions about work environment and career growth"*

### 📊 Analytics Dashboard
- Response trend charts (30-day)
- Form popularity rankings
- Activity by day of week
- Hourly response heatmap

### 🔍 AI Response Analysis
- Executive summary
- Sentiment analysis
- Key insights & patterns
- Actionable recommendations

### 🔗 Public Form Sharing
- Unique shareable links (`/f/your-form-slug`)
- Mobile-responsive submission page
- Real-time progress bar
- Custom success messages

### 📥 Response Management
- View all responses in a table
- Click through to individual response detail
- Export to CSV
- Delete individual responses

---

## Project Structure
```
smartforms/
├── app.py              # Flask app factory & entry point
├── database.py         # SQLite init & connection helpers
├── helpers.py          # Auth decorators, password hashing, utils
├── ai_service.py       # Groq API integration (Llama 3)
├── requirements.txt
├── routes/
│   ├── auth.py         # Login, register, logout
│   ├── dashboard.py    # Main dashboard
│   ├── forms.py        # Form CRUD + question API
│   ├── responses.py    # View, export, AI analysis
│   ├── analytics.py    # Charts data
│   ├── settings.py     # Profile, password, API key
│   ├── public.py       # Public form submission
│   └── api.py          # Misc API endpoints
├── templates/
│   ├── base.html       # Sidebar layout
│   ├── auth/           # Login, register
│   ├── dashboard/      # Dashboard page
│   ├── forms/          # Form list, builder, new, edit
│   ├── responses/      # Response list, detail view
│   ├── analytics/      # Analytics charts
│   ├── settings/       # Settings page
│   └── public/         # Public form, success, 404
├── static/
│   ├── css/
│   │   ├── main.css    # Design system + all components
│   │   ├── auth.css    # Auth page styles
│   │   └── public.css  # Public form styles
│   ├── js/
│   │   ├── app.js      # Sidebar, toasts, micro-interactions
│   │   ├── builder.js  # Drag-drop, question CRUD, AI gen
│   │   └── public.js   # Progress bar, ratings, submit
│   └── uploads/        # File upload storage
└── instance/
    └── smartforms.db   # SQLite database (auto-created)
```

---

## Database Schema
- **users** — accounts with password hash + Groq API key
- **forms** — form metadata, slug, publish status
- **questions** — typed questions with options JSON
- **responses** — submission records
- **answers** — individual field responses
- **ai_reports** — saved AI analysis results

---

## Design System
- Apple / Notion / Linear-inspired aesthetics
- CSS custom properties (design tokens)
- Glassmorphism effects
- Subtle 3D card tilt micro-interactions
- Responsive: desktop, tablet, mobile
- `Plus Jakarta Sans` typography

---

## Security
- PBKDF2-SHA256 password hashing (100,000 iterations)
- Session-based authentication
- Per-user data isolation
- SQL injection protection via parameterized queries
- CSRF-safe form handling
- Secure file upload with randomized filenames
