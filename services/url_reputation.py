"""
URL Reputation Service - Phase 4 Enhancement
Real-time URL analysis using Google Safe Browsing and VirusTotal APIs

This service provides threat intelligence for URLs found in emails,
enhancing the detection capabilities beyond rule-based analysis.
"""

import os
import json
import time
import hashlib
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

import requests
from urllib.parse import urlparse, quote_plus

logger = logging.getLogger(__name__)

@dataclass
class URLAnalysisResult:
    """Structured result from URL reputation analysis"""
    url: str
    is_malicious: bool
    threat_types: List[str]
    confidence_score: float  # 0.0 to 1.0
    source: str  # 'google_safe_browsing', 'virustotal', 'cached'
    analysis_time: datetime
    details: Dict = None

class URLReputationError(Exception):
    """Custom exception for URL reputation analysis errors"""
    pass

class URLReputationService:
    """
    Service for real-time URL reputation checking using multiple threat intelligence sources
    Implements caching and rate limiting for production use
    """
    
    def __init__(self):
        self.gsb_api_key = os.getenv('GOOGLE_SAFE_BROWSING_API_KEY')
        self.vt_api_key = os.getenv('VIRUSTOTAL_API_KEY')
        self.cache_duration_hours = int(os.getenv('URL_CACHE_DURATION_HOURS', '24'))
        self.rate_limit_delay = float(os.getenv('URL_API_DELAY_SECONDS', '1.0'))
        self.last_api_call = 0
        
        # API endpoints
        self.gsb_endpoint = "https://safebrowsing.googleapis.com/v4/threatMatches:find"
        self.vt_endpoint = "https://www.virustotal.com/vtapi/v2/url/report"
        
        logger.info(f"URLReputationService initialized with GSB: {'✓' if self.gsb_api_key else '✗'}, VT: {'✓' if self.vt_api_key else '✗'}")

    def _rate_limit(self):
        """Implement rate limiting between API calls"""
        elapsed = time.time() - self.last_api_call
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_api_call = time.time()

    def _get_url_hash(self, url: str) -> str:
        """Generate consistent hash for URL caching"""
        return hashlib.sha256(url.encode()).hexdigest()

    def _is_cache_valid(self, cached_result: Dict) -> bool:
        """Check if cached result is still valid"""
        if not cached_result or 'analysis_time' not in cached_result:
            return False
        
        cache_time = datetime.fromisoformat(cached_result['analysis_time'])
        expiry_time = cache_time + timedelta(hours=self.cache_duration_hours)
        return datetime.now() < expiry_time

    def _check_google_safe_browsing(self, urls: List[str]) -> Dict[str, URLAnalysisResult]:
        """
        Check URLs against Google Safe Browsing API
        Supports batch checking for efficiency
        """
        if not self.gsb_api_key:
            logger.warning("Google Safe Browsing API key not configured")
            return {}

        self._rate_limit()
        
        request_body = {
            "client": {
                "clientId": "phishing-detector",
                "clientVersion": "1.0.1"
            },
            "threatInfo": {
                "threatTypes": [
                    "MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", 
                    "POTENTIALLY_HARMFUL_APPLICATION"
                ],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": url} for url in urls]
            }
        }

        try:
            response = requests.post(
                f"{self.gsb_endpoint}?key={self.gsb_api_key}",
                headers={'Content-Type': 'application/json'},
                json=request_body,
                timeout=10
            )
            response.raise_for_status()
            
            result_data = response.json()
            results = {}
            
            # Parse matches (threats found)
            matches = result_data.get('matches', [])
            threatened_urls = {match['threat']['url'] for match in matches}
            
            for url in urls:
                if url in threatened_urls:
                    # Find threat details for this URL
                    url_matches = [m for m in matches if m['threat']['url'] == url]
                    threat_types = [m['threatType'] for m in url_matches]
                    
                    results[url] = URLAnalysisResult(
                        url=url,
                        is_malicious=True,
                        threat_types=threat_types,
                        confidence_score=0.9,  # High confidence for GSB matches
                        source='google_safe_browsing',
                        analysis_time=datetime.now(),
                        details={'matches': url_matches}
                    )
                else:
                    # Clean URL
                    results[url] = URLAnalysisResult(
                        url=url,
                        is_malicious=False,
                        threat_types=[],
                        confidence_score=0.8,  # Good confidence for clean URLs
                        source='google_safe_browsing',
                        analysis_time=datetime.now()
                    )
            
            return results
            
        except requests.RequestException as e:
            logger.error(f"Google Safe Browsing API error: {e}")
            raise URLReputationError(f"GSB API request failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in GSB analysis: {e}")
            raise URLReputationError(f"GSB analysis failed: {e}")

    def _check_virustotal(self, url: str) -> URLAnalysisResult:
        """
        Check single URL against VirusTotal API
        VirusTotal has stricter rate limits, so we check one at a time
        """
        if not self.vt_api_key:
            logger.warning("VirusTotal API key not configured")
            return None

        self._rate_limit()

        params = {
            'apikey': self.vt_api_key,
            'resource': url,
            'scan': '1'  # Request scan if not in database
        }

        try:
            response = requests.get(self.vt_endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            result_data = response.json()
            
            if result_data['response_code'] == 1:
                # URL found in database
                positives = result_data.get('positives', 0)
                total = result_data.get('total', 0)
                
                if total > 0:
                    malicious_ratio = positives / total
                    is_malicious = malicious_ratio > 0.1  # 10% threshold
                    confidence = min(0.9, 0.5 + malicious_ratio)  # Scale confidence
                    
                    return URLAnalysisResult(
                        url=url,
                        is_malicious=is_malicious,
                        threat_types=['MALWARE' if is_malicious else 'CLEAN'],
                        confidence_score=confidence,
                        source='virustotal',
                        analysis_time=datetime.now(),
                        details={
                            'positives': positives,
                            'total': total,
                            'scan_date': result_data.get('scan_date')
                        }
                    )
            
            # URL not found or no data
            return URLAnalysisResult(
                url=url,
                is_malicious=False,
                threat_types=[],
                confidence_score=0.5,  # Lower confidence for unknown URLs
                source='virustotal',
                analysis_time=datetime.now(),
                details={'response_code': result_data.get('response_code')}
            )
            
        except requests.RequestException as e:
            logger.error(f"VirusTotal API error: {e}")
            raise URLReputationError(f"VT API request failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in VT analysis: {e}")
            raise URLReputationError(f"VT analysis failed: {e}")

    def analyze_urls(self, urls: List[str], use_cache: bool = True) -> Dict[str, URLAnalysisResult]:
        """
        Analyze multiple URLs using available threat intelligence sources
        
        Args:
            urls: List of URLs to analyze
            use_cache: Whether to use cached results
            
        Returns:
            Dict mapping URL to analysis results
        """
        if not urls:
            return {}

        results = {}
        uncached_urls = []

        # Check cache first if enabled
        if use_cache:
            # Import cache manager here to avoid circular imports
            try:
                from services.cache_manager import CacheManager
                cache = CacheManager()
                
                for url in urls:
                    cache_key = f"url_reputation:{self._get_url_hash(url)}"
                    cached_result = cache.get(cache_key)
                    
                    if cached_result and self._is_cache_valid(cached_result):
                        results[url] = URLAnalysisResult(**cached_result)
                        logger.debug(f"Using cached result for {url}")
                    else:
                        uncached_urls.append(url)
            except ImportError:
                logger.warning("Cache manager not available, proceeding without cache")
                uncached_urls = urls
        else:
            uncached_urls = urls

        if not uncached_urls:
            return results

        # Analyze uncached URLs
        try:
            # Try Google Safe Browsing first (supports batch)
            if self.gsb_api_key:
                gsb_results = self._check_google_safe_browsing(uncached_urls)
                for url, result in gsb_results.items():
                    results[url] = result
                    
                    # Cache result if available
                    if use_cache:
                        try:
                            cache_key = f"url_reputation:{self._get_url_hash(url)}"
                            cache.set(cache_key, result.__dict__, 
                                    expire_hours=self.cache_duration_hours)
                        except:
                            pass  # Cache errors shouldn't break analysis

            # For URLs not analyzed by GSB, try VirusTotal
            remaining_urls = [url for url in uncached_urls if url not in results]
            
            if remaining_urls and self.vt_api_key:
                for url in remaining_urls[:5]:  # Limit VT calls due to rate limits
                    try:
                        vt_result = self._check_virustotal(url)
                        if vt_result:
                            results[url] = vt_result
                            
                            # Cache result
                            if use_cache:
                                try:
                                    cache_key = f"url_reputation:{self._get_url_hash(url)}"
                                    cache.set(cache_key, vt_result.__dict__,
                                            expire_hours=self.cache_duration_hours)
                                except:
                                    pass
                    except URLReputationError:
                        continue  # Try next URL

            # For any remaining URLs, create default results
            for url in uncached_urls:
                if url not in results:
                    results[url] = URLAnalysisResult(
                        url=url,
                        is_malicious=False,
                        threat_types=[],
                        confidence_score=0.3,  # Low confidence for unanalyzed URLs
                        source='default',
                        analysis_time=datetime.now(),
                        details={'reason': 'no_api_keys_configured'}
                    )

        except Exception as e:
            logger.error(f"URL reputation analysis error: {e}")
            # Return default results for all URLs
            for url in uncached_urls:
                if url not in results:
                    results[url] = URLAnalysisResult(
                        url=url,
                        is_malicious=False,
                        threat_types=[],
                        confidence_score=0.1,  # Very low confidence due to error
                        source='error',
                        analysis_time=datetime.now(),
                        details={'error': str(e)}
                    )

        return results

    def analyze_single_url(self, url: str, use_cache: bool = True) -> URLAnalysisResult:
        """
        Convenience method to analyze a single URL
        
        Args:
            url: URL to analyze
            use_cache: Whether to use cached results
            
        Returns:
            URLAnalysisResult for the URL
        """
        results = self.analyze_urls([url], use_cache)
        return results.get(url)

    def get_reputation_summary(self, results: Dict[str, URLAnalysisResult]) -> Dict:
        """
        Generate summary statistics from URL reputation analysis
        
        Args:
            results: Dict of URL analysis results
            
        Returns:
            Dict containing summary statistics
        """
        if not results:
            return {
                'total_urls': 0,
                'malicious_urls': 0,
                'clean_urls': 0,
                'unknown_urls': 0,
                'average_confidence': 0.0,
                'threat_types': [],
                'sources_used': []
            }

        malicious_count = sum(1 for r in results.values() if r.is_malicious)
        clean_count = len(results) - malicious_count
        
        # Collect all threat types
        all_threat_types = set()
        for result in results.values():
            all_threat_types.update(result.threat_types)
        
        # Collect sources used
        sources_used = list(set(r.source for r in results.values()))
        
        # Calculate average confidence
        avg_confidence = sum(r.confidence_score for r in results.values()) / len(results)

        return {
            'total_urls': len(results),
            'malicious_urls': malicious_count,
            'clean_urls': clean_count,
            'average_confidence': round(avg_confidence, 3),
            'threat_types': list(all_threat_types),
            'sources_used': sources_used,
            'highest_risk_urls': [
                {'url': r.url, 'confidence': r.confidence_score, 'threats': r.threat_types}
                for r in sorted(results.values(), key=lambda x: x.confidence_score, reverse=True)
                if r.is_malicious
            ][:5]  # Top 5 most dangerous URLs
        }


# Global service instance
_url_reputation_service = None

def get_url_reputation_service() -> URLReputationService:
    """
    Get global URL reputation service instance
    Implements singleton pattern for efficient resource usage
    """
    global _url_reputation_service
    if _url_reputation_service is None:
        _url_reputation_service = URLReputationService()
    return _url_reputation_service


def reset_url_reputation_service():
    """Reset the global service instance (mainly for testing)"""
    global _url_reputation_service
    _url_reputation_service = None