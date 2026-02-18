# -*- coding: utf-8 -*-
"""
TURKPATENT API Core Module

Handles reCAPTCHA token resolution via capsolver, API calls to
turkpatent.gov.tr/api/research, and in-memory caching.
"""

import asyncio
import hashlib
import json
import os
import sys
from typing import Any, Optional

import httpx
from cachetools import TTLCache

# --- Configuration ---

CAPSOLVER_API_KEY = os.getenv("CAPSOLVER_API_KEY", "")
CAPSOLVER_CREATE_TASK_URL = "https://api.capsolver.com/createTask"
CAPSOLVER_GET_RESULT_URL = "https://api.capsolver.com/getTaskResult"

RECAPTCHA_SITE_KEY = "6LcsCTYhAAAAAJBX4xh-BMzLJfwxfhri7KJPAxn3"
RECAPTCHA_PAGE_URL = "https://www.turkpatent.gov.tr/arastirma-yap"

API_URL = "https://www.turkpatent.gov.tr/api/research"
HEADERS = {
    "Content-Type": "application/json",
    "Origin": "https://www.turkpatent.gov.tr",
    "Referer": "https://www.turkpatent.gov.tr/arastirma-yap",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
}

# --- Caching ---

search_cache: TTLCache = TTLCache(maxsize=100, ttl=600)      # 10 min
detail_cache: TTLCache = TTLCache(maxsize=500, ttl=3600)      # 1 hour


def _cache_key(type_: str, params: dict, next_: int, limit: int) -> str:
    """Generate a deterministic cache key from request parameters."""
    raw = json.dumps({"type": type_, "params": params, "next": next_, "limit": limit}, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


# --- reCAPTCHA Token Resolution ---

async def get_recaptcha_token() -> str:
    """Solve reCAPTCHA v3 via capsolver API (action: research_form)."""
    if not CAPSOLVER_API_KEY:
        raise RuntimeError("CAPSOLVER_API_KEY environment variable is not set")

    async with httpx.AsyncClient(timeout=120) as client:
        # Create task — reCAPTCHA v3 with action
        create_payload = {
            "clientKey": CAPSOLVER_API_KEY,
            "task": {
                "type": "ReCaptchaV3TaskProxyLess",
                "websiteURL": RECAPTCHA_PAGE_URL,
                "websiteKey": RECAPTCHA_SITE_KEY,
                "pageAction": "research_form",
                "minScore": 0.9,
            },
        }
        resp = await client.post(CAPSOLVER_CREATE_TASK_URL, json=create_payload)
        result = resp.json()

        if result.get("errorId") != 0:
            raise RuntimeError(f"Capsolver create task error: {result.get('errorDescription', result)}")

        task_id = result.get("taskId")
        print(f"Capsolver task created: {task_id}", file=sys.stderr)

        # Poll for result
        for _ in range(60):
            await asyncio.sleep(2)
            get_payload = {"clientKey": CAPSOLVER_API_KEY, "taskId": task_id}
            resp = await client.post(CAPSOLVER_GET_RESULT_URL, json=get_payload)
            result = resp.json()

            if result.get("status") == "ready":
                token = result.get("solution", {}).get("gRecaptchaResponse")
                if token:
                    print("Capsolver token received.", file=sys.stderr)
                    return token
                raise RuntimeError("Capsolver returned ready but no token")

            if result.get("status") == "failed":
                raise RuntimeError(f"Capsolver task failed: {result.get('errorDescription', result)}")

        raise RuntimeError("Capsolver timeout waiting for token")


# --- API Client ---

async def call_research_api(
    type_: str,
    params: dict,
    next_: int = 0,
    limit: int = 20,
    order: Optional[dict] = None,
    max_retries: int = 5,
) -> dict:
    """Call turkpatent.gov.tr/api/research with reCAPTCHA token.

    Retries with a fresh token on INVALID_CREDENTIALS (v3 score too low).
    """
    last_error = None

    for attempt in range(1, max_retries + 1):
        token = await get_recaptcha_token()

        body = {
            "type": type_,
            "params": params,
            "next": next_,
            "limit": limit,
            "order": order,
            "token": token,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(API_URL, json=body, headers=HEADERS)

            if response.status_code == 500:
                data = response.json()
                error_code = data.get("error", {}).get("code", "")
                if error_code == "INVALID_CREDENTIALS" and attempt < max_retries:
                    print(f"INVALID_CREDENTIALS (attempt {attempt}/{max_retries}), retrying with new token...", file=sys.stderr)
                    last_error = data
                    await asyncio.sleep(1)
                    continue
                response.raise_for_status()

            response.raise_for_status()
            data = response.json()

            if not data.get("success"):
                raise RuntimeError(f"API returned success=false: {data}")

            return data

    raise RuntimeError(f"API failed after {max_retries} retries: {last_error}")


# --- Trademark Functions ---

SEARCH_TEXT_OPTION_MAP = {
    "contains": "isContains",
    "startsWith": "isStartWith",
    "equals": "isEqual",
}

HOLDER_NAME_OPTION_MAP = {
    "startsWith": "isStartWith",
    "equals": "isEqual",
}


async def search_trademarks_core(
    trademark_name: str = "",
    name_operator: str = "contains",
    holder_name: Optional[str] = None,
    holder_name_operator: str = "startsWith",
    nice_classes: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    """Search trademarks on TURKPATENT."""
    cache_key = _cache_key("trademark", {
        "searchText": trademark_name,
        "searchTextOption": name_operator,
        "holderName": holder_name or "",
        "holderNameOption": holder_name_operator,
        "niceClasses": nice_classes or "",
    }, offset, limit)

    cached = search_cache.get(cache_key)
    if cached is not None:
        print("Cache HIT: trademark search", file=sys.stderr)
        return cached

    params = {
        "markTypeId": "0",
        "searchText": trademark_name,
        "searchTextOption": SEARCH_TEXT_OPTION_MAP.get(name_operator, "isContains"),
        "holderName": holder_name or "",
        "holderNameOption": HOLDER_NAME_OPTION_MAP.get(holder_name_operator, "isStartWith"),
        "bulletinNo": "",
        "gazzetteNo": "",
        "clientNo": "",
        "niceClasses": nice_classes or "",
        "niceClassesFor": "selected" if nice_classes else "all",
    }

    data = await call_research_api("trademark", params, next_=offset, limit=limit)
    payload = data.get("payload", {})
    result = _format_search_result(payload)
    search_cache[cache_key] = result
    return result


async def get_trademark_detail_core(application_number: str) -> dict:
    """Get trademark details by application number."""
    cache_key = f"trademark-file:{application_number}"
    cached = detail_cache.get(cache_key)
    if cached is not None:
        print("Cache HIT: trademark detail", file=sys.stderr)
        return cached

    params = {"id": application_number}
    data = await call_research_api("trademark-file", params)
    payload = data.get("payload", {})
    item = payload.get("item", {})

    # Strip base64 image data to reduce token usage
    mark_info = item.get("markInformation", {})
    if mark_info.get("figure"):
        mark_info["figure"] = "[base64 image data omitted]"

    detail_cache[cache_key] = item
    return item


# --- Patent Functions ---

async def search_patents_core(
    title: str = "",
    abstract: Optional[str] = None,
    owner: Optional[str] = None,
    applicant: Optional[str] = None,
    application_number: Optional[str] = None,
    ipc_class: Optional[str] = None,
    cpc_class: Optional[str] = None,
    attorney: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    """Search patents on TURKPATENT."""
    params: dict[str, Any] = {
        "title": title,
        "abstract": abstract or "",
        "inventorName": owner or "",
        "applicantName": applicant or "",
        "applicationNumber": application_number or "",
        "epcApplicationNumber": "",
        "pctApplicationNumber": "",
        "epcPublicationNumber": "",
        "priorityNumber": "",
        "pctPublicationNumber": "",
        "ipcClass": ipc_class or "",
        "cpcClass": cpc_class or "",
        "publicationDate": "",
        "publicationEndDate": "",
        "attorney": attorney or "",
    }

    cache_key = _cache_key("patent", params, offset, limit)
    cached = search_cache.get(cache_key)
    if cached is not None:
        print("Cache HIT: patent search", file=sys.stderr)
        return cached

    data = await call_research_api("patent", params, next_=offset, limit=limit)
    payload = data.get("payload", {})
    result = _format_search_result(payload)
    search_cache[cache_key] = result
    return result


async def get_patent_detail_core(application_number: str) -> dict:
    """Get patent details by application number."""
    cache_key = f"patent-file:{application_number}"
    cached = detail_cache.get(cache_key)
    if cached is not None:
        print("Cache HIT: patent detail", file=sys.stderr)
        return cached

    params = {"id": application_number}
    data = await call_research_api("patent-file", params)
    payload = data.get("payload", {})
    item = payload.get("item", {})
    detail_cache[cache_key] = item
    return item


# --- Design Functions ---

async def search_designs_core(
    design_name: str = "",
    designer: Optional[str] = None,
    applicant: Optional[str] = None,
    registration_no: Optional[str] = None,
    locarno_class: Optional[str] = None,
    attorney: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    """Search designs on TURKPATENT."""
    params: dict[str, Any] = {
        "designName": design_name,
        "designerName": designer or "",
        "holderTitle": applicant or "",
        "registrationNo": registration_no or "",
        "locarno": locarno_class or "",
        "bulletin": "",
        "attorney": attorney or "",
    }

    cache_key = _cache_key("design", params, offset, limit)
    cached = search_cache.get(cache_key)
    if cached is not None:
        print("Cache HIT: design search", file=sys.stderr)
        return cached

    data = await call_research_api("design", params, next_=offset, limit=limit)
    payload = data.get("payload", {})
    result = _format_search_result(payload)
    search_cache[cache_key] = result
    return result


async def get_design_detail_core(file_id: str) -> dict:
    """Get design details by file ID (from search results)."""
    cache_key = f"design-file:{file_id}"
    cached = detail_cache.get(cache_key)
    if cached is not None:
        print("Cache HIT: design detail", file=sys.stderr)
        return cached

    params = {"id": file_id}
    data = await call_research_api("design-file", params)
    payload = data.get("payload", {})
    item = payload.get("item", {})
    detail_cache[cache_key] = item
    return item


# --- Helpers ---

def _format_search_result(payload: dict) -> dict:
    """Format API search payload into a clean result dict."""
    items = payload.get("items", [])
    # Strip base64 image data from search results to save tokens
    for item in items:
        if isinstance(item.get("image"), dict) and item["image"].get("data"):
            item["image"]["data"] = "[base64 omitted]"

    return {
        "total": payload.get("total", len(items)),
        "items": items,
        "fields": payload.get("fields", []),
    }
