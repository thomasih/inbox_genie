# InboxGenie

[![Build Status](https://img.shields.io/badge/build-pending-yellow.svg)]()

**InboxGenie** is a Dockerized FastAPI + React application that leverages Microsoft Graph and OpenAI to automatically classify and sort your emails into folders you define.

---

## 🚀 Features

- **OAuth2 authentication** via Microsoft MSAL  
- **Batch fetching** and operations on Outlook mailboxes  
- **AI-based classification** using OpenAI GPT models  
- **Configurable categories** and folder mappings  
- **Action log** support for “undo” operations  
- **Modern React dashboard** with real-time status & controls  
- **Docker-ready** for easy deployment to Azure App Service, AKS, or Static Web Apps  

---

## 📦 Repository Structure

```
.
├── README.md
├── .env.example
├── docs/
│   ├── context.yaml
│   └── roadmap.yaml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   └── tests/
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   └── src/
├── alembic/
└── terraform/
```

---

## 🔧 Getting Started

### Prerequisites

- [Docker](https://www.docker.com/)  
- Azure account with **Microsoft Graph** permissions  
- OpenAI API key  

### Quickstart (Local)

1. **Clone & configure**  
   ```bash
   git clone https://github.com/your-org/inboxgenie.git
   cd inboxgenie
   cp .env.example .env
   # Edit .env with your Azure & OpenAI credentials
   ```

2. **Backend**  
   ```bash
   docker build -f backend/Dockerfile -t inboxgenie-backend .
   docker run --env-file .env -p 8000:8000 inboxgenie-backend
   ```

3. **Frontend**  
   ```bash
   docker build -f frontend/Dockerfile -t inboxgenie-frontend .
   docker run -p 3000:80 inboxgenie-frontend
   ```

   - Access the dashboard at `http://localhost:3000`  
   - API docs at `http://localhost:8000/docs`  

---

## 🧪 Testing

- **Backend tests**  
  ```bash
  cd backend
  pytest
  ```

- **Frontend tests**  
  ```bash
  cd frontend
  npm install
  npm test
  ```

---

## 🛣️ Roadmap

See [`docs/roadmap.yaml`](./docs/roadmap.yaml) for our detailed future plan.

---

## ⛅ Deployment

- **Backend** → Azure App Service / AKS via Docker  
  ```bash
  az webapp up --sku F1 --name inboxgenie-backend --deployment-container-image-name your-registry/inboxgenie-backend
  ```

- **Frontend** → Azure Static Web Apps or any static host  

- **Infra as Code** → Terraform in `terraform/` (coming soon)  

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Please open a PR against `main`.

1. Fork the repo  
2. Create a feature branch (`git checkout -b feat/my-feature`)  
3. Commit your changes  
4. Push to your fork and open a PR  

---