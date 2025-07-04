import os
import hashlib
import json
from openai import AzureOpenAI
import logging
import demjson3

USE_LLM = os.getenv("USE_LLM", "false").lower() == "true"

# Simple in-memory cache for dev; replace with Redis or DB in prod
_llm_cache = {}

logger = logging.getLogger("inboxgenie.llm_categorizer")

CATEGORIES = [
    "Finance", "News", "Technology", "Shopping", "Education", "Travel", "Utilities", "Transportation",
    "Music", "Real Estate", "Events", "Entertainment", "Job Opportunities"
]

class LLMEmailCategorizer:
    def __init__(self):
        self.use_llm = USE_LLM
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
        if self.use_llm:
            self.client = AzureOpenAI(
                api_version=self.api_version,
                azure_endpoint=self.endpoint,
                api_key=self.api_key,
            )

    def categorize_emails(self, emails):
        # Limit batch size for LLM
        BATCH_SIZE = 5  # Lowered to avoid LLM output truncation
        all_folder_maps = []
        errors = []
        for i in range(0, len(emails), BATCH_SIZE):
            batch = emails[i:i+BATCH_SIZE]
            # Use a hash of the input as cache key
            input_str = json.dumps(batch, sort_keys=True)
            cache_key = hashlib.sha256(input_str.encode()).hexdigest()
            if cache_key in _llm_cache:
                logger.info(f"LLM cache hit for key {cache_key}")
                all_folder_maps.append(_llm_cache[cache_key])
                continue
            if not self.use_llm:
                # Return a mock result for dev/testing
                logger.info("LLM mock mode: returning fake folder grouping.")
                all_folder_maps.append({CATEGORIES[0]: [e["id"] for e in batch]})
                continue
            # Build prompt with fixed categories
            prompt = (
                f"Group the following emails into the following categories: {', '.join(CATEGORIES)}, or 'Other' if none fit. "
                "Assign each email to exactly one of these categories. Do not invent new categories. "
                "If an email does not fit any category, put it in 'Other'. "
                "Do not omit or repeat any IDs. Do not create duplicate folders. "
                "Each email ID must appear in one and only one category. "
                "Output ONLY a single valid JSON object in the format: {\"Category 1\": [\"id1\", \"id2\"], ... , \"Other\": [\"id4\"]}. "
                "Do not include any explanation, extra text, markdown, or code block. Use only the provided email IDs. "
                "At the end of the JSON object, add a key 'Summary' with the total number of unique IDs assigned. "
                "Do not include any trailing commas before closing brackets or braces. "
                "Double-check that your output is valid JSON and does not contain any syntax errors. "
                "Do not add a comma before the closing brace or bracket. "
            )
            for email in batch:
                sender = email['sender']
                sender_str = f"{sender.get('name','')} <{sender.get('email','')}>" if sender.get('email') else sender.get('name','')
                prompt += f"\nID: {email['id']}\nSubject: {email['subject']}\nFrom: {sender_str}\n"
            prompt += "\nNow group the emails. Output ONLY the JSON object."
            # Call Azure OpenAI
            try:
                response = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1024,
                    temperature=0.2,
                    model=self.deployment
                )
                text = response.choices[0].message.content
                logger.info(f"Raw LLM output: {text}")
                # Try to extract JSON
                json_start = text.find('{')
                json_end = text.rfind('}') + 1
                json_str = text[json_start:json_end]
                # Pre-repair: insert missing comma before 'Summary' if needed
                import re
                json_str = re.sub(r'(\])\s*"Summary"', r'\1, "Summary"', json_str)
                # Check for truncation
                if not json_str.strip().endswith('}'):  # Incomplete JSON
                    logger.error(f"LLM output appears truncated or incomplete. Output: {text}")
                    errors.append(f"Batch {i//BATCH_SIZE+1}: LLM output was truncated. Try with fewer emails or reduce batch size.")
                    continue
                # --- REPLACE CUSTOM JSON REPAIR WITH demjson3 ---
                try:
                    folder_map = json.loads(json_str)
                except Exception as e_json:
                    logger.warning(f"Standard json.loads failed, trying demjson3: {e_json}")
                    try:
                        folder_map = demjson3.decode(json_str)
                    except Exception as e_demjson:
                        logger.error(f"demjson3 also failed. Raw output: {text}\nError: {e_demjson}")
                        errors.append(f"Batch {i//BATCH_SIZE+1}: LLM output could not be parsed. Try with fewer emails.")
                        continue
                # Remove 'Summary' key if present
                folder_map.pop('Summary', None)
                # Only keep allowed categories (plus 'Other' if present)
                filtered_map = {cat: folder_map[cat] for cat in CATEGORIES if cat in folder_map}
                if 'Other' in folder_map:
                    filtered_map['Other'] = folder_map['Other']
                # Deduplicate: ensure each ID appears in only one folder
                seen = set()
                deduped = {}
                for folder, ids in filtered_map.items():
                    unique_ids = []
                    for eid in ids:
                        if eid not in seen:
                            unique_ids.append(eid)
                            seen.add(eid)
                    deduped[folder] = unique_ids
                # Find missing IDs
                input_ids = set(e['id'] for e in batch)
                output_ids = set()
                for ids in deduped.values():
                    output_ids.update(ids)
                missing = input_ids - output_ids
                repeated = [eid for eid in output_ids if list(output_ids).count(eid) > 1]
                if missing:
                    logger.warning(f"LLM output missing {len(missing)} IDs: {missing}")
                if repeated:
                    logger.warning(f"LLM output has repeated IDs: {repeated}")
                # Add any missing IDs to 'Other'
                if missing:
                    deduped.setdefault('Other', []).extend(list(missing))
                _llm_cache[cache_key] = deduped
                all_folder_maps.append(deduped)
            except Exception as e:
                logger.error(f"Failed to parse LLM output as JSON: {e}. Output was: {text if 'text' in locals() else ''}")
                errors.append(f"Batch {i//BATCH_SIZE+1}: LLM output could not be parsed. Try with fewer emails.")
        # Merge all folder maps
        final_map = {}
        for folder_map in all_folder_maps:
            for folder, ids in folder_map.items():
                final_map.setdefault(folder, []).extend(ids)
        # Final deduplication across batches
        seen = set()
        deduped_final = {}
        for folder, ids in final_map.items():
            unique_ids = []
            for eid in ids:
                if eid not in seen:
                    unique_ids.append(eid)
                    seen.add(eid)
            deduped_final[folder] = unique_ids
        # Add any missing IDs to 'Other'
        input_ids = set(e['id'] for e in emails)
        output_ids = set()
        for ids in deduped_final.values():
            output_ids.update(ids)
        missing = input_ids - output_ids
        if missing:
            logger.warning(f"Final output missing {len(missing)} IDs: {missing}")
            deduped_final.setdefault('Other', []).extend(list(missing))
        # Only keep allowed categories (plus 'Other' if present)
        filtered_final = {cat: deduped_final[cat] for cat in CATEGORIES if cat in deduped_final and deduped_final[cat]}
        if 'Other' in deduped_final and deduped_final['Other']:
            filtered_final['Other'] = deduped_final['Other']
        # Ensure 'Other' is last in the output
        if 'Other' in filtered_final:
            other_ids = filtered_final.pop('Other')
            filtered_final['Other'] = other_ids
        if errors:
            logger.error(f"LLM errors: {errors}")
            return {"error": errors[0]}
        _llm_cache[hashlib.sha256(json.dumps(emails, sort_keys=True).encode()).hexdigest()] = filtered_final
        return filtered_final
