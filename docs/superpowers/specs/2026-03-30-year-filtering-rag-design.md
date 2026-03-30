# Year-Filtering for RAG System Design

**Date**: 2026-03-30
**Status**: Approved
**Problem**: Year-specific queries ("top countries 2023") return non-matching years (2024/2025) because FAISS semantic search ignores metadata.
**Solution**: Post-filtering with year extraction from query.

---

## 1. Architecture Overview

### Goal
Improve year-specific queries while preserving accuracy for conceptual queries.

### Design Decision
**Explicit-year filtering only**. Year filter is applied ONLY when:
- Query contains explicit 4-digit year(s) (2021 onwards) — detected via regex
- Filter uses OR logic for multiple years ("compare 2021 and 2024" → both years)

### Flow
```
Query → Year Detection → Branch:
  │
  ├─ Years detected → Post-filter search (k×3 candidates, filter to detected years, return top_k)
  │
  └─ No year → Pure semantic search (current behavior)
```

### Why Post-Filtering
- No re-architecture of ingestion required
- Simple to implement (one new method)
- FAISS doesn't support native metadata filtering
- Works with existing vector store

---

## 2. Components

### 2.1 Year Extraction Utility

Location: `vector-db/vector_store.py`

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

### 2.2 Post-Filter Search Method

Location: `vector-db/vector_store.py` (add to VectorStore class)

```python
def similarity_search_with_filter(
    self, 
    query: str, 
    k: int = 5,
    filters: Dict[str, Any] = None
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

### 2.3 RAG Service Integration

Location: `api/rag_service.py` (modify `_retrieve_documents`)

```python
from vector_store import extract_years_from_query

async def _retrieve_documents(self, query: str, top_k: int) -> List[Dict[str, Any]]:
    """Retrieve documents with optional year filtering"""
    
    # Extract years from query
    years = extract_years_from_query(query)
    
    filters = None
    if years:
        filters = {"year": years}  # List for OR logic
        logger.info(f"Detected years {years} in query, applying filter")
    
    # Search with optional filter
    search_results = self.vector_store.similarity_search_with_filter(
        query, k=top_k, filters=filters
    )
    
    # Format results (existing logic)
    docs = []
    for result in search_results:
        doc = {
            "content": result.get("content", ""),
            "metadata": result.get("metadata", {}),
            "similarity_score": result.get("similarity_score", 0.0),
        }
        docs.append(doc)
    
    return docs
```

---

## 3. Data Flow

### Year-Specific Query Flow
```
User Query: "top countries 2023"
    │
    ▼
RAGService.query() receives query
    │
    ▼
extract_years_from_query()
    │ Regex: \b(202[1-9]|20[3-9]\d)\b
    │ Returns: [2023]
    │
    ▼
filters = {"year": [2023]}
    │
    ▼
similarity_search_with_filter(query, k=5, filters)
    │ Get 15 candidates (k×3)
    │ Filter by year == 2023
    │ Return top 5 matches
    │
    ▼
Results: Only 2023-Chandler-Good-Government-Index-Report.pdf
```

### Multi-Year Query Flow
```
User Query: "compare 2021 and 2024"
    │
    ▼
extract_years_from_query() → [2021, 2024]
    │
    ▼
filters = {"year": [2021, 2024]}  # OR logic
    │
    ▼
similarity_search_with_filter(query, k=5, filters)
    │ Filter by year IN [2021, 2024]
    │ Return top 5 (mixed 2021 and 2024 sources)
    │
    ▼
Results: 2021 and 2024 PDFs only
```

### Non-Year Query Flow
```
User Query: "What is CGGI's core belief?"
    │
    ▼
extract_years_from_query() → [] (empty)
    │
    ▼
filters = None
    │
    ▼
similarity_search(query, k=5)
    │ Pure semantic search
    │
    ▼
Results: Best matches from any year (2021-2025)
```

---

## 4. Error Handling & Edge Cases

| Scenario | Behavior |
|----------|----------|
| Year detected but no matching docs | Fallback to unfiltered results (avoid empty response) |
| Multiple years in query | Uses OR logic (match ANY of detected years) |
| Year in wrong context ("report number 2021") | Matches anyway — user intent assumed |
| No year in query | Pure semantic search (current behavior) |
| Future year with no docs ("top countries 2030") | Fallback to unfiltered results |

---

## 5. Testing Plan

### Test Cases

| Test | Query | Expected Result |
|------|-------|-----------------|
| Single year filtering | "top countries 2023" | Only 2023 PDF sources |
| Multi-year filtering | "compare 2021 and 2024" | Only 2021 and 2024 PDF sources |
| Future year | "top countries 2030" | Fallback (mixed years) |
| No year | "What is CGGI's core belief?" | Mixed year sources, semantic ranking |
| Year with typo | "top countrie 2023" | Still filters (regex matches year) |
| Conceptual question | "How many indicators does CGGI use?" | Best semantic matches, any year |

### Verification Commands

```bash
# Test single year filtering
curl -X POST http://localhost:9000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "top countries 2023", "top_k": 5}'
# Expected: sources all contain "2023-Chandler-Good-Government-Index-Report.pdf"

# Test multi-year filtering
curl -X POST http://localhost:9000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "compare 2021 and 2024", "top_k": 5}'
# Expected: sources contain only 2021 or 2024 PDFs

# Test non-year query
curl -X POST http://localhost:9000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is CGGI's core belief?", "top_k": 5}'
# Expected: sources from mixed years based on semantic relevance
```

---

## 6. Files to Modify

| File | Changes |
|------|---------|
| `vector-db/vector_store.py` | Add `extract_years_from_query()` function and `similarity_search_with_filter()` method |
| `api/rag_service.py` | Modify `_retrieve_documents()` to use year extraction and filtered search |

---

## 7. Limitations

- Post-filtering retrieves k×3 candidates; if year match rate is very low, may return fewer than k results
- Regex detects years 2021-2099; won't detect years before 2021
- Year extraction is regex-based, not LLM-based (simpler but less intelligent for complex temporal expressions)

---

## 8. Future Enhancements (Not in Scope)

- LLM-based query parsing for complex temporal expressions ("recent", "last 5 years")
- Recency boost for non-temporal queries (prefer 2025 results)
- Hybrid search (BM25 + semantic) for better year keyword matching