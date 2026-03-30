# Year-Filtering for RAG System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add year-filtering to RAG system so queries like "top countries 2023" return only 2023 documents, while conceptual queries remain unfiltered.

**Architecture:** Post-filtering approach — extract year(s) from query via regex, retrieve k×3 candidates, filter by year metadata, return top k. Falls back to unfiltered if no matches.

**Tech Stack:** Python, FAISS, FastAPI, regex

---

## File Structure

| File | Purpose |
|------|---------|
| `vector-db/vector_store.py` | Add `extract_years_from_query()` and `similarity_search_with_filter()` |
| `api/rag_service.py` | Modify `_retrieve_documents()` to use year extraction and filtering |

---

## Task 1: Add Year Extraction Function

**Files:**
- Modify: `vector-db/vector_store.py` (add function at top of file after imports)

- [ ] **Step 1: Add import and function**

Add after line 8 (`import os`):

```python
import re
from typing import List, Optional


def extract_years_from_query(query: str) -> List[int]:
    """Extract all explicit 4-digit years from query (2021 onwards)
    
    Examples:
        "top countries 2023" → [2023]
        "compare 2021 and 2024" → [2021, 2024]
        "What is CGGI?" → []
    """
    # Matches 2021-2029, 2030-2099 (future reports)
    matches = re.findall(r'\b(202[1-9]|20[3-9]\d)\b', query)
    return [int(m) for m in matches]
```

- [ ] **Step 2: Test year extraction manually**

Run:
```bash
cd D:\dev\CGGI\cggi-rag-system
python -c "
import sys
sys.path.insert(0, 'vector-db')
from vector_store import extract_years_from_query

# Test cases
tests = [
    ('top countries 2023', [2023]),
    ('compare 2021 and 2024', [2021, 2024]),
    ('What is CGGI?', []),
    ('report from 2030', [2030]),
    ('data for 2020', []),  # Before 2021, should not match
]

for query, expected in tests:
    result = extract_years_from_query(query)
    status = '✓' if result == expected else '✗'
    print(f'{status} \"{query}\" → {result} (expected {expected})')
"
```

Expected output:
```
✓ "top countries 2023" → [2023] (expected [2023])
✓ "compare 2021 and 2024" → [2021, 2024] (expected [2021, 2024])
✓ "What is CGGI?" → [] (expected [])
✓ "report from 2030" → [2030] (expected [2030])
✓ "data for 2020" → [] (expected [])
```

---

## Task 2: Add similarity_search_with_filter Method

**Files:**
- Modify: `vector-db/vector_store.py` (add method to VectorStore class)

- [ ] **Step 1: Add method after similarity_search method**

Add after line 93 (after the `return results` of `similarity_search`):

```python
    def similarity_search_with_filter(
        self,
        query: str,
        k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search with metadata filtering applied post-retrieval
        
        Args:
            query: Search query text
            k: Number of results to return
            filters: Dict of metadata filters, e.g., {"year": [2021, 2024]}
                     Uses OR logic for list values (match ANY)
        
        Returns:
            Filtered results if matches found, else unfiltered fallback
        """
        
        # Get more candidates for filtering (k × 3 ensures enough matches)
        candidates = self.similarity_search(query, k=k * 3)
        
        if not filters:
            return candidates[:k]
        
        # Filter by metadata with OR logic for list values
        filtered = []
        for doc in candidates:
            match = True
            for key, value in filters.items():
                doc_value = doc.get("metadata", {}).get(key)
                
                # OR logic: if value is list, match ANY
                if isinstance(value, list):
                    if doc_value not in value:
                        match = False
                        break
                else:
                    if doc_value != value:
                        match = False
                        break
            
            if match:
                filtered.append(doc)
        
        # Fallback: if filtering returns empty, return unfiltered results
        return filtered[:k] if filtered else candidates[:k]
```

- [ ] **Step 2: Test filter method with loaded vector store**

Run:
```bash
cd D:\dev\CGGI\cggi-rag-system
python -c "
import sys
sys.path.insert(0, 'vector-db')
from vector_store import VectorStore

vs = VectorStore()
vs.load('vector_store.pkl')

# Test 1: No filter (should return results from any year)
results = vs.similarity_search_with_filter('top countries', k=3, filters=None)
print(f'No filter: {len(results)} results')
for r in results:
    print(f'  - Year: {r[\"metadata\"].get(\"year\")}, Source: {r[\"metadata\"].get(\"source_file\", \"unknown\")[:30]}...')

# Test 2: Filter by year 2023
results = vs.similarity_search_with_filter('top countries', k=3, filters={'year': [2023]})
print(f'\\nFilter year=[2023]: {len(results)} results')
for r in results:
    print(f'  - Year: {r[\"metadata\"].get(\"year\")}, Source: {r[\"metadata\"].get(\"source_file\", \"unknown\")[:30]}...')

# Test 3: Filter by multiple years
results = vs.similarity_search_with_filter('top countries', k=5, filters={'year': [2021, 2024]})
print(f'\\nFilter year=[2021, 2024]: {len(results)} results')
for r in results:
    print(f'  - Year: {r[\"metadata\"].get(\"year\")}, Source: {r[\"metadata\"].get(\"source_file\", \"unknown\")[:30]}...')

# Test 4: Filter by future year (fallback expected)
results = vs.similarity_search_with_filter('top countries', k=3, filters={'year': [2030]})
print(f'\\nFilter year=[2030] (fallback): {len(results)} results')
for r in results:
    print(f'  - Year: {r[\"metadata\"].get(\"year\")}, Source: {r[\"metadata\"].get(\"source_file\", \"unknown\")[:30]}...')
"
```

Expected output:
- No filter: 3 results with mixed years
- Filter year=[2023]: 3 results all with year=2023
- Filter year=[2021, 2024]: results with year=2021 or 2024 only
- Filter year=[2030]: fallback results (mixed years, since no 2030 docs exist)

---

## Task 3: Integrate Year Filtering in RAG Service

**Files:**
- Modify: `api/rag_service.py` (modify `_retrieve_documents` method)

- [ ] **Step 1: Update import statement**

Change line 59 from:
```python
try:
    from vector_store import VectorStore
```

To:
```python
try:
    from vector_store import VectorStore, extract_years_from_query
```

- [ ] **Step 2: Replace _retrieve_documents method**

Replace the entire `_retrieve_documents` method (lines 196-264) with:

```python
    async def _retrieve_documents(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents from the vector store with optional year filtering
        """
        if not hasattr(self, "vector_store") or self.vector_store is None:
            logger.error("Vector store not initialized")
            # Fallback to placeholder behavior
            docs = []
            for i in range(top_k):
                docs.append(
                    {
                        "content": f"Placeholder content for query '{query}', result #{i + 1}",
                        "metadata": {
                            "source_file": f"placeholder_source_{i}.pdf",
                            "year": 2025,
                            "type": "cggi_report",
                            "pillar": "all",
                            "similarity_score": 0.5,
                        },
                    }
                )
            return docs

        try:
            # Extract years from query for filtering
            years = extract_years_from_query(query)
            
            filters = None
            if years:
                filters = {"year": years}  # List for OR logic
                logger.info(f"Detected years {years} in query, applying filter")
            
            # Perform similarity search with optional filter
            search_results = self.vector_store.similarity_search_with_filter(
                query, k=top_k, filters=filters
            )

            logger.info(
                f"Found {len(search_results)} results from vector store for query: {query}"
            )

            # Convert vector store results to required format
            docs = []
            for result in search_results:
                # Extract content, metadata, and similarity score
                content = result.get("content", "")
                metadata = result.get("metadata", {})
                similarity_score = result.get("similarity_score", 0.0)

                doc = {
                    "content": content,
                    "metadata": metadata,
                    "similarity_score": similarity_score,
                }
                docs.append(doc)

            logger.info(f"Returning {len(docs)} documents for query")
            return docs

        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}")
            logger.exception("Full exception traceback:")
            # Fallback to placeholder behavior if vector store fails
            docs = []
            for i in range(top_k):
                docs.append(
                    {
                        "content": f"Placeholder content for query '{query}', result #{i + 1}",
                        "metadata": {
                            "source_file": f"placeholder_source_{i}.pdf",
                            "year": 2025,
                            "type": "cggi_report",
                            "pillar": "all",
                            "similarity_score": 0.5,
                        },
                    }
                )
            return docs
```

- [ ] **Step 3: Remove duplicate dead code**

Delete lines 266-393 (the dead code after the return statement - duplicate try/except blocks that are unreachable).

---

## Task 4: Rebuild and Test API

**Files:**
- No file changes - container rebuild and testing

- [ ] **Step 1: Rebuild API container**

Run:
```bash
cd D:\dev\CGGI\cggi-rag-system
docker-compose build --no-cache api
docker-compose up -d --no-deps api
```

- [ ] **Step 2: Wait for container to start and check logs**

Run:
```bash
sleep 60 && docker logs cggi-api 2>&1 | tail -10
```

Expected output:
```
INFO:vector_store:Vector store loaded from vector_store.pkl with 3375 vectors
INFO:rag_service:Vector store loaded from vector_store.pkl
INFO:rag_service:RAG Service initialized with vector store integration
```

- [ ] **Step 3: Test single year filtering**

Run:
```bash
curl -s -X POST http://localhost:9000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "top countries 2023", "top_k": 5}' | python -c "
import sys, json
d = json.load(sys.stdin)
print('Query: top countries 2023')
print(f'Confidence: {d[\"confidence_score\"]:.2f}')
print('Sources:')
for doc in d['documents']:
    year = doc['metadata'].get('year', 'N/A')
    source = doc['source'][:40] if doc['source'] else 'N/A'
    print(f'  - Year: {year}, Source: {source}...')
print('\\nAll sources are 2023:', all(doc['metadata'].get('year') == 2023 for doc in d['documents']))
"
```

Expected: All sources should have year=2023

- [ ] **Step 4: Test multi-year filtering**

Run:
```bash
curl -s -X POST http://localhost:9000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "compare 2021 and 2024 rankings", "top_k": 5}' | python -c "
import sys, json
d = json.load(sys.stdin)
print('Query: compare 2021 and 2024 rankings')
print(f'Confidence: {d[\"confidence_score\"]:.2f}')
print('Sources:')
for doc in d['documents']:
    year = doc['metadata'].get('year', 'N/A')
    source = doc['source'][:40] if doc['source'] else 'N/A'
    print(f'  - Year: {year}, Source: {source}...')
years = [doc['metadata'].get('year') for doc in d['documents']]
print(f'\\nAll years are 2021 or 2024: {all(y in [2021, 2024] for y in years)}')
"
```

Expected: All sources should have year=2021 or year=2024

- [ ] **Step 5: Test non-year query (no filtering)**

Run:
```bash
curl -s -X POST http://localhost:9000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the core belief of CGGI?", "top_k": 5}' | python -c "
import sys, json
d = json.load(sys.stdin)
print('Query: What is the core belief of CGGI?')
print(f'Confidence: {d[\"confidence_score\"]:.2f}')
print('Sources (should be mixed years):')
for doc in d['documents']:
    year = doc['metadata'].get('year', 'N/A')
    source = doc['source'][:40] if doc['source'] else 'N/A'
    print(f'  - Year: {year}, Source: {source}...')
years = set(doc['metadata'].get('year') for doc in d['documents'])
print(f'\\nUnique years found: {years}')
"
```

Expected: Mixed years based on semantic relevance (not filtered)

---

## Task 5: Verify Logs Show Year Detection

**Files:**
- No file changes - log verification

- [ ] **Step 1: Check API logs for year detection**

Run:
```bash
docker logs cggi-api 2>&1 | grep -i "detected year\|applying filter"
```

Expected output (after running year-specific queries):
```
INFO:rag_service:Detected years [2023] in query, applying filter
INFO:rag_service:Detected years [2021, 2024] in query, applying filter
```

- [ ] **Step 2: Final integration test**

Run all three test queries in sequence:
```bash
echo "=== Test 1: Single year ===" && \
curl -s -X POST http://localhost:9000/query -H "Content-Type: application/json" -d '{"query": "top countries 2023", "top_k": 3}' | python -c "import sys,json; d=json.load(sys.stdin); years=[doc['metadata'].get('year') for doc in d['documents']]; print(f'Years: {years}'); print(f'PASS: {all(y==2023 for y in years)}')" && \
echo "" && \
echo "=== Test 2: Multi-year ===" && \
curl -s -X POST http://localhost:9000/query -H "Content-Type: application/json" -d '{"query": "compare 2021 and 2024", "top_k": 5}' | python -c "import sys,json; d=json.load(sys.stdin); years=[doc['metadata'].get('year') for doc in d['documents']]; print(f'Years: {years}'); print(f'PASS: {all(y in [2021,2024] for y in years)}')" && \
echo "" && \
echo "=== Test 3: No year ===" && \
curl -s -X POST http://localhost:9000/query -H "Content-Type: application/json" -d '{"query": "What is CGGI core belief?", "top_k": 3}' | python -c "import sys,json; d=json.load(sys.stdin); years=[doc['metadata'].get('year') for doc in d['documents']]; print(f'Years: {years}'); print(f'PASS: {len(set(years)) > 1} (mixed years expected)')"
```

Expected:
```
=== Test 1: Single year ===
Years: [2023, 2023, 2023]
PASS: True

=== Test 2: Multi-year ===
Years: [2021, 2024, 2021, 2024, 2024]
PASS: True

=== Test 3: No year ===
Years: [2024, 2025, 2023]
PASS: True (mixed years expected)
```

---

## Summary

| Task | Description | Status |
|------|-------------|--------|
| 1 | Add `extract_years_from_query()` function | - [ ] |
| 2 | Add `similarity_search_with_filter()` method | - [ ] |
| 3 | Integrate year filtering in RAG service | - [ ] |
| 4 | Rebuild and test API | - [ ] |
| 5 | Verify logs and final integration test | - [ ] |