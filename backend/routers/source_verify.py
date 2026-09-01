"""
Source Verification Router
API endpoints for source verification and provenance chain checking.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from backend.services.source_verification import get_source_verifier


router = APIRouter(prefix="/source-verify", tags=["Source Verification"])


class SourceVerifyRequest(BaseModel):
    url: str
    content_text: Optional[str] = None
    image_hash: Optional[str] = None


class ClaimCheckRequest(BaseModel):
    claim: str
    context: Optional[str] = None


@router.post("/verify")
async def verify_source(request: SourceVerifyRequest):
    """Verify a source URL for credibility and provenance."""
    verifier = get_source_verifier()
    
    try:
        result = verifier.verify_source(request.url)
        
        # Also check fact database if content provided
        if request.content_text:
            fact_checks = verifier.check_fact_database(request.content_text)
            result.fact_check_results = fact_checks
        
        # Also do reverse image search if hash provided
        if request.image_hash:
            reverse_results = verifier.reverse_image_search(request.image_hash)
            result.reverse_image_results = reverse_results
        
        return {
            "status": "success",
            "data": result.to_dict(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


@router.post("/check-claim")
async def check_claim(request: ClaimCheckRequest):
    """Check a claim against fact-check databases."""
    verifier = get_source_verifier()
    
    try:
        results = verifier.check_fact_database(request.claim)
        return {
            "status": "success",
            "data": {
                "claim": request.claim,
                "results": results,
                "database_count": len(verifier.FACT_CHECK_DB),
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Claim check failed: {str(e)}")


@router.post("/reverse-image")
async def reverse_image_search(image_hash: str):
    """Perform reverse image search."""
    verifier = get_source_verifier()
    
    try:
        results = verifier.reverse_image_search(image_hash)
        return {
            "status": "success",
            "data": {
                "image_hash": image_hash,
                "results": results,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reverse image search failed: {str(e)}")


@router.get("/provenance/{url:path}")
async def get_provenance_chain(url: str):
    """Get provenance chain for a URL."""
    verifier = get_source_verifier()
    
    try:
        chain = verifier.build_provenance_chain(url)
        return {
            "status": "success",
            "data": {
                "url": url,
                "chain": chain,
                "chain_length": len(chain),
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Provenance check failed: {str(e)}")
