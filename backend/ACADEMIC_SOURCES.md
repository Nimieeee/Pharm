# Additional Free/Open Academic Sources Integration Guide

PharmGPT now supports **8 academic databases** beyond PubMed and Tavily:

## ✅ Integrated Sources

### 0. **Google Scholar** (via SERP API) ⭐ NEW!
- **API**: `https://serpapi.com/search` (requires SERP_API_KEY)
- **Features**: Comprehensive academic coverage, citation counts, PDF links
- **Requires API key** (free tier: 100 searches/month, paid: $50/5000 searches)
- **Best for**: Broadest academic coverage, highly cited papers, interdisciplinary research

### 0.5. **DuckDuckGo** (Web Search) ⭐ NEW!
- **API**: HTML Scraping (No key needed)
- **Features**: General web search, privacy-focused
- **Best for**: General knowledge, government sites (FDA, NIH), news
### 1. **Semantic Scholar** (AI-Powered Academic Search)
- **API**: `https://api.semanticscholar.org/graph/v1`
- **Features**: Citation counts, AI-powered relevance, cross-disciplinary
- **No API key needed** for basic search
- **Best for**: Computer science, biomedicine, general research

### 2. **Crossref** (DOI Metadata)
- **API**: `https://api.crossref.org`
- **Features**: Comprehensive DOI metadata, publisher info
- **No API key needed**
- **Best for**: Published journal articles, citation data

### 3. **Europe PMC** (European Life Sciences)
- **API**: `https://www.ebi.ac.uk/europepmc/webservices/rest`
- **Features**: Life sciences focus, full-text search
- **No API key needed**
- **Best for**: Biomedical research, European publications

### 4. **arXiv** (Preprints - Physics, Math, CS, Bio)
- **API**: `http://export.arxiv.org/api/query`
- **Features**: Latest research, pre-publication
- **No API key needed**
- **Best for**: Cutting-edge research, preprints

### 5. **bioRxiv** (Life Sciences Preprints)
- **API**: `https://api.biorxiv.org/details`
- **Features**: Biology preprints before peer review
- **No API key needed**
- **Best for**: Latest biology research

### 6. **medRxiv** (Medical Preprints)
- **API**: `https://api.biorxiv.org/details` (same as bioRxiv)
- **Features**: Medical, clinical preprints
- **No API key needed**
- **Best for**: Clinical research, epidemiology

### 7. **DOAJ** (Directory of Open Access Journals)
- **API**: `https://doaj.org/api/search`
- **Features**: Only open access journals
- **No API key needed**
- **Best for**: Verified open access content

## Integration Benefits

### Coverage Expansion
- **Current**: ~35M PubMed articles
- **With new sources**: ~200M+ papers across all databases
- **Preprints**: Cutting-edge research months before publication

### Source Diversity
- **Multidisciplinary**: Semantic Scholar covers CS, physics, social sciences
- **Regional**: Europe PMC adds European perspective
- **Open Access**: DOAJ ensures free full-text access

### Quality Indicators
- **Citation counts** (Semantic Scholar)
- **Peer review status** (distinguish preprints from published)
- **Publisher information** (Crossref)

## Implementation Status

The academic sources module (`academic_sources.py`) provides:
- Individual API clients for each source
- Standardized output format
- Parallel search across all sources
- Error handling for API failures

## Next Steps

To activate these sources in deep research:
1. Import `search_all_sources` from `academic_sources.py`
2. Call it alongside existing PubMed search
3. Merge and deduplicate results
4. Rank by relevance and citation count

## Example Usage

```python
from app.services.academic_sources import search_all_sources

# Search query
query = "drosophila melanogaster Parkinson's disease"

# Get results from all 7 sources + PubMed
results_by_source = await search_all_sources(query, max_per_source=5)

# Results structure:
# {
#     "Semantic Scholar": [list of papers],
#     "Crossref": [list of papers],
#     "Europe PMC": [list of papers],
#     "arXiv": [list of papers],
#     "bioRxiv": [list of papers],
#     "medRxiv": [list of papers],
#     "DOAJ": [list of papers]
# }
```

## Performance

- **Parallel execution**: All 7 sources queried simultaneously
- **Timeout**: 30s per source
- **Resilience**: Failures in one source don't affect others
- **Total time**: ~5-10 seconds for comprehensive search

This dramatically improves research quality by accessing diverse, up-to-date academic content! 🚀
