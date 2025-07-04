# Why Switch to a Cloud LLM for Email Categorisation

## Summary

This project originally explored three approaches for categorising and grouping emails:

1. **Traditional ML (clustering, embeddings, etc.)**
2. **Local LLM (running open-source models on local hardware)**
3. **Cloud LLM (OpenAI, Azure OpenAI, etc.)**

After experimentation, we are moving forward with a cloud LLM approach. Here’s why:

---

## Why Not Clustering/Embeddings?
- **Limited semantic understanding:** Clustering and embeddings (e.g., MiniLM, KMeans) can group emails by similarity, but they do not understand context, intent, or nuanced topics.
- **Poor folder naming:** Automatic folder naming with classic ML is unreliable and often produces generic or meaningless names.
- **Hard to tune:** Requires manual tuning of cluster count, feature engineering, and post-processing.
- **Not robust to real-world email diversity:** Fails on edge cases, mixed languages, or emails with little text.

## Why Not Local LLM?
- **Hardware limitations:** Even small models (e.g., TinyLlama, Phi-3-mini) are slow and memory-intensive on 8GB RAM, making real-time or batch processing impractical.
- **Inferior instruction following:** Local models are less reliable at following strict output formats (e.g., valid JSON) compared to cloud LLMs.
- **Maintenance overhead:** Requires managing model weights, dependencies, and updates locally.
- **No access to latest models:** Cloud LLMs are always up-to-date and more capable for structured tasks.

## Why Cloud LLM?
- **Superior accuracy:** Cloud LLMs (OpenAI, Azure OpenAI, etc.) provide best-in-class language understanding and instruction following.
- **Robust output:** They reliably produce valid JSON and handle edge cases, mixed languages, and complex instructions.
- **No local resource drain:** No need to download or run large models locally—frees up disk and RAM.
- **Easy to scale:** Cloud APIs can handle large volumes and concurrent users.
- **Lower maintenance:** No need to manage model files, dependencies, or hardware upgrades.

---

## Migration Plan
- All local LLM, clustering, and embedding code is being removed from the backend.
- The backend will call a cloud LLM API for categorisation and folder naming in the next phase.
- The current step is to ensure raw email extraction and frontend display works perfectly before reintroducing LLM-based grouping.

---

**This approach ensures the best user experience, reliability, and maintainability for the project.**
