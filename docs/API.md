# OmniMind API Design (Phase 2 & beyond)

## Authentication (Phase 2)
- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Authenticate user and return JWT
- `POST /api/auth/refresh` - Refresh JWT token
- `POST /api/auth/logout` - Logout user

## Digital Twin Profile (Phase 3)
- `GET /api/profile` - Get user profile
- `POST /api/profile/resume` - Upload and parse resume
- `POST /api/profile/skills` - Update skills

## Intelligence Engines (Phase 4-7)
- `POST /api/github/sync` - Sync GitHub profile
- `GET /api/github/report` - Get GitHub analysis report
- `GET /api/career/score` - Get ATS score for a specific job

## Interview Engine (Phase 8)
- `POST /api/interview/generate` - Generate mock interview questions
- `POST /api/interview/evaluate` - Evaluate answers and store history
