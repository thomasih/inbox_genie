# InboxGenie

## What
A Python FastAPI + React app that uses Microsoft Graph & OpenAI to auto-classify and sort a user’s mailbox.

## Quickstart

1. Clone repo  
2. `cd mailbox-cleanser/backend`  
3. `python3 -m venv venv && source venv/bin/activate`  
4. `pip install -r requirements.txt`  
5. Copy `.env.example` → `.env`, fill in Azure AD & OpenAI creds  
6. `uvicorn app.main:app --reload`  
7. In another shell, `cd ../frontend && npm install && npm run dev`  

## Deployment
- Backend: Docker → Azure App Service or AKS  
- Frontend: Static build → Azure Static Web Apps  
- Infra: `terraform apply`