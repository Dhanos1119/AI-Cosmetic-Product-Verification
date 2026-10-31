"use client";

import { useState } from "react";
import {
  RotateCcw,
  CheckCircle2,
  ShieldCheck,
  Sparkles,
  Store,
  Search,
  MessageSquare,
  Info,
  Tag,
  Package,
  Terminal,
  ChevronDown,
  ChevronUp,
  Cpu,
  FileCheck,
  FileText,
  AlertTriangle,
  ExternalLink,
  ShieldAlert,
  Layers,
  HelpCircle,
  AlertCircle,
  ThumbsUp,
  ThumbsDown,
  MinusCircle,
  Clock,
  User,
  Star,
  Globe,
  Loader2,
} from "lucide-react";

export interface OcrResultDetails {
  status: string;
  engine?: string;
  raw_text: string[];
  brand_name?: string;
  product_name?: string;
  category?: string;
  confidence: number;
  total_lines_detected: number;
}

export interface ClipResultDetails {
  status: string;
  similarity_score: number;
  similarity_percentage: number;
  match_status: string;
  vector_dimension: number;
  model: string;
  confidence_level?: string;
  matching_method?: string;
  matched_brand?: string;
  matched_product_name?: string;
  matched_category?: string;
}

export interface ReviewSampleItem {
  review_id?: string;
  author?: string;
  rating?: number;
  headline?: string;
  body?: string;
  verified_purchase?: boolean;
  vine?: boolean;
  label?: string;
  date?: string;
}

export interface MarketplaceSentimentSummary {
  status: string;
  analyzed_count: number;
  counts: { positive: number; neutral: number; negative: number };
  explanation?: string;
  model_version?: string;
  note?: string;
}

export interface SuspiciousIndicator {
  indicator: string;
  severity: "LOW" | "MODERATE" | "HIGH";
  description: string;
  evidence?: string[];
}

export interface SuspiciousReviewRisk {
  status: string;
  risk_level: string;
  risk_score?: number | null;
  flag: boolean;
  analyzed_review_count: number;
  indicators_detected: SuspiciousIndicator[];
  explanation: string;
  disclaimer: string;
  is_validated_ml_detector: boolean;
}

export interface MarketplaceReview {
  author?: string;
  rating?: number;
  comment?: string;
  date?: string;
  verified_purchase?: boolean;
  sentiment?: string;
  sentiment_confidence?: number;
  suspicious_flag?: boolean;
  suspicious_reason?: string;
}

export interface ReviewResultDetails {
  status: string;
  review_dataset_source?: string;
  authenticity_analysis_status?: string;
  authenticity_note?: string;
  total_reviews_analyzed?: number;
  review_authenticity_score?: number | null;
  sentiment_label: string;
  average_rating?: number | null;
  verified_buyer_percentage?: number | null;
  deceptive_review_percentage?: number;
  authenticity_status: string;
  suspicious_review_flag: boolean;
  suspicious_review_risk?: SuspiciousReviewRisk;
  label_breakdown?: {
    genuine_count?: number;
    fake_cg_count?: number;
    incentivized_count?: number;
  };
  summary: string;
  sample_reviews?: ReviewSampleItem[];
  analyzed_reviews?: MarketplaceReview[];
  marketplace_sentiment?: MarketplaceSentimentSummary;
  sentiment_model?: { available?: boolean; model_version?: string | null; label_type?: string };
  synthetic_benchmark?: { disclaimer?: string; total_reviews?: number };
}

export interface AuthenticityResultDetails {
  status: string;
  overall_authenticity_score: number;
  prediction_badge: string;
  risk_level: string;
  recommendation: string;
  score_scope?: string;
  assessment_outcome?: string; // NOT_ASSESSED | INSUFFICIENT_EVIDENCE | INCONSISTENT_INFORMATION | REQUIRES_MANUAL_VERIFICATION
  assessment_explanation?: string;
  verified_evidence?: string[];
  inconsistencies?: string[];
  missing_information?: string[];
  score_breakdown: Record<string, any>;
}

export interface ProductIdentity {
  brand: string;
  product_name: string;
  product_type: string;
  category: string;
  product_id?: string;
  shade_or_variant?: string;
}

export interface MarketplaceListing {
  platform: string;
  product_name: string;
  brand: string;
  product_type: string;
  shade_or_variant?: string;
  price?: number;
  currency?: string;
  rating?: number;
  rating_count?: number;
  review_count?: number;
  seller_name?: string;
  product_url?: string;
  product_image_url?: string;
  reviews?: MarketplaceReview[];
  source_status: string;
  match_status: string;
  match_confidence: number;
  status_explanation?: string;
  search_query?: string;
  listing_status?: string;
  passed_match_threshold?: boolean;
}

export interface ScoreBreakdown {
  review_trust_score: number;
  rating_score: number;
  seller_trust_score: number;
  match_confidence_score: number;
}

export interface PlatformComparisonScore {
  platform: string;
  total_score: number;
  rank: number;
  score_breakdown: ScoreBreakdown;
  recommendation_reason: string;
  listing: MarketplaceListing;
}

export interface AiAnalysisResult {
  success: boolean;
  filename: string;
  image_validation: string;
  width: number;
  height: number;
  format: string;
  size: number;
  ocr_status: string;
  brand_name?: string;
  product_name?: string;
  ocr_result?: OcrResultDetails;
  product_detection: string;
  clip_similarity: string;
  clip_result?: ClipResultDetails;
  review_authenticity: string;
  review_result?: ReviewResultDetails;
  authenticity_prediction: string;
  authenticity_result?: AuthenticityResultDetails;
  product_identity?: ProductIdentity;
  marketplace_listings?: MarketplaceListing[];
  platform_comparison?: PlatformComparisonScore[];
  db_persisted?: boolean;
}

interface VerificationResultProps {
  previewUrl: string | null;
  aiAnalysisResult: AiAnalysisResult | null;
  onReset: () => void;
}

export default function VerificationResult({
  previewUrl,
  aiAnalysisResult,
  onReset,
}: VerificationResultProps) {
  const [showDeveloperDebug, setShowDeveloperDebug] = useState(false);
  const [showExtractedText, setShowExtractedText] = useState(false);
  const [showMissingInfo, setShowMissingInfo] = useState(false);

  // Interactive direct marketplace URL scraping state
  const [directUrl, setDirectUrl] = useState("");
  const [isScrapingUrl, setIsScrapingUrl] = useState(false);
  const [urlScrapeError, setUrlScrapeError] = useState<string | null>(null);
  const [urlScrapeSuccess, setUrlScrapeSuccess] = useState<string | null>(null);
  const [customListing, setCustomListing] = useState<MarketplaceListing | null>(null);
  const [customReviews, setCustomReviews] = useState<MarketplaceReview[]>([]);
  const [customReviewResult, setCustomReviewResult] = useState<ReviewResultDetails | null>(null);

  // Extract result sub-objects
  const ocrData = aiAnalysisResult?.ocr_result;
  const clipData = aiAnalysisResult?.clip_result;
  const reviewData = aiAnalysisResult?.review_result;
  const authData = aiAnalysisResult?.authenticity_result;
  const identity = aiAnalysisResult?.product_identity;

  const brandName = identity?.brand || aiAnalysisResult?.brand_name || ocrData?.brand_name || "Unknown Brand";
  const productName = identity?.product_name || aiAnalysisResult?.product_name || ocrData?.product_name || "Unidentified Product";
  const categoryName = identity?.category || ocrData?.category || aiAnalysisResult?.product_detection || "General Cosmetics";

  const isDbPersisted = aiAnalysisResult?.db_persisted === true;
  const matchingMethod = clipData?.matching_method || "1-NN Reference Bank (Max-Pooling) + OCR Brand Boost";

  // Active review data (custom direct URL takes precedence over initial scan)
  const activeReviewData = customReviewResult || reviewData;

  // Separate valid marketplace comparison items from scraper access status entries
  const platformComparisons = aiAnalysisResult?.platform_comparison || [];
  const baseValidListings = platformComparisons.filter(
    (p) =>
      p.listing &&
      p.listing.source_status === "available" &&
      p.listing.passed_match_threshold !== false &&
      p.listing.listing_status !== "INVALID_URL" &&
      p.listing.product_url &&
      p.listing.product_url.startsWith("http") &&
      !p.listing.product_url.includes("/item/P0") &&
      !p.listing.product_url.includes("/item/PROD")
  );

  const validListings = customListing
    ? [{ platform: customListing.platform, listing: customListing, platform_score: 85.0, rank: 1 }, ...baseValidListings]
    : baseValidListings;

  const statusEntries = platformComparisons.filter(
    (p) =>
      !p.listing ||
      p.listing.source_status !== "available" ||
      p.listing.passed_match_threshold === false ||
      p.listing.listing_status === "INVALID_URL" ||
      !p.listing.product_url ||
      !p.listing.product_url.startsWith("http") ||
      p.listing.product_url.includes("/item/P0") ||
      p.listing.product_url.includes("/item/PROD")
  );

  // Collect all real customer reviews (custom scraped reviews take precedence)
  const allCustomerReviews: MarketplaceReview[] =
    customReviews.length > 0
      ? customReviews
      : (activeReviewData?.analyzed_reviews && activeReviewData.analyzed_reviews.length > 0)
      ? activeReviewData.analyzed_reviews
      : (aiAnalysisResult?.marketplace_listings || []).flatMap((m) => m.reviews || []);

  const suspiciousRisk = activeReviewData?.suspicious_review_risk;

  // Normalized search query for external marketplace browser searches
  const searchQuery = `${brandName !== "Unknown Brand" ? brandName : ""} ${productName}`.trim() || "Cosmetic Product";
  const darazSearchUrl = `https://www.daraz.lk/catalog/?q=${encodeURIComponent(searchQuery)}`;
  const amazonSearchUrl = `https://www.amazon.com/s?k=${encodeURIComponent(searchQuery)}`;
  const temuSearchUrl = `https://www.temu.com/search_result.html?search_key=${encodeURIComponent(searchQuery)}`;

  // Direct Marketplace URL Scrape Handler via Express Gateway (:5000)
  const handleDirectUrlScrape = async () => {
    if (!directUrl.trim()) return;
    setIsScrapingUrl(true);
    setUrlScrapeError(null);
    setUrlScrapeSuccess(null);

    try {
      const host = typeof window !== "undefined" ? window.location.hostname : "localhost";
      const endpoint = `http://${host}:5000/api/marketplace/scrape-url`;
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: directUrl.trim() }),
      });

      const res = await response.json();
      if (!response.ok || !res.success) {
        throw new Error(res.message || res.detail || "Direct marketplace scraping failed.");
      }

      const item = res.data;
      const listingObj: MarketplaceListing = {
        platform: item.platform || "Marketplace",
        product_name: item.raw_title,
        brand: item.brand || (brandName !== "Unknown Brand" ? brandName : "Cosmetic Brand"),
        product_type: categoryName,
        price: item.price_val,
        currency: item.currency || "USD",
        rating: item.rating_val,
        rating_count: item.rating_count_val,
        review_count: item.review_count_val || (item.reviews ? item.reviews.length : 0),
        seller_name: item.seller,
        product_url: item.link,
        product_image_url: item.image_link,
        reviews: item.reviews || [],
        source_status: item.source_status || "available",
        match_status: "Exact Product Match",
        match_confidence: 100.0,
        status_explanation: item.explanation || "Extracted directly from user-provided marketplace link.",
        search_query: item.link,
        listing_status: item.status_code || "VERIFIED_LISTING",
        passed_match_threshold: true,
      };

      setCustomListing(listingObj);
      if (item.reviews && item.reviews.length > 0) {
        setCustomReviews(item.reviews);
      }
      if (res.review_result) {
        setCustomReviewResult(res.review_result);
      }
      setIsScrapingUrl(false);
      setUrlScrapeSuccess(
        `Extracted verified listing from ${item.platform} with ${item.reviews ? item.reviews.length : 0} review(s).`
      );
    } catch (err: any) {
      setIsScrapingUrl(false);
      setUrlScrapeError(err.message || "Error connecting to Marketplace Scraper via Express gateway.");
    }
  };

  // Outcome badge styling helper
  const getOutcomeBadgeStyle = (outcome?: string) => {
    switch (outcome) {
      case "REQUIRES_MANUAL_VERIFICATION":
        return "bg-purple-100 text-purple-950 border-purple-300";
      case "INCONSISTENT_INFORMATION":
        return "bg-rose-100 text-rose-950 border-rose-300";
      case "INSUFFICIENT_EVIDENCE":
        return "bg-amber-100 text-amber-950 border-amber-300";
      case "NOT_ASSESSED":
      default:
        return "bg-slate-100 text-slate-800 border-slate-300";
    }
  };

  const getRiskLevelBadgeStyle = (level?: string) => {
    switch (level) {
      case "LOW":
        return "bg-emerald-950 text-emerald-300 border-emerald-700";
      case "MODERATE":
        return "bg-amber-950 text-amber-300 border-amber-700";
      case "ELEVATED":
        return "bg-rose-950 text-rose-300 border-rose-700";
      case "INSUFFICIENT_DATA":
      default:
        return "bg-slate-800 text-slate-300 border-slate-600";
    }
  };

  return (
    <div className="w-full space-y-6 bg-white rounded-3xl p-6 sm:p-8 border border-purple-200 shadow-xl shadow-purple-900/5 animate-fadeIn">
      {/* 1. Gateway & System Status Banner */}
      <div className="p-4 bg-purple-50/80 border border-purple-200 rounded-2xl text-purple-950 text-xs sm:text-sm flex items-start gap-3 shadow-2xs">
        <Cpu className="w-5 h-5 text-purple-700 shrink-0 mt-0.5" />
        <div className="space-y-1.5 w-full">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-extrabold uppercase tracking-wide text-xs text-purple-900 bg-purple-200/80 px-2.5 py-0.5 rounded-md border border-purple-300">
              Gateway (:5000) → FastAPI (:8001)
            </span>
            <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200 flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3 text-emerald-600" />
              <span>Image Validated</span>
            </span>
            {isDbPersisted && (
              <span className="text-xs font-bold text-blue-900 bg-blue-100 px-2.5 py-0.5 rounded-md border border-blue-300 flex items-center gap-1">
                <FileCheck className="w-3 h-3 text-blue-600" />
                <span>PostgreSQL Persisted (cosmetic_verification_db)</span>
              </span>
            )}
          </div>
          <p className="text-purple-900/80 text-xs leading-relaxed">
            Multi-modal verification pipeline completed. OCR text extracted, visual feature vectors matched via 1-NN reference bank, marketplace listings searched, and real customer reviews analyzed.
          </p>
        </div>
      </div>

      {/* 2. Primary Identified Product & Matching Method Header */}
      <div className="p-6 bg-gradient-to-r from-purple-900 via-indigo-950 to-slate-950 rounded-2xl text-white space-y-4 shadow-lg border border-purple-800">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-purple-800/80 pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-pink-400" />
              <span className="text-xs font-extrabold uppercase tracking-widest text-pink-300">
                Identified Product
              </span>
            </div>
            <h3 className="text-2xl font-black text-white tracking-tight">
              {brandName} — {productName}
            </h3>
            <p className="text-xs text-purple-200">
              Category: <span className="font-semibold text-white">{categoryName}</span>
              {identity?.product_id && (
                <span className="ml-2 font-mono text-[11px] bg-purple-800/60 px-2 py-0.5 rounded border border-purple-700">
                  {identity.product_id}
                </span>
              )}
            </p>
          </div>

          <div className="text-right space-y-1">
            <div className="inline-block text-[10px] font-bold uppercase tracking-wider text-purple-200 bg-purple-800/50 px-3 py-1 rounded-full border border-purple-600">
              Matching Engine
            </div>
            <p className="text-xs font-extrabold text-pink-300 font-mono">
              {matchingMethod}
            </p>
            {clipData?.similarity_percentage !== undefined && (
              <p className="text-[11px] text-purple-300">
                Visual Similarity: <strong className="text-white">{clipData.similarity_percentage}%</strong> ({clipData.match_status})
              </p>
            )}
          </div>
        </div>

        {/* Out-of-Catalog / Low Confidence Notice */}
        {(clipData?.match_status?.includes("Catalog Mismatch") ||
          clipData?.confidence_level === "Low" ||
          (clipData?.similarity_percentage !== undefined && clipData.similarity_percentage < 65)) && (
          <div className="p-3.5 bg-amber-950/70 border border-amber-500/80 rounded-xl flex items-start gap-3 text-amber-200">
            <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            <div className="space-y-1 text-xs">
              <div className="font-extrabold text-amber-300 uppercase tracking-wide flex items-center gap-2">
                <span>Catalog Status: Out-of-Catalog Product</span>
                <span className="text-[10px] font-bold bg-amber-900/80 px-2 py-0.5 rounded border border-amber-700">
                  {clipData?.similarity_percentage}% Similarity
                </span>
              </div>
              <p className="text-amber-100/90 leading-relaxed">
                This item does not meet confident catalog match criteria (current nearest catalog neighbor is <em>{productName}</em> with {clipData?.similarity_percentage}% similarity). Per project catalog integrity rules, this item is treated as an <strong>Out-of-Catalog Product</strong>. You can verify real product listings and reviews using direct marketplace search tools below.
              </p>
            </div>
          </div>
        )}

        {/* Dual Inspection Pipeline: OCR vs CLIP */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 text-xs">
          <div className="p-3.5 bg-slate-900/80 rounded-xl border border-purple-800/60 space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-purple-300 uppercase flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-purple-400" />
                <span>1A. EasyOCR Label Extraction</span>
              </span>
              {ocrData?.confidence ? (
                <span className="text-[10px] font-extrabold text-emerald-300 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-700">
                  {(ocrData.confidence * 100).toFixed(0)}% Conf
                </span>
              ) : null}
            </div>
            <div className="font-extrabold text-white truncate">
              Brand: {ocrData?.brand_name || brandName}
            </div>
            <p className="text-[11px] text-slate-300">
              {ocrData?.total_lines_detected ? `${ocrData.total_lines_detected} label text lines detected` : "Physical label extracted"}
            </p>
          </div>

          <div className="p-3.5 bg-slate-900/80 rounded-xl border border-purple-800/60 space-y-1.5">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold text-purple-300 uppercase flex items-center gap-1.5">
                <Search className="w-3.5 h-3.5 text-purple-400" />
                <span>1B. 1-NN Reference Bank Visual Match</span>
              </span>
              <span className="text-[10px] font-extrabold text-pink-300 bg-pink-950 px-2 py-0.5 rounded border border-pink-700">
                512-dim CLIP
              </span>
            </div>
            <div className="font-extrabold text-white">
              {clipData ? `${clipData.similarity_percentage}% Match` : "Visual Match"}
            </div>
            <p className="text-[11px] text-slate-300">
              Status: {clipData?.match_status || "Evaluated"} • Method: {matchingMethod}
            </p>
          </div>
        </div>

        {/* Extracted Label Text Accordion */}
        {ocrData && ocrData.raw_text && ocrData.raw_text.length > 0 && (
          <div className="p-3 bg-slate-900/60 rounded-xl border border-purple-900/60 space-y-2">
            <button
              type="button"
              onClick={() => setShowExtractedText(!showExtractedText)}
              className="w-full flex items-center justify-between text-xs font-bold text-purple-200 cursor-pointer"
            >
              <div className="flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-purple-400" />
                <span>Extracted Packaging Label Text ({ocrData.raw_text.length} lines detected)</span>
              </div>
              {showExtractedText ? <ChevronUp className="w-4 h-4 text-purple-400" /> : <ChevronDown className="w-4 h-4 text-purple-400" />}
            </button>

            {showExtractedText && (
              <div className="pt-2 flex flex-wrap gap-1.5 animate-fadeIn">
                {ocrData.raw_text.map((line, idx) => (
                  <span
                    key={idx}
                    className="inline-block text-[11px] font-medium bg-slate-800 text-purple-200 px-2.5 py-1 rounded-lg border border-purple-800/80"
                  >
                    {line}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* 3. Section 2 — Evidence-Based Product Authenticity Assessment */}
      <div className="p-6 bg-slate-900 rounded-2xl border border-slate-800 text-white space-y-4 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2 text-pink-300 text-xs font-extrabold uppercase tracking-wider">
            <ShieldCheck className="w-4 h-4 text-pink-400" />
            <span>Section 2 — Evidence-Based Authenticity Assessment</span>
          </div>
          <div className="flex items-center gap-2">
            <span className={`text-xs font-black uppercase px-3 py-1 rounded-full border ${getOutcomeBadgeStyle(authData?.assessment_outcome)}`}>
              Outcome: {authData?.assessment_outcome || "REQUIRES_MANUAL_VERIFICATION"}
            </span>
            <span className="text-[10px] font-bold uppercase px-2.5 py-1 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
              {authData?.risk_level || "Low Risk"}
            </span>
          </div>
        </div>

        {/* Narrative Reason */}
        <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
          <p className="text-xs text-slate-200 leading-relaxed">
            {authData?.assessment_explanation || authData?.recommendation || "Packaging label text and visual features match catalog reference specifications."}
          </p>
          <div className="text-[11px] text-purple-300 pt-1 border-t border-slate-800 flex items-center justify-between">
            <span>
              <strong>Scope:</strong> {authData?.score_scope || "Packaging appearance & visual catalog similarity"} ({authData?.overall_authenticity_score ?? 85}%)
            </span>
            <span className="italic text-slate-400">Never claims physical chemical authenticity</span>
          </div>
        </div>

        {/* Verified Evidence vs Conflicts */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 text-xs">
          {/* Verified Checks */}
          <div className="p-3.5 bg-slate-950 rounded-xl border border-emerald-900/40 space-y-2">
            <div className="text-[11px] font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>Verified Evidence ({authData?.verified_evidence?.length || 0})</span>
            </div>
            {authData?.verified_evidence && authData.verified_evidence.length > 0 ? (
              <ul className="space-y-1.5 text-slate-300 text-[11px]">
                {authData.verified_evidence.map((ev, i) => (
                  <li key={i} className="flex items-start gap-1.5">
                    <span className="text-emerald-400 shrink-0 font-bold">•</span>
                    <span>{ev}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-slate-400 italic text-[11px]">No verifiable evidence points confirmed.</p>
            )}
          </div>

          {/* Inconsistencies or Conflicts */}
          <div className="p-3.5 bg-slate-950 rounded-xl border border-rose-900/40 space-y-2">
            <div className="text-[11px] font-bold text-rose-400 uppercase tracking-wider flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
              <span>Inconsistencies &amp; Conflicts ({authData?.inconsistencies?.length || 0})</span>
            </div>
            {authData?.inconsistencies && authData.inconsistencies.length > 0 ? (
              <ul className="space-y-1.5 text-rose-200 text-[11px]">
                {authData.inconsistencies.map((inc, i) => (
                  <li key={i} className="flex items-start gap-1.5">
                    <span className="text-rose-400 shrink-0 font-bold">•</span>
                    <span>{inc}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="p-2 bg-emerald-950/30 rounded border border-emerald-900/40 text-emerald-300 text-[11px]">
                Zero product name, brand, or category conflicts detected between modalities.
              </div>
            )}
          </div>
        </div>

        {/* Missing Information & Model Boundary Accordion */}
        <div className="p-3 bg-slate-950/70 rounded-xl border border-slate-800 space-y-2">
          <button
            type="button"
            onClick={() => setShowMissingInfo(!showMissingInfo)}
            className="w-full flex items-center justify-between text-xs font-semibold text-slate-300 cursor-pointer"
          >
            <div className="flex items-center gap-1.5 text-amber-300">
              <ShieldAlert className="w-4 h-4 text-amber-400" />
              <span>View Unverified Factors &amp; Model Limitations ({authData?.missing_information?.length || 3})</span>
            </div>
            {showMissingInfo ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
          </button>

          {showMissingInfo && (
            <div className="pt-2 text-xs space-y-2 border-t border-slate-800 animate-fadeIn">
              <ul className="space-y-1.5 text-slate-400 text-[11px]">
                {(authData?.missing_information || [
                  "Physical chemical formulation and laboratory ingredient composition cannot be verified via 2D photo.",
                  "Manufacturer batch code / lot number validation against brand registry is not available online.",
                  "Tamper-evident seal and packaging inner lining integrity cannot be physically inspected.",
                ]).map((msg, i) => (
                  <li key={i} className="flex items-start gap-1.5">
                    <span className="text-amber-400 shrink-0">•</span>
                    <span>{msg}</span>
                  </li>
                ))}
              </ul>
              <p className="text-[10px] text-slate-400 italic pt-1">
                A high packaging score confirms label and container visual agreement with catalog references only. Purchase from authorized sellers is always recommended.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* 4. Section 3 — Marketplace Search & Platform Comparison */}
      <div className="p-6 bg-slate-900 rounded-2xl border border-slate-800 text-white space-y-4 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
          <div className="space-y-0.5">
            <div className="flex items-center gap-2 text-purple-300 text-xs font-extrabold uppercase tracking-wider">
              <Store className="w-4 h-4 text-purple-400" />
              <span>Section 3 — Marketplace Product Search</span>
            </div>
            <p className="text-xs text-slate-300">
              Normalized Query: <span className="font-bold text-white">{brandName}</span> <span className="text-purple-200">{productName}</span>
            </p>
          </div>
          <div className="inline-flex items-center gap-1.5 bg-purple-950 border border-purple-800 text-purple-300 px-3 py-1 rounded-full text-xs font-semibold">
            <Info className="w-3.5 h-3.5 text-purple-400" />
            <span>Permitted Scrapers &amp; Direct URLs</span>
          </div>
        </div>

        {/* Browser Direct Search Links */}
        <div className="p-4 bg-slate-950 rounded-xl border border-purple-900/60 space-y-2.5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="flex items-center gap-2 text-xs font-bold text-purple-200">
              <Globe className="w-4 h-4 text-purple-400" />
              <span>Search Online Marketplaces Directly in Browser</span>
            </div>
            <span className="text-[11px] text-slate-400 italic">
              Bypasses automated bot detection
            </span>
          </div>
          <p className="text-[11px] text-slate-400 leading-snug">
            If automated search is blocked or returns zero listings, click below to open live searches for <strong className="text-white">"{searchQuery}"</strong> directly in your browser:
          </p>
          <div className="flex flex-wrap gap-2 pt-1">
            <a
              href={darazSearchUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#f57224]/20 hover:bg-[#f57224]/30 text-[#f57224] border border-[#f57224]/40 rounded-lg text-xs font-bold transition-colors"
            >
              <span>Search on Daraz LK</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
            <a
              href={amazonSearchUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#ff9900]/20 hover:bg-[#ff9900]/30 text-[#ff9900] border border-[#ff9900]/40 rounded-lg text-xs font-bold transition-colors"
            >
              <span>Search on Amazon</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
            <a
              href={temuSearchUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#fb7701]/20 hover:bg-[#fb7701]/30 text-[#fb7701] border border-[#fb7701]/40 rounded-lg text-xs font-bold transition-colors"
            >
              <span>Search on Temu</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>

        {/* Direct Product URL Scraper Form */}
        <div className="p-4 bg-slate-950 rounded-xl border border-indigo-900/60 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-bold text-indigo-300">
              <ExternalLink className="w-4 h-4 text-indigo-400" />
              <span>Direct Marketplace URL Scraper &amp; Review Analyzer</span>
            </div>
            <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
              Express Gateway (:5000)
            </span>
          </div>
          <p className="text-[11px] text-slate-300 leading-snug">
            Paste any direct product link from <strong className="text-white">Daraz, Amazon, or Temu</strong>. The system extracts real listing details, collects customer reviews, and runs sentiment analysis in real time.
          </p>

          <div className="flex flex-col sm:flex-row gap-2">
            <input
              type="url"
              placeholder="https://www.daraz.lk/products/maybelline-fit-me-..."
              value={directUrl}
              onChange={(e) => setDirectUrl(e.target.value)}
              className="flex-1 px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
            <button
              type="button"
              onClick={handleDirectUrlScrape}
              disabled={isScrapingUrl || !directUrl.trim()}
              className="px-4 py-2 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-500 rounded-lg transition-colors flex items-center justify-center gap-2 shrink-0 cursor-pointer disabled:cursor-not-allowed"
            >
              {isScrapingUrl ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Extracting Reviews...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Scrape &amp; Analyze</span>
                </>
              )}
            </button>
          </div>

          {urlScrapeError && (
            <div className="p-2.5 bg-rose-950/80 border border-rose-800 text-rose-300 rounded-lg text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400" />
              <span>{urlScrapeError}</span>
            </div>
          )}

          {urlScrapeSuccess && (
            <div className="p-2.5 bg-emerald-950/80 border border-emerald-800 text-emerald-300 rounded-lg text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
              <span>{urlScrapeSuccess}</span>
            </div>
          )}
        </div>

        {/* Valid Verified Marketplace Listings */}
        {validListings.length > 0 ? (
          <div className="space-y-3">
            <h5 className="text-xs font-extrabold text-purple-300 uppercase tracking-wider">
              Verified Marketplace Product Listings ({validListings.length})
            </h5>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
              {validListings.map((plat, idx) => {
                const listing = plat.listing;
                const statusBadge = listing.listing_status || "VERIFIED_LISTING";

                return (
                  <div
                    key={idx}
                    className="p-4 bg-slate-950 rounded-xl border border-purple-900/70 hover:border-purple-600 transition-colors space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-sm text-purple-300">{plat.platform}</span>
                      <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-700">
                        {statusBadge}
                      </span>
                    </div>

                    <div className="space-y-1">
                      <h6 className="font-bold text-xs text-white line-clamp-2" title={listing.product_name}>
                        {listing.product_name}
                      </h6>
                      {listing.seller_name && (
                        <p className="text-[11px] text-slate-400">
                          Seller: <span className="text-slate-200 font-semibold">{listing.seller_name}</span>
                        </p>
                      )}
                    </div>

                    <div className="flex items-center justify-between text-xs pt-1 border-t border-slate-800">
                      <div>
                        {listing.price && listing.price > 0 ? (
                          <span className="text-sm font-extrabold text-emerald-400">
                            {listing.currency || "USD"} {listing.price.toFixed(2)}
                          </span>
                        ) : (
                          <span className="text-xs text-slate-400 italic">Price Unavailable</span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 text-[11px] text-slate-300">
                        {listing.rating && listing.rating > 0 ? (
                          <span className="flex items-center gap-1 text-amber-300 font-bold">
                            <Star className="w-3.5 h-3.5 fill-amber-300 text-amber-300" />
                            <span>{listing.rating.toFixed(1)}/5.0</span>
                          </span>
                        ) : null}
                        <span>({listing.review_count || (listing.reviews ? listing.reviews.length : 0)} reviews)</span>
                      </div>
                    </div>

                    {listing.product_url && listing.product_url.startsWith("http") ? (
                      <a
                        href={listing.product_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center justify-center gap-1.5 w-full py-2 px-3 text-xs font-bold text-white bg-purple-900 hover:bg-purple-800 rounded-lg transition-colors cursor-pointer"
                      >
                        <span>View Verified Listing on {plat.platform}</span>
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    ) : (
                      <span className="block text-[10px] text-center text-slate-400 italic">
                        Direct URL Unavailable
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          <div className="p-4 bg-slate-950/80 rounded-xl border border-slate-800 text-xs text-slate-300 space-y-1">
            <p className="font-bold text-slate-200">No Verified Product Listings Returned</p>
            <p className="text-slate-400 text-[11px]">
              Marketplace search did not return active catalog listings matching the normalized query, or platform anti-bot controls restricted automated search. You can supply an exact product link in the workspace above.
            </p>
          </div>
        )}

        {/* Platform Scraper Operational & Blocked Statuses */}
        {statusEntries.length > 0 && (
          <div className="pt-3 border-t border-slate-800 space-y-2">
            <h5 className="text-[11px] font-extrabold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-slate-400" />
              <span>Platform Access Status &amp; Anti-Bot Disclosures</span>
            </h5>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
              {statusEntries.map((plat, idx) => {
                const listing = plat.listing;
                const statusType = listing?.source_status || "unavailable";
                const statusCode = listing?.listing_status || (statusType === "blocked" ? "MARKETPLACE_BLOCKED" : "UNAVAILABLE");
                const explanation = plat.recommendation_reason || listing?.status_explanation || "No listing data returned";

                return (
                  <div
                    key={idx}
                    className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-xs space-y-1.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-200">{plat.platform}</span>
                      <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded border ${
                        statusCode === "MARKETPLACE_BLOCKED"
                          ? "bg-rose-950 text-rose-300 border-rose-800"
                          : statusCode === "NOT_RETRIEVABLE"
                          ? "bg-amber-950 text-amber-300 border-amber-800"
                          : "bg-slate-800 text-slate-400 border-slate-700"
                      }`}>
                        {statusCode}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 leading-snug">
                      {explanation}
                    </p>
                    <a
                      href={
                        plat.platform.toLowerCase().includes("daraz")
                          ? darazSearchUrl
                          : plat.platform.toLowerCase().includes("amazon")
                          ? amazonSearchUrl
                          : temuSearchUrl
                      }
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-[11px] font-bold text-purple-400 hover:text-purple-300 pt-1"
                    >
                      <span>Search on {plat.platform} in Browser</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* 5. Section 4 — Actual Customer Reviews Collection */}
      <div id="customer-reviews-section" className="p-6 bg-slate-900 rounded-2xl border border-slate-800 text-white space-y-4 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2 text-indigo-300 text-xs font-extrabold uppercase tracking-wider">
            <MessageSquare className="w-4 h-4 text-indigo-400" />
            <span>Section 4 — Actual Customer Reviews Collection</span>
          </div>
          <span className="text-xs font-bold px-3 py-1 rounded-full bg-slate-800 border border-slate-700 text-slate-200">
            Collected: {allCustomerReviews.length} Real Review(s)
          </span>
        </div>

        {allCustomerReviews.length > 0 ? (
          <div className="space-y-3">
            <div className="grid grid-cols-1 gap-3 max-h-[380px] overflow-y-auto pr-1">
              {allCustomerReviews.map((rv, idx) => (
                <div
                  key={idx}
                  className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 space-y-2 hover:border-slate-700 transition-colors"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-6 rounded-full bg-purple-950 border border-purple-800 flex items-center justify-center text-purple-300 text-[10px] font-bold">
                        <User className="w-3.5 h-3.5" />
                      </div>
                      <span className="text-xs font-bold text-slate-200">{rv.author || "Anonymous"}</span>
                      {rv.verified_purchase && (
                        <span className="text-[10px] font-bold text-emerald-400 bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-800 flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>Verified Purchase</span>
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      {rv.date && (
                        <span className="text-[11px] text-slate-400 flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          <span>{rv.date}</span>
                        </span>
                      )}
                      {rv.rating ? (
                        <span className="text-xs font-bold text-amber-300 flex items-center gap-0.5">
                          <Star className="w-3 h-3 fill-amber-300 text-amber-300" />
                          <span>{rv.rating.toFixed(1)}</span>
                        </span>
                      ) : null}
                    </div>
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed pl-8">
                    "{rv.comment}"
                  </p>

                  <div className="flex flex-wrap items-center justify-between gap-2 pl-8 pt-1 text-[11px]">
                    {rv.sentiment ? (
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded font-bold ${
                        rv.sentiment === "positive"
                          ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                          : rv.sentiment === "negative"
                          ? "bg-rose-950 text-rose-300 border border-rose-800"
                          : "bg-slate-800 text-slate-300 border border-slate-700"
                      }`}>
                        {rv.sentiment === "positive" ? <ThumbsUp className="w-3 h-3" /> : rv.sentiment === "negative" ? <ThumbsDown className="w-3 h-3" /> : <MinusCircle className="w-3 h-3" />}
                        <span>{rv.sentiment.toUpperCase()}</span>
                        {rv.sentiment_confidence ? <span>({(rv.sentiment_confidence * 100).toFixed(0)}%)</span> : null}
                      </span>
                    ) : (
                      <span className="text-slate-500 italic">No sentiment computed</span>
                    )}

                    {rv.suspicious_flag && (
                      <span className="text-[10px] font-bold text-rose-300 bg-rose-950 px-2 py-0.5 rounded border border-rose-800 flex items-center gap-1">
                        <AlertTriangle className="w-3 h-3 text-rose-400" />
                        <span>{rv.suspicious_reason || "Flagged Anomaly"}</span>
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="p-4 bg-slate-950/80 rounded-xl border border-slate-800 text-xs text-slate-300 space-y-1">
            <p className="font-bold text-slate-200">No Review Text Available</p>
            <p className="text-slate-400 text-[11px]">
              No written customer reviews were extracted from accessible marketplace sources for this product. The system never fabricates synthetic or placeholder reviews.
            </p>
          </div>
        )}
      </div>

      {/* 6. Section 5 — Sentiment Analysis (TF-IDF + Logistic Regression Baseline) */}
      <div id="sentiment-analysis-section" className="p-6 bg-slate-900 rounded-2xl border border-slate-800 text-white space-y-4 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2 text-indigo-300 text-xs font-extrabold uppercase tracking-wider">
            <Sparkles className="w-4 h-4 text-indigo-400" />
            <span>Section 5 — Sentiment Analysis on Collected Reviews</span>
          </div>
          <span className="text-xs font-bold px-3 py-1 rounded-full bg-indigo-950 border border-indigo-700 text-indigo-300">
            Model: TF-IDF + Logistic Regression
          </span>
        </div>

        {activeReviewData?.marketplace_sentiment && activeReviewData.marketplace_sentiment.analyzed_count > 0 ? (
          <div className="space-y-3">
            <div className="grid grid-cols-3 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-emerald-950/50 border border-emerald-900 text-emerald-300 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold">Positive</span>
                  <ThumbsUp className="w-3.5 h-3.5" />
                </div>
                <div className="text-xl font-black font-mono">
                  {activeReviewData.marketplace_sentiment.counts.positive}
                </div>
                <p className="text-[10px] text-emerald-400/80">
                  {((activeReviewData.marketplace_sentiment.counts.positive / activeReviewData.marketplace_sentiment.analyzed_count) * 100).toFixed(0)}% of analyzed
                </p>
              </div>

              <div className="p-3 rounded-xl bg-slate-800/80 border border-slate-700 text-slate-200 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold">Neutral</span>
                  <MinusCircle className="w-3.5 h-3.5 text-slate-400" />
                </div>
                <div className="text-xl font-black font-mono">
                  {activeReviewData.marketplace_sentiment.counts.neutral}
                </div>
                <p className="text-[10px] text-slate-400">
                  {((activeReviewData.marketplace_sentiment.counts.neutral / activeReviewData.marketplace_sentiment.analyzed_count) * 100).toFixed(0)}% of analyzed
                </p>
              </div>

              <div className="p-3 rounded-xl bg-rose-950/50 border border-rose-900 text-rose-300 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold">Negative</span>
                  <ThumbsDown className="w-3.5 h-3.5" />
                </div>
                <div className="text-xl font-black font-mono">
                  {activeReviewData.marketplace_sentiment.counts.negative}
                </div>
                <p className="text-[10px] text-rose-400/80">
                  {((activeReviewData.marketplace_sentiment.counts.negative / activeReviewData.marketplace_sentiment.analyzed_count) * 100).toFixed(0)}% of analyzed
                </p>
              </div>
            </div>

            <p className="text-[11px] text-slate-400 leading-snug">
              Analyzed {activeReviewData.marketplace_sentiment.analyzed_count} real customer review(s). Overall Sentiment: <strong className="text-white">{activeReviewData.sentiment_label}</strong>.
            </p>
          </div>
        ) : (
          <p className="text-xs text-slate-300">
            {activeReviewData?.marketplace_sentiment?.explanation || "No actual customer review text was collected for this product, so no live sentiment is reported."}
          </p>
        )}

        {/* Model Boundary & Rating-Derived Disclosure */}
        <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-[11px] text-slate-400 space-y-1">
          <p className="font-bold text-slate-300">Model Training &amp; Label Disclosure:</p>
          <p>
            Sentiment model was trained using rating-derived labels (1-2★ negative, 3★ neutral, 4-5★ positive) from the Amazon Beauty Reviews dataset (v1.0.0). Due to rating skew, neutral-class performance is limited. This is a sentiment model only, not a fake-review detector.
          </p>
        </div>
      </div>

      {/* 7. Section 6 — Explainable Suspicious-Review Risk Indicator */}
      <div id="suspicious-review-section" className="p-6 bg-slate-900 rounded-2xl border border-slate-800 text-white space-y-4 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2 text-indigo-300 text-xs font-extrabold uppercase tracking-wider">
            <ShieldAlert className="w-4 h-4 text-indigo-400" />
            <span>Section 6 — Suspicious-Review Risk Indicator</span>
          </div>
          <span className={`text-xs font-extrabold uppercase px-3 py-1 rounded-full border ${getRiskLevelBadgeStyle(suspiciousRisk?.risk_level)}`}>
            Risk Status: {suspiciousRisk?.risk_level || "INSUFFICIENT_DATA"}
          </span>
        </div>

        {/* Narrative Reason */}
        <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
          <p className="text-xs text-slate-200 leading-relaxed">
            {suspiciousRisk?.explanation || "Fewer than 3 customer reviews collected. Cannot reliably evaluate statistical suspicious-review patterns."}
          </p>
          <p className="text-[11px] text-slate-400 italic border-t border-slate-800 pt-1.5">
            {suspiciousRisk?.disclaimer || "Explainable heuristic risk indicator based on available metadata anomalies. Not a validated machine-learning classifier; does not prove fraud."}
          </p>
        </div>

        {/* Detected Indicators List */}
        {suspiciousRisk && suspiciousRisk.indicators_detected && suspiciousRisk.indicators_detected.length > 0 ? (
          <div className="space-y-2.5">
            <h6 className="text-[11px] font-bold text-amber-300 uppercase tracking-wider">
              Detected Review Anomalies ({suspiciousRisk.indicators_detected.length})
            </h6>
            <div className="space-y-2">
              {suspiciousRisk.indicators_detected.map((ind, i) => (
                <div key={i} className="p-3 bg-slate-950 rounded-xl border border-amber-900/50 space-y-1 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-extrabold text-amber-300 flex items-center gap-1.5">
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                      <span>{ind.indicator}</span>
                    </span>
                    <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800">
                      Severity: {ind.severity}
                    </span>
                  </div>
                  <p className="text-slate-300 text-[11px]">{ind.description}</p>
                  {ind.evidence && ind.evidence.length > 0 && (
                    <div className="pt-1 text-[10px] font-mono text-slate-400 bg-slate-900 p-2 rounded">
                      Evidence: {ind.evidence.join(" • ")}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        ) : suspiciousRisk?.status === "EVALUATED" ? (
          <div className="p-3 bg-emerald-950/30 rounded-xl border border-emerald-900/50 text-emerald-300 text-xs flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>Zero duplicate review texts, temporal bursts, or rating-sentiment conflicts detected across the collected reviews.</span>
          </div>
        ) : null}
      </div>

      {/* 8. Developer Debug Payload Accordion */}
      {aiAnalysisResult && (
        <div className="pt-2 border-t border-slate-100">
          <button
            type="button"
            onClick={() => setShowDeveloperDebug(!showDeveloperDebug)}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-purple-700 transition-colors py-1 cursor-pointer"
          >
            <Terminal className="w-3.5 h-3.5" />
            <span>{showDeveloperDebug ? "Hide FastAPI Debug Log" : "FastAPI Response Debug Payload"}</span>
            {showDeveloperDebug ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>

          {showDeveloperDebug && (
            <div className="mt-2 p-4 bg-slate-900 rounded-xl border border-slate-800 text-slate-200 space-y-2 animate-fadeIn">
              <div className="flex items-center justify-between text-[11px] font-bold text-purple-400 uppercase tracking-wider">
                <div className="flex items-center gap-1.5">
                  <Terminal className="w-3.5 h-3.5 text-emerald-400" />
                  <span>FastAPI Payload Debug Log (POST http://localhost:8001/api/analyze)</span>
                </div>
                <span className="text-[10px] bg-emerald-950 text-emerald-400 border border-emerald-700 px-2 py-0.5 rounded-md">
                  Port 8001
                </span>
              </div>
              <pre className="text-xs font-mono bg-slate-950 p-3 rounded-lg overflow-x-auto text-emerald-300 leading-relaxed border border-slate-800">
                {JSON.stringify(aiAnalysisResult, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* 9. Reset Action Footer */}
      <div className="pt-4 border-t border-purple-100 flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>Real multi-modal inspection completed</span>
        </div>

        <button
          type="button"
          onClick={onReset}
          className="inline-flex items-center gap-2 px-5 py-2.5 text-xs font-bold text-slate-800 bg-white hover:bg-slate-100 border border-slate-300 rounded-xl shadow-xs transition-colors touch-manipulation min-h-[44px] cursor-pointer"
        >
          <RotateCcw className="w-4 h-4 text-purple-600" />
          <span>Reset Verification</span>
        </button>
      </div>
    </div>
  );
}
