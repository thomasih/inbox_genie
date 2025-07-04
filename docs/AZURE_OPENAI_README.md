# Using Azure OpenAI (gpt-3.5-turbo) with InboxGenie

This guide explains how to use your Azure OpenAI deployment for email categorization, summarization, or any LLM-powered feature in InboxGenie.

---

## 1. Prerequisites
- Azure OpenAI resource deployed (see Azure Portal)
- gpt-3.5-turbo model deployed (deployment name: `gpt-35-turbo`)
- API key and endpoint from Azure Portal
- Python 3.8+

---

## 2. Install the SDK
```sh
pip install openai
```

---

## 3. Basic Usage Example
```python
import os
from openai import AzureOpenAI

endpoint = "https://thoma-mcomuluf-eastus2.cognitiveservices.azure.com/"
deployment = "gpt-35-turbo"  # Use your deployment name
subscription_key = "<your-api-key>"  # Get from Azure Portal
api_version = "2024-12-01-preview"  # Use the latest version from Azure docs

client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    api_key=subscription_key,
)

response = client.chat.completions.create(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Summarize this email: ..."}
    ],
    max_tokens=4096,
    temperature=0.2,
    model=deployment
)

print(response.choices[0].message.content)
```

---

## 4. Integration Tips
- Use the deployment name you chose in Azure (e.g., `gpt-35-turbo`).
- Use your endpoint and API key from the Azure Portal.
- For email categorization, send a prompt with a list of emails and request a strict JSON output for folder mapping.
- Set `temperature` low (e.g., 0.2) for more deterministic, structured output.

---

## 5. Example Prompt for Email Grouping
```
Group the following emails into logical folders. Output ONLY a single valid JSON object in the format: {"Travel": ["id1", "id2"], "Finance": ["id3"]}. Do not include any explanation, extra text, markdown, or code block. Use only the provided email IDs.\n

ID: 123
Subject: Flight to Paris
Snippet: Your flight to Paris is confirmed.
From: Air France <info@airfrance.com>

ID: 456
Subject: Invoice for May
Snippet: Your May invoice is attached.
From: Acme Corp <billing@acme.com>

Now group the emails. Output ONLY the JSON object.
```

---

## 6. Cost Management
- Set up cost alerts in the Azure Portal to avoid unexpected charges.
- gpt-3.5-turbo is very affordable for most use cases.

---

## 7. Troubleshooting
- If you get a model version retirement warning, edit your deployment and select the latest available version.
- If you get authentication errors, double-check your API key and endpoint.
- For more, see the [Azure OpenAI documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/).

---

## 8. References
- [Azure OpenAI Python SDK Docs](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [Azure OpenAI Quickstart](https://learn.microsoft.com/en-us/azure/ai-services/openai/quickstart)
- [Azure OpenAI Model Versioning](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models)

---
