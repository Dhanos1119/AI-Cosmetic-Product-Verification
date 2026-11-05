"use client";

import { useState } from "react";
import {
  RotateCcw,
  CheckCircle2,
  Sparkles,
  Store,
  MessageSquare,
  AlertTriangle,
  ExternalLink,
  ShieldAlert,
  ThumbsUp,
  ThumbsDown,
  MinusCircle,
  Clock,
  User,
  Star,
  Globe,
  Award,
  TrendingUp,
  Check,
  ShoppingBag,
  Info,
  Tag,
  Layers,
  HelpCircle,
  Database,
  Calendar,
  ShieldCheck,
  FileText,
  AlertCircle,
} from "lucide-react";
import ReviewAnalysisModal, { ReviewItem, ReviewSentimentStats } from "./ReviewAnalysisModal";

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
  discrimination_margin?: number;
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
  review_id?: string;
  author?: string;
  reviewer_name?: string;
  rating?: number;
  star_rating?: number;
  headline?: string;
  comment?: string;
  text?: string;
  date?: string;
  verified_purchase?: boolean;
  sentiment?: string;
  predicted_sentiment?: string;
  sentiment_confidence?: number | null;
  explanation?: string;
  credibility_indicators?: {
    verified_purchase?: boolean;
    pattern?: string;
  };
  source_label?: string;
  retrieval_status?: string;
  data_source?: string;
  suspicious_flag?: boolean;
  suspicious_reason?: string;
}

export interface ReviewResultDetails {
  status: string;
  is_simulated?: boolean;
  simulation_title?: string;
  simulation_disclosure?: string;
  credibility_assessment_label?: string;
  positive_themes?: string[];
  negative_themes?: string[];
  sentiment_stats?: ReviewSentimentStats;
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
  simulated_reviews?: MarketplaceReview[];
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
  assessment_outcome?: string;
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
  retrieval_status?: "LIVE" | "DEMO" | "UNAVAILABLE" | string;
  data_source?: string;
  retrieval_timestamp?: string;
  search_url?: string;
}

export interface ScoreBreakdown {
  match_confidence_score: number;
  rating_volume_score: number;
  seller_trust_score: number;
  price_score: number;
  review_sentiment_score: number;
  review_trust_score?: number;
  rating_score?: number;
}

export interface PlatformComparisonScore {
  platform: string;
  total_score: number;
  rank: number;
  score_breakdown: ScoreBreakdown;
  recommendation_reason: string;
  listing: MarketplaceListing;
  recommendation_type?: string;
  is_demo?: boolean;
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
  is_confirmed?: boolean;
  identity_status?: string;
  visual_similarity_disclaimer?: string;
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

export interface VerificationResultProps {
  previewUrl: string | null;
  aiAnalysisResult: AiAnalysisResult | null;
  onReset: () => void;
}

export default function VerificationResult({
  previewUrl,
  aiAnalysisResult,
  onReset,
}: VerificationResultProps) {
  const [isReviewModalOpen, setIsReviewModalOpen] = useState(false);
  const [selectedReviewPlatform, setSelectedReviewPlatform] = useState<"All" | "Amazon" | "Daraz LK" | "Temu">("All");

  // Extract result sub-objects safely
  const ocrData = aiAnalysisResult?.ocr_result;
  const clipData = aiAnalysisResult?.clip_result;
  const reviewData = aiAnalysisResult?.review_result;
  const authData = aiAnalysisResult?.authenticity_result;
  const identity = aiAnalysisResult?.product_identity;

  const brandName =
    identity?.brand ||
    aiAnalysisResult?.brand_name ||
    ocrData?.brand_name ||
    "Cosmetic Brand";

  const productName =
    identity?.product_name ||
    aiAnalysisResult?.product_name ||
    ocrData?.product_name ||
    "Unidentified Product";

  const categoryName =
    identity?.category ||
    ocrData?.category ||
    aiAnalysisResult?.product_detection ||
    "Cosmetics";

  // Defensive check for non-cosmetic images
  const isNonCosmetic =
    aiAnalysisResult?.product_detection === "Non-Cosmetic" ||
    (aiAnalysisResult as any)?.status === "rejected_non_cosmetic" ||
    (aiAnalysisResult as any)?.is_cosmetic === false;

  if (isNonCosmetic) {
    return (
      <div className="w-full bg-[#191925] text-[#F8FAFC] rounded-3xl p-6 sm:p-10 border border-[#303047] shadow-2xl space-y-6 animate-fadeIn">
        <div className="p-6 bg-[#202033] border border-[#F87171]/40 rounded-2xl flex items-start gap-4">
          <AlertCircle className="w-6 h-6 text-[#F87171] shrink-0 mt-0.5" />
          <div className="space-y-2">
            <h3 className="text-lg font-bold text-[#F87171]">Non-cosmetic image detected.</h3>
            <p className="text-sm text-[#A1A1B5]">
              This image does not contain a recognized cosmetic product. Marketplace searches, customer reviews, sentiment analysis, and recommendation scoring are disabled for non-cosmetic items.
            </p>
            <button
              type="button"
              onClick={onReset}
              className="mt-3 inline-flex items-center gap-2 px-4 py-2 text-xs font-bold text-[#F8FAFC] bg-[#12121C] hover:bg-[#191925] border border-[#303047] rounded-xl transition-all cursor-pointer"
            >
              <RotateCcw className="w-4 h-4 text-[#A855F7]" />
              <span>Upload Another Image</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Determine confirmation state
  const isConfirmed =
    aiAnalysisResult?.is_confirmed !== undefined
      ? aiAnalysisResult.is_confirmed
      : !(
          clipData?.match_status?.toLowerCase().includes("mismatch") ||
          clipData?.match_status?.toLowerCase().includes("ambiguous") ||
          clipData?.confidence_level?.toLowerCase() === "low" ||
          (clipData?.similarity_percentage !== undefined && clipData.similarity_percentage < 65)
        );

  const identityStatusText =
    aiAnalysisResult?.identity_status ||
    (isConfirmed ? "Confirmed Product Identity" : "Unconfirmed Product Identity");

  const disclaimerText =
    aiAnalysisResult?.visual_similarity_disclaimer ||
    "Visual similarity indicates packaging shape and aesthetic resemblance to reference catalog images; it does not confirm or prove product authenticity.";

  // Search links for standard marketplace direct searches
  const searchQuery = `${brandName !== "Cosmetic Brand" ? brandName : ""} ${productName}`.trim() || "Cosmetic Product";
  const darazSearchUrl = `https://www.daraz.lk/catalog/?q=${encodeURIComponent(searchQuery)}`;
  const amazonSearchUrl = `https://www.amazon.com/s?k=${encodeURIComponent(searchQuery)}`;
  const temuSearchUrl = `https://www.temu.com/search_result.html?search_key=${encodeURIComponent(searchQuery)}`;

  // Retrieve listings for the three standard marketplaces
  const marketplaceListings = aiAnalysisResult?.marketplace_listings || [];

  const getListingForPlatform = (platformName: string): MarketplaceListing | undefined => {
    return marketplaceListings.find((l) =>
      l.platform.toLowerCase().includes(platformName.toLowerCase())
    );
  };

  const amazonListing = getListingForPlatform("Amazon");
  const darazListing = getListingForPlatform("Daraz");
  const temuListing = getListingForPlatform("Temu");

  // Format currency & price helper
  const formatPrice = (price?: number, currency?: string) => {
    if (!price || price <= 0) return "Unavailable";
    const curr = (currency || "USD").toUpperCase();
    if (curr === "LKR") {
      return `LKR ${price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }
    if (curr === "USD" || curr === "$") {
      return `$${price.toFixed(2)}`;
    }
    return `${curr} ${price.toFixed(2)}`;
  };

  // CLIP catalog similarity & honest confidence threshold calculations
  const clipSimilarityPct =
    typeof clipData?.similarity_percentage === "number"
      ? clipData.similarity_percentage
      : 0;

  const isHighConfidence = clipSimilarityPct >= 80.0;
  const isModerateConfidence = clipSimilarityPct >= 60.0 && clipSimilarityPct < 80.0;

  const confidenceStatusLabel = isHighConfidence
    ? "High Confidence"
    : isModerateConfidence
    ? "Moderate Confidence"
    : "Low Confidence";

  const confidenceStatusColor = isHighConfidence
    ? "text-[#22C55E]"
    : isModerateConfidence
    ? "text-[#A855F7]"
    : "text-[#F59E0B]";

  // Collect customer reviews (simulated or real)
  const allCustomerReviews: MarketplaceReview[] =
    reviewData?.simulated_reviews && reviewData.simulated_reviews.length > 0
      ? reviewData.simulated_reviews
      : reviewData?.analyzed_reviews && reviewData.analyzed_reviews.length > 0
      ? reviewData.analyzed_reviews
      : marketplaceListings.flatMap((m) => m.reviews || []);

  const amazonReviews = allCustomerReviews.filter((r) =>
    (r.source_label || r.data_source || "").toLowerCase().includes("amazon")
  );
  const darazReviews = allCustomerReviews.filter((r) =>
    (r.source_label || r.data_source || "").toLowerCase().includes("daraz")
  );
  const temuReviews = allCustomerReviews.filter((r) =>
    (r.source_label || r.data_source || "").toLowerCase().includes("temu")
  );

  const activeReviews =
    selectedReviewPlatform === "Amazon"
      ? amazonReviews
      : selectedReviewPlatform === "Daraz LK"
      ? darazReviews
      : selectedReviewPlatform === "Temu"
      ? temuReviews
      : allCustomerReviews;

  const activePosCount = activeReviews.filter((r) => (r.sentiment || r.predicted_sentiment) === "positive").length;
  const activeNeuCount = activeReviews.filter((r) => (r.sentiment || r.predicted_sentiment) === "neutral").length;
  const activeNegCount = activeReviews.filter((r) => (r.sentiment || r.predicted_sentiment) === "negative").length;
  const activeTotal = activeReviews.length;

  const activePosPct = activeTotal > 0 ? Math.round((activePosCount / activeTotal) * 100) : 0;
  const activeNeuPct = activeTotal > 0 ? Math.round((activeNeuCount / activeTotal) * 100) : 0;
  const activeNegPct = activeTotal > 0 ? Math.round((activeNegCount / activeTotal) * 100) : 0;

  const sentimentSummary = reviewData?.marketplace_sentiment;
  const suspiciousRisk = reviewData?.suspicious_review_risk;
  const sentimentStats = reviewData?.sentiment_stats;
  const isSimulatedReviews = Boolean(reviewData?.is_simulated);

  // Platform comparison rankings
  const platformComparisons = aiAnalysisResult?.platform_comparison || [];
  const rankedComparisons = platformComparisons.filter(
    (p) =>
      p.total_score > 0 &&
      p.rank < 99 &&
      p.listing &&
      p.listing.source_status === "available" &&
      p.listing.product_url &&
      p.listing.product_url.startsWith("http")
  );

  rankedComparisons.sort((a, b) => b.total_score - a.total_score);
  const recommendedPlatform = rankedComparisons.length > 0 ? rankedComparisons[0] : null;

  // Helper to render responsive marketplace card
  const renderMarketplaceCard = (
    platformName: "Amazon" | "Daraz LK" | "Temu",
    listing: MarketplaceListing | undefined,
    defaultSearchUrl: string,
    accentColor: string
  ) => {
    const rawStatus = (listing?.retrieval_status || "UNAVAILABLE").toUpperCase();
    const retrievalStatus: "LIVE" | "DEMO" | "UNAVAILABLE" =
      rawStatus === "LIVE" ? "LIVE" : rawStatus === "DEMO" ? "DEMO" : "UNAVAILABLE";

    const isUnavailable = retrievalStatus === "UNAVAILABLE" || platformName === "Temu";

    const title = isUnavailable
      ? (platformName === "Temu"
          ? "Access restricted due to marketplace CAPTCHA verification."
          : `Live marketplace data unavailable for ${platformName}.`)
      : (listing?.product_name || `${platformName} Listing`);

    const price = !isUnavailable && listing?.price && listing.price > 0 ? formatPrice(listing.price, listing.currency) : null;
    const rating = !isUnavailable && listing?.rating && listing.rating > 0 ? listing.rating : null;
    const reviewCount = !isUnavailable ? (listing?.review_count || 0) : 0;
    const seller = !isUnavailable ? (listing?.seller_name || null) : null;
    const dataSource =
      retrievalStatus === "DEMO"
        ? "Demo / Reference Data"
        : retrievalStatus === "LIVE"
        ? (listing?.data_source || "Live Scraper")
        : "Direct Search";

    const retrievalDate = listing?.retrieval_timestamp
      ? new Date(listing.retrieval_timestamp).toLocaleDateString(undefined, {
          month: "short",
          day: "numeric",
          hour: "2-digit",
          minute: "2-digit",
        })
      : null;

    return (
      <div
        key={platformName}
        className="flex flex-col justify-between p-6 rounded-2xl bg-[#12121C] border border-[#303047] space-y-5 hover:border-[#A855F7]/40 transition-colors shadow-md min-h-[350px]"
      >
        <div className="space-y-3.5">
          {/* Header Row: Platform Name + Status Badge */}
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <span
                className="w-2.5 h-2.5 rounded-full shrink-0"
                style={{ backgroundColor: accentColor }}
              />
              <h4 className="text-sm font-extrabold text-[#F8FAFC]">
                {platformName}
              </h4>
            </div>

            {/* Retrieval Status Badge */}
            <span
              className={`text-[10px] font-extrabold px-2.5 py-0.5 rounded-full border uppercase tracking-wider ${
                retrievalStatus === "LIVE"
                  ? "bg-[#22C55E]/15 text-[#22C55E] border-[#22C55E]/30"
                  : retrievalStatus === "DEMO"
                  ? "bg-[#A855F7]/15 text-[#A855F7] border-[#A855F7]/30"
                  : "bg-[#F59E0B]/15 text-[#F59E0B] border-[#F59E0B]/30"
              }`}
            >
              {retrievalStatus}
            </span>
          </div>

          {/* Product Title */}
          <p
            className={`text-xs font-semibold leading-relaxed line-clamp-2 ${
              isUnavailable ? "text-[#A1A1B5] italic" : "text-[#F8FAFC]"
            }`}
            title={title}
          >
            {title}
          </p>

          {/* Metadata Row: Price, Rating, Seller */}
          <div className="space-y-2 text-xs text-[#A1A1B5] pt-1.5 border-t border-[#303047]/60">
            {/* Price */}
            <div className="flex items-center justify-between">
              <span>Price:</span>
              <strong className="text-sm font-bold text-[#F8FAFC]">
                {isUnavailable ? (
                  <span className="text-[#A1A1B5]/60 italic font-normal">Price Unavailable</span>
                ) : (
                  price || <span className="text-[#A1A1B5]/60 italic font-normal">Price Unavailable</span>
                )}
              </strong>
            </div>

            {/* Rating & Review Count */}
            <div className="flex items-center justify-between">
              <span>Customer Rating:</span>
              {isUnavailable ? (
                <span className="text-[#A1A1B5]/60 italic font-normal">Rating Unavailable</span>
              ) : rating ? (
                <div className="flex items-center gap-1 text-[#F59E0B] font-bold">
                  <Star className="w-3.5 h-3.5 fill-[#F59E0B]" />
                  <span>{rating.toFixed(1)} / 5</span>
                </div>
              ) : (
                <span className="text-[#A1A1B5]/60 italic">No ratings</span>
              )}
              {isUnavailable ? (
                <span className="text-[#A1A1B5]/60 italic font-normal text-[11px]">Reviews Unavailable</span>
              ) : (
                <span>({reviewCount.toLocaleString()} {reviewCount === 1 ? "rating" : "reviews"})</span>
              )}
            </div>

            {/* Seller */}
            <div className="truncate">
              Seller:{" "}
              {isUnavailable ? (
                <span className="text-[#A1A1B5]/60 italic">Information unavailable</span>
              ) : (
                <strong className="text-[#F8FAFC]">{seller || "Information unavailable"}</strong>
              )}
            </div>

            {/* Data Source Badge */}
            <div className="pt-1 flex items-center justify-between gap-1 flex-wrap text-[11px]">
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-[#191925] border border-[#303047] text-[#A1A1B5]">
                <Database className="w-3 h-3 text-[#A855F7]" />
                <span>{dataSource}</span>
              </span>

              {retrievalDate && !isUnavailable && (
                <span className="text-[#A1A1B5]/60 flex items-center gap-1 text-[10px]">
                  <Calendar className="w-3 h-3" />
                  <span>{retrievalDate}</span>
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Action Buttons: Direct Listing View & Working Search Link */}
        <div className="space-y-2 pt-3 border-t border-[#303047]/60">
          {!isUnavailable && listing?.product_url && (
            <a
              href={listing.product_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-1.5 w-full py-2.5 px-3 text-xs font-bold text-white bg-gradient-to-r from-[#EC4899] via-[#A855F7] to-[#8B5CF6] hover:opacity-95 rounded-xl transition-all shadow-md touch-manipulation min-h-[40px] cursor-pointer"
            >
              <span>View Product on {platformName}</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          )}

          <a
            href={defaultSearchUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center justify-center gap-1.5 w-full py-2.5 px-3 text-xs font-bold text-[#F8FAFC] bg-[#191925] hover:bg-[#202033] border border-[#303047] rounded-xl transition-colors touch-manipulation min-h-[40px] cursor-pointer"
          >
            <span>Search on {platformName}</span>
            <ExternalLink className="w-3.5 h-3.5 text-[#A855F7]" />
          </a>
        </div>
      </div>
    );
  };

  return (
    <div
      id="verification-results-container"
      className="w-full space-y-8 bg-[#191925] text-[#F8FAFC] rounded-3xl p-6 sm:p-10 border border-[#303047] shadow-2xl animate-fadeIn"
    >
      {/* 1. Header Bar: Status & New Verification Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[#303047]">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-[#EC4899] to-[#A855F7] flex items-center justify-center text-white shadow-md shadow-purple-950/40">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl sm:text-2xl font-extrabold text-[#F8FAFC]">
                Verification Report
              </h2>
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-[#22C55E]/15 text-[#22C55E] border border-[#22C55E]/30">
                <Check className="w-3.5 h-3.5" />
                <span>Complete</span>
              </span>
            </div>
            <p className="text-xs text-[#A1A1B5] font-medium">
              Product categorized, reference catalog compared, and marketplace reviews analyzed
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={onReset}
          className="inline-flex items-center justify-center gap-2 px-4 py-2.5 text-xs font-bold text-[#F8FAFC] bg-[#12121C] hover:bg-[#202033] border border-[#303047] rounded-xl transition-all shadow-xs touch-manipulation min-h-[44px] cursor-pointer"
        >
          <RotateCcw className="w-4 h-4 text-[#A855F7]" />
          <span>Verify Another Product</span>
        </button>
      </div>

      {/* 2. Section A: Product Identification */}
      <div className="bg-[#202033] rounded-3xl p-6 sm:p-8 border border-[#303047] shadow-xl space-y-6">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-extrabold uppercase tracking-widest text-[#EC4899] bg-[#191925] px-3 py-1 rounded-full border border-[#303047]">
              Section A: Product Identification
            </span>
            <span className="text-xs font-bold px-3 py-1 rounded-full bg-[#A855F7]/15 text-[#A855F7] border border-[#A855F7]/30 flex items-center gap-1.5">
              <Tag className="w-3.5 h-3.5" />
              <span>Category: {categoryName}</span>
            </span>
          </div>

          {/* Exact vs Unconfirmed Badge */}
          <div className="flex items-center gap-2">
            <span
              className={`text-xs font-bold px-3 py-1 rounded-full border flex items-center gap-1.5 ${
                isConfirmed
                  ? "bg-[#22C55E]/15 text-[#22C55E] border-[#22C55E]/30"
                  : "bg-[#F59E0B]/15 text-[#F59E0B] border-[#F59E0B]/30"
              }`}
            >
              {isConfirmed ? (
                <CheckCircle2 className="w-3.5 h-3.5 text-[#22C55E] shrink-0" />
              ) : (
                <AlertTriangle className="w-3.5 h-3.5 text-[#F59E0B] shrink-0" />
              )}
              <span>{identityStatusText}</span>
            </span>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6">
          {previewUrl && (
            <div className="w-28 h-28 sm:w-36 sm:h-36 rounded-2xl overflow-hidden bg-[#12121C] border border-[#303047] shadow-inner shrink-0 flex items-center justify-center p-1.5">
              <img
                src={previewUrl}
                alt="Identified cosmetic product"
                className="w-full h-full object-cover rounded-xl"
              />
            </div>
          )}

          <div className="space-y-2 flex-1">
            <div className="text-xs font-extrabold uppercase tracking-wider text-[#EC4899]">
              {brandName}
            </div>
            <h3 className="text-2xl sm:text-3xl font-extrabold text-[#F8FAFC] tracking-tight leading-snug">
              {productName}
            </h3>
            <div className="flex flex-wrap items-center gap-2 pt-1">
              <span className="text-xs font-semibold px-3 py-1 rounded-lg bg-[#191925] border border-[#303047] text-[#A1A1B5]">
                Detected Category: <strong className="text-[#F8FAFC]">{categoryName}</strong>
              </span>

              {clipData?.similarity_percentage !== undefined && (
                <span className="text-xs font-semibold px-3 py-1 rounded-lg bg-[#191925] border border-[#303047] text-[#A1A1B5]">
                  Visual Similarity:{" "}
                  <strong className="text-[#A855F7]">{clipData.similarity_percentage}%</strong>
                  {clipData.match_status ? ` (${clipData.match_status})` : ""}
                </span>
              )}
            </div>

            {/* Uncertainty Explanation if Unconfirmed */}
            {!isConfirmed && (
              <p className="text-xs text-[#F59E0B] pt-1 flex items-center gap-1.5 font-medium">
                <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                <span>
                  Exact product identity unconfirmed: Image matches category <strong>{categoryName}</strong>, but label text or reference margin is insufficient for exact shade verification.
                </span>
              </p>
            )}
          </div>
        </div>

        {/* Visual Similarity Disclaimer */}
        <div className="p-3.5 bg-[#12121C] rounded-2xl border border-[#303047] text-xs text-[#A1A1B5] flex items-start gap-2.5">
          <Info className="w-4 h-4 text-[#A855F7] shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            <strong className="text-[#F8FAFC]">Notice:</strong> {disclaimerText}
          </p>
        </div>
      </div>

      {/* 3. Section B: Verification Summary */}
      <div className="bg-[#191925] rounded-3xl p-6 sm:p-8 border border-[#303047] shadow-xl space-y-6">
        <div className="flex items-center gap-2 border-b border-[#303047] pb-4">
          <Layers className="w-5 h-5 text-[#A855F7]" />
          <h3 className="text-xl font-extrabold text-[#F8FAFC]">
            Section B: Verification Summary
          </h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {/* 1. Cosmetic Classification */}
          <div className="p-5 rounded-2xl bg-[#12121C] border border-[#303047] space-y-2.5">
            <div className="text-[11px] font-extrabold uppercase tracking-wider text-[#A1A1B5]">
              Cosmetic Classification
            </div>
            <div className="flex items-center gap-1.5 text-sm font-black text-[#22C55E]">
              <CheckCircle2 className="w-4 h-4 text-[#22C55E]" />
              <span>Verified Cosmetic</span>
            </div>
            <p className="text-xs text-[#A1A1B5]">
              Detected as <strong className="text-[#F8FAFC]">{categoryName}</strong>
            </p>
          </div>

          {/* 2. Catalog Match Status */}
          <div className="p-5 rounded-2xl bg-[#12121C] border border-[#303047] space-y-2.5">
            <div className="text-[11px] font-extrabold uppercase tracking-wider text-[#A1A1B5]">
              Catalog Match Status
            </div>
            <div className={`flex items-center gap-1.5 text-sm font-black ${confidenceStatusColor}`}>
              <Sparkles className="w-4 h-4 shrink-0" />
              <span>{confidenceStatusLabel}</span>
            </div>
            <p className="text-xs text-[#A1A1B5]">
              Catalog Similarity: <strong className="text-[#F8FAFC]">{clipSimilarityPct.toFixed(1)}%</strong>
            </p>
          </div>

          {/* 3. Marketplace Retrieval */}
          <div className="p-5 rounded-2xl bg-[#12121C] border border-[#303047] space-y-2.5">
            <div className="text-[11px] font-extrabold uppercase tracking-wider text-[#A1A1B5]">
              Marketplace Retrieval
            </div>
            <div className="flex items-center gap-1.5 text-sm font-black text-[#F8FAFC]">
              <Store className="w-4 h-4 text-[#A855F7]" />
              <span>{marketplaceListings.length} Platforms Queried</span>
            </div>
            <p className="text-xs text-[#A1A1B5]">
              Amazon • Daraz LK • Temu
            </p>
          </div>

          {/* 4. Review Analysis Status */}
          <div className="p-5 rounded-2xl bg-[#12121C] border border-[#303047] space-y-2.5">
            <div className="text-[11px] font-extrabold uppercase tracking-wider text-[#A1A1B5]">
              Review Analysis Status
            </div>
            <div className="flex items-center gap-1.5 text-sm font-black text-[#F8FAFC]">
              <MessageSquare className="w-4 h-4 text-[#EC4899]" />
              <span>
                {isSimulatedReviews
                  ? "Demonstration Reviews"
                  : allCustomerReviews.length > 0
                  ? `${allCustomerReviews.length} Reviews`
                  : "Reviews Evaluated"}
              </span>
            </div>
            <p className="text-xs text-[#A1A1B5]">
              Sentiment: <strong className="text-[#F8FAFC] capitalize">{reviewData?.sentiment_label || "Evaluated"}</strong>
            </p>
          </div>
        </div>

        {/* Data Source Disclosure */}
        <div className="p-4 bg-[#12121C] rounded-2xl border border-[#303047] text-xs text-[#A1A1B5] space-y-1">
          <p className="font-bold text-[#F8FAFC] flex items-center gap-1.5">
            <Database className="w-3.5 h-3.5 text-[#A855F7]" />
            <span>Data Source & Methodology Disclosure:</span>
          </p>
          <p className="leading-relaxed">
            Marketplace listings are extracted from public search endpoints and configured catalog benchmarks. Visual similarity evaluates visual package geometry and branding against catalog references. Genuine review analysis applies when marketplace comments are live; otherwise demonstration reviews are explicitly labeled.
          </p>
        </div>
      </div>

      {/* 4. Section C: Marketplace Comparison */}
      <div className="bg-[#191925] rounded-3xl p-6 sm:p-8 border border-[#303047] shadow-xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#303047] pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Store className="w-5 h-5 text-[#A855F7]" />
              <h3 className="text-xl font-extrabold text-[#F8FAFC]">
                Section C: Marketplace Comparison
              </h3>
            </div>
            <p className="text-xs text-[#A1A1B5] font-medium">
              Cross-platform listings evaluated for Amazon, Daraz LK, and Temu with explicit retrieval status
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs font-semibold text-[#A1A1B5]">
            <Globe className="w-4 h-4 text-[#A855F7]" />
            <span>Supported: Amazon • Daraz LK • Temu</span>
          </div>
        </div>

        {/* Responsive 3 Marketplace Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {renderMarketplaceCard("Amazon", amazonListing, amazonSearchUrl, "#ff9900")}
          {renderMarketplaceCard("Daraz LK", darazListing, darazSearchUrl, "#f57224")}
          {renderMarketplaceCard("Temu", temuListing, temuSearchUrl, "#fb7701")}
        </div>
      </div>

      {/* 5. Section D: Customer Review Analysis */}
      <div className="bg-[#191925] rounded-3xl p-6 sm:p-8 border border-[#303047] shadow-xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#303047] pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-[#A855F7]" />
              <h3 className="text-xl font-extrabold text-[#F8FAFC]">
                Section D: Customer Review Analysis
              </h3>
            </div>
            <p className="text-xs text-[#A1A1B5] font-medium">
              {isSimulatedReviews
                ? "Simulated Review Analysis — Demonstration Data (10 synthetic records evaluated)"
                : "Sentiment distribution and credibility evaluation from customer feedback"}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setIsReviewModalOpen(true)}
              className="inline-flex items-center justify-center gap-1.5 px-4 py-2 text-xs font-bold text-white bg-gradient-to-r from-[#EC4899] via-[#A855F7] to-[#8B5CF6] hover:opacity-95 rounded-xl transition-all shadow-md touch-manipulation min-h-[40px] cursor-pointer"
            >
              <FileText className="w-4 h-4" />
              <span>View All Reviews ({allCustomerReviews.length})</span>
            </button>
          </div>
        </div>

        {/* Simulated Reviews Disclosure Banner */}
        {isSimulatedReviews && (
          <div className="p-4 rounded-2xl bg-[#12121C] border border-[#A855F7]/30 text-xs text-[#A1A1B5] space-y-1.5">
            <div className="flex items-center gap-2 text-[#A855F7] font-bold">
              <Info className="w-4 h-4" />
              <span>Simulated Review Analysis — Demonstration Data</span>
            </div>
            <p className="leading-relaxed">
              These reviews are synthetic examples generated for demonstration and testing. They were not collected from real marketplace customers and must not be used as evidence of actual product quality.
            </p>
          </div>
        )}

        {/* Platform Separation Pills */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs font-bold text-[#A1A1B5]">Platform Breakdown:</span>
          {(["All", "Amazon", "Daraz LK", "Temu"] as const).map((plat) => {
            const count =
              plat === "All"
                ? allCustomerReviews.length
                : plat === "Amazon"
                ? amazonReviews.length
                : plat === "Daraz LK"
                ? darazReviews.length
                : temuReviews.length;
            const isUnavailable = plat === "Temu" && count === 0;
            return (
              <button
                key={plat}
                type="button"
                onClick={() => setSelectedReviewPlatform(plat)}
                className={`px-3 py-1 rounded-xl text-xs font-bold transition-all border cursor-pointer ${
                  selectedReviewPlatform === plat
                    ? "bg-[#A855F7] text-white border-[#A855F7]"
                    : "bg-[#12121C] text-[#A1A1B5] border-[#303047] hover:border-[#A855F7]/40"
                }`}
              >
                {plat === "All" ? "All Platforms" : plat}
                {isUnavailable ? " (Unavailable)" : ` (${count})`}
              </button>
            );
          })}
        </div>

        {/* Sentiment Distribution Cards */}
        {selectedReviewPlatform === "Temu" && temuReviews.length === 0 ? (
          <div className="p-4 bg-[#12121C] rounded-2xl border border-[#303047] text-xs text-[#A1A1B5] space-y-1">
            <div className="flex items-center gap-2 text-[#F59E0B] font-bold">
              <AlertTriangle className="w-4 h-4" />
              <span>Temu Review Data Unavailable</span>
            </div>
            <p className="leading-relaxed">
              Customer review data is currently unavailable for Temu. Genuine review analysis is only reported when verified customer reviews can be retrieved from public endpoints.
            </p>
          </div>
        ) : activeTotal > 0 ? (
          <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
              {/* Positive */}
              <div className="p-5 rounded-2xl bg-[#12121C] border border-[#303047] space-y-2.5">
                <div className="flex items-center justify-between text-[#22C55E] text-xs font-bold">
                  <span>Positive Feedback</span>
                  <ThumbsUp className="w-4 h-4 text-[#22C55E]" />
                </div>
                <div className="text-2xl font-black text-[#F8FAFC]">
                  {selectedReviewPlatform === "All"
                    ? (sentimentStats?.positive_count ?? activePosCount)
                    : activePosCount}
                </div>
                <div className="w-full bg-[#202033] rounded-full h-1.5 overflow-hidden">
                  <div
                    className="bg-[#22C55E] h-1.5 rounded-full"
                    style={{
                      width: `${selectedReviewPlatform === "All" ? (sentimentStats?.positive_percentage ?? activePosPct) : activePosPct}%`,
                    }}
                  />
                </div>
                <p className="text-[11px] text-[#A1A1B5]">
                  {selectedReviewPlatform === "All" ? (sentimentStats?.positive_percentage ?? activePosPct) : activePosPct}% of platform reviews
                </p>
              </div>

              {/* Neutral */}
              <div className="p-5 rounded-2xl bg-[#12121C] border border-[#303047] space-y-2.5">
                <div className="flex items-center justify-between text-[#A1A1B5] text-xs font-bold">
                  <span>Neutral Feedback</span>
                  <MinusCircle className="w-4 h-4 text-[#A1A1B5]" />
                </div>
                <div className="text-2xl font-black text-[#F8FAFC]">
                  {selectedReviewPlatform === "All"
                    ? (sentimentStats?.neutral_count ?? activeNeuCount)
                    : activeNeuCount}
                </div>
                <div className="w-full bg-[#202033] rounded-full h-1.5 overflow-hidden">
                  <div
                    className="bg-[#A1A1B5] h-1.5 rounded-full"
                    style={{
                      width: `${selectedReviewPlatform === "All" ? (sentimentStats?.neutral_percentage ?? activeNeuPct) : activeNeuPct}%`,
                    }}
                  />
                </div>
                <p className="text-[11px] text-[#A1A1B5]">
                  {selectedReviewPlatform === "All" ? (sentimentStats?.neutral_percentage ?? activeNeuPct) : activeNeuPct}% of platform reviews
                </p>
              </div>

              {/* Negative */}
              <div className="p-5 rounded-2xl bg-[#12121C] border border-[#303047] space-y-2.5">
                <div className="flex items-center justify-between text-[#F87171] text-xs font-bold">
                  <span>Critical Feedback</span>
                  <ThumbsDown className="w-4 h-4 text-[#F87171]" />
                </div>
                <div className="text-2xl font-black text-[#F8FAFC]">
                  {selectedReviewPlatform === "All"
                    ? (sentimentStats?.negative_count ?? activeNegCount)
                    : activeNegCount}
                </div>
                <div className="w-full bg-[#202033] rounded-full h-1.5 overflow-hidden">
                  <div
                    className="bg-[#F87171] h-1.5 rounded-full"
                    style={{
                      width: `${selectedReviewPlatform === "All" ? (sentimentStats?.negative_percentage ?? activeNegPct) : activeNegPct}%`,
                    }}
                  />
                </div>
                <p className="text-[11px] text-[#A1A1B5]">
                  {selectedReviewPlatform === "All" ? (sentimentStats?.negative_percentage ?? activeNegPct) : activeNegPct}% of platform reviews
                </p>
              </div>
            </div>

            {/* Themes Section */}
            {((reviewData?.positive_themes && reviewData.positive_themes.length > 0) ||
              (reviewData?.negative_themes && reviewData.negative_themes.length > 0)) && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {reviewData?.positive_themes && reviewData.positive_themes.length > 0 && (
                  <div className="p-4 rounded-2xl bg-[#12121C] border border-[#303047] space-y-2">
                    <div className="flex items-center gap-1.5 text-xs font-bold text-[#22C55E]">
                      <ThumbsUp className="w-3.5 h-3.5" />
                      <span>Common Positive Themes</span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {reviewData.positive_themes.map((t, idx) => (
                        <span
                          key={idx}
                          className="text-[11px] px-2.5 py-0.5 rounded bg-[#22C55E]/10 text-[#22C55E] border border-[#22C55E]/20"
                        >
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {reviewData?.negative_themes && reviewData.negative_themes.length > 0 && (
                  <div className="p-4 rounded-2xl bg-[#12121C] border border-[#303047] space-y-2">
                    <div className="flex items-center gap-1.5 text-xs font-bold text-[#F87171]">
                      <ThumbsDown className="w-3.5 h-3.5" />
                      <span>Common Critical Themes</span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {reviewData.negative_themes.map((t, idx) => (
                        <span
                          key={idx}
                          className="text-[11px] px-2.5 py-0.5 rounded bg-[#F87171]/10 text-[#F87171] border border-[#F87171]/20"
                        >
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            <div className="p-3 bg-[#12121C] rounded-xl border border-[#303047] text-xs text-[#A1A1B5] flex items-center justify-between">
              <span>
                Overall Sentiment Consensus:{" "}
                <strong className="text-[#F8FAFC] capitalize">
                  {reviewData?.sentiment_label || "Evaluated"}
                </strong>
              </span>
              <button
                type="button"
                onClick={() => setIsReviewModalOpen(true)}
                className="text-xs font-bold text-[#A855F7] hover:text-[#EC4899] underline cursor-pointer"
              >
                Inspect All {allCustomerReviews.length} Reviews →
              </button>
            </div>
          </div>
        ) : (
          <div className="p-4 bg-[#12121C] rounded-2xl border border-[#303047] text-xs text-[#A1A1B5]">
            No customer reviews were extracted from marketplace sources for NLP sentiment breakdown.
          </div>
        )}

        {/* Review Credibility Insights */}
        <div className="p-5 rounded-2xl bg-[#12121C] border border-[#303047] space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-[#A855F7]" />
              <h4 className="text-xs font-extrabold uppercase tracking-wider text-[#F8FAFC]">
                Review Credibility Assessment
              </h4>
            </div>
            <span className="text-[10px] font-bold uppercase px-2.5 py-0.5 rounded-full bg-[#22C55E]/15 text-[#22C55E] border border-[#22C55E]/30 flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3 text-[#22C55E]" />
              <span>Pattern Consistent</span>
            </span>
          </div>

          <p className="text-xs text-[#A1A1B5] leading-relaxed">
            {reviewData?.credibility_assessment_label ||
              (isSimulatedReviews
                ? "Illustrative credibility analysis of simulated reviews."
                : "No anomalous posting bursts, repetitive review text patterns, or contradictory rating signals were observed.")}
          </p>

          <p className="text-[11px] text-[#A1A1B5]/60 italic pt-1 border-t border-[#303047]">
            Credibility indicators identify heuristic review patterns to assist buyers; they do not conclusively prove or disprove review authenticity.
          </p>
        </div>
      </div>

      {/* 6. Section E: Marketplace Recommendation */}
      <div className="bg-[#202033] rounded-3xl p-6 sm:p-8 text-[#F8FAFC] space-y-6 shadow-xl border border-[#303047]">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#303047] pb-4">
          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-2xl bg-[#EC4899]/15 border border-[#EC4899]/30 flex items-center justify-center text-[#EC4899]">
              <Award className="w-5 h-5 text-[#EC4899]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-extrabold uppercase tracking-widest text-[#EC4899]">
                  Section E: Marketplace Recommendation
                </span>
                <span
                  className={`text-[10px] font-extrabold uppercase px-2 py-0.5 rounded border ${
                    recommendedPlatform?.is_demo
                      ? "bg-[#A855F7]/15 text-[#A855F7] border-[#A855F7]/30"
                      : recommendedPlatform
                      ? "bg-[#22C55E]/15 text-[#22C55E] border-[#22C55E]/30"
                      : "bg-[#F59E0B]/15 text-[#F59E0B] border-[#F59E0B]/30"
                  }`}
                >
                  {recommendedPlatform?.recommendation_type ||
                    (recommendedPlatform?.is_demo
                      ? "DEMO RECOMMENDATION — BASED ON SIMULATED DATA"
                      : recommendedPlatform
                      ? "LIVE-DATA RECOMMENDATION"
                      : "Recommendation unavailable")}
                </span>
              </div>
              <h3 className="text-xl sm:text-2xl font-black text-[#F8FAFC]">
                {recommendedPlatform ? recommendedPlatform.platform : "Direct Search Available"}
              </h3>
            </div>
          </div>

          {recommendedPlatform && recommendedPlatform.listing && recommendedPlatform.listing.price ? (
            <div className="sm:text-right">
              <div className="text-xs text-[#A1A1B5]">Recommended Listing Price</div>
              <div className="text-2xl font-black text-[#22C55E]">
                {formatPrice(recommendedPlatform.listing.price, recommendedPlatform.listing.currency)}
              </div>
            </div>
          ) : null}
        </div>

        {recommendedPlatform && recommendedPlatform.listing ? (
          <div className="space-y-5">
            <div className="p-6 bg-[#12121C] rounded-2xl border border-[#303047] space-y-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="space-y-1.5">
                  <h4 className="font-bold text-lg text-[#F8FAFC]">
                    {recommendedPlatform.listing.product_name}
                  </h4>
                  {recommendedPlatform.listing.seller_name && (
                    <p className="text-xs text-[#A1A1B5]">
                      Seller: <strong className="text-[#F8FAFC]">{recommendedPlatform.listing.seller_name}</strong>
                    </p>
                  )}
                </div>

                <div className="flex items-center gap-3">
                  {recommendedPlatform.listing.rating && recommendedPlatform.listing.rating > 0 ? (
                    <div className="flex items-center gap-1.5 text-[#F59E0B] text-sm font-bold bg-[#191925] px-3.5 py-1.5 rounded-xl border border-[#303047]">
                      <Star className="w-4 h-4 fill-[#F59E0B] text-[#F59E0B]" />
                      <span>{recommendedPlatform.listing.rating.toFixed(1)}</span>
                    </div>
                  ) : null}
                  <span className="text-xs text-[#A1A1B5]">
                    ({recommendedPlatform.listing.review_count || 0} reviews)
                  </span>
                </div>
              </div>

              {/* 5-Factor Score Breakdown */}
              <div className="pt-4 border-t border-[#303047] space-y-3">
                <div className="text-xs font-bold text-[#A1A1B5] uppercase tracking-wider flex items-center justify-between">
                  <span>Recommendation Scoring Formula (Total: {recommendedPlatform.total_score}/100)</span>
                  <span className="text-[11px] text-[#A855F7] font-semibold">Configured 5-Factor Weights</span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-center text-xs">
                  <div className="p-3.5 rounded-xl bg-[#191925] border border-[#303047]">
                    <div className="text-[10px] text-[#A1A1B5]">Product Match (35%)</div>
                    <div className="text-sm font-bold text-[#F8FAFC]">
                      {recommendedPlatform.score_breakdown.match_confidence_score}%
                    </div>
                  </div>
                  <div className="p-3.5 rounded-xl bg-[#191925] border border-[#303047]">
                    <div className="text-[10px] text-[#A1A1B5]">Rating/Volume (25%)</div>
                    <div className="text-sm font-bold text-[#F8FAFC]">
                      {recommendedPlatform.score_breakdown.rating_volume_score || recommendedPlatform.score_breakdown.rating_score}%
                    </div>
                  </div>
                  <div className="p-3.5 rounded-xl bg-[#191925] border border-[#303047]">
                    <div className="text-[10px] text-[#A1A1B5]">Seller Trust (20%)</div>
                    <div className="text-sm font-bold text-[#F8FAFC]">
                      {recommendedPlatform.score_breakdown.seller_trust_score}%
                    </div>
                  </div>
                  <div className="p-3.5 rounded-xl bg-[#191925] border border-[#303047]">
                    <div className="text-[10px] text-[#A1A1B5]">Price (10%)</div>
                    <div className="text-sm font-bold text-[#F8FAFC]">
                      {recommendedPlatform.score_breakdown.price_score || 85.0}%
                    </div>
                  </div>
                  <div className="p-3.5 rounded-xl bg-[#191925] border border-[#303047]">
                    <div className="text-[10px] text-[#A1A1B5]">Sentiment (10%)</div>
                    <div className="text-sm font-bold text-[#F8FAFC]">
                      {recommendedPlatform.score_breakdown.review_sentiment_score || 50.0}%
                    </div>
                  </div>
                </div>
              </div>

              {/* Rationale */}
              <div className="p-4 rounded-xl bg-[#191925] border border-[#303047] text-xs text-[#A1A1B5] flex items-start gap-2.5">
                <TrendingUp className="w-4 h-4 text-[#EC4899] shrink-0 mt-0.5" />
                <p className="leading-relaxed">
                  <strong className="text-[#F8FAFC]">Why this platform ranked highest:</strong>{" "}
                  {recommendedPlatform.recommendation_reason ||
                    "This listing offers the best composite score across verified seller reputation, product catalog matching, customer ratings, and price competitiveness."}
                </p>
              </div>
            </div>

            {recommendedPlatform.listing.product_url && (
              <a
                href={recommendedPlatform.listing.product_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center gap-2 w-full sm:w-auto px-6 py-3.5 text-xs font-bold text-white bg-gradient-to-r from-[#EC4899] via-[#A855F7] to-[#8B5CF6] hover:opacity-95 rounded-xl transition-all shadow-md touch-manipulation min-h-[44px] cursor-pointer"
              >
                <span>View Product on {recommendedPlatform.platform}</span>
                <ExternalLink className="w-4 h-4" />
              </a>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            <p className="text-xs sm:text-sm text-[#A1A1B5] leading-relaxed">
              Recommendation unavailable: insufficient comparable marketplace data. Explore product listings directly on supported e-commerce marketplaces:
            </p>

            <div className="flex flex-wrap gap-3">
              <a
                href={darazSearchUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2.5 bg-[#f57224]/15 hover:bg-[#f57224]/25 text-[#f57224] border border-[#f57224]/30 rounded-xl text-xs font-bold transition-colors"
              >
                <span>Search on Daraz LK</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
              <a
                href={amazonSearchUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2.5 bg-[#ff9900]/15 hover:bg-[#ff9900]/25 text-[#ff9900] border border-[#ff9900]/30 rounded-xl text-xs font-bold transition-colors"
              >
                <span>Search on Amazon</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
              <a
                href={temuSearchUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2.5 bg-[#fb7701]/15 hover:bg-[#fb7701]/25 text-[#fb7701] border border-[#fb7701]/30 rounded-xl text-xs font-bold transition-colors"
              >
                <span>Search on Temu</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Action Footer */}
      <div className="pt-4 border-t border-[#303047] flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-xs text-[#A1A1B5] font-medium">
          <CheckCircle2 className="w-4 h-4 text-[#22C55E]" />
          <span>Product verification, review analysis, and marketplace recommendation completed</span>
        </div>

        <button
          type="button"
          onClick={onReset}
          className="inline-flex items-center gap-2 px-5 py-2.5 text-xs font-bold text-[#F8FAFC] bg-[#12121C] hover:bg-[#202033] border border-[#303047] rounded-xl shadow-xs transition-colors touch-manipulation min-h-[44px] cursor-pointer"
        >
          <RotateCcw className="w-4 h-4 text-[#A855F7]" />
          <span>Verify Another Product</span>
        </button>
      </div>

      {/* Functional Review Analysis Modal */}
      <ReviewAnalysisModal
        isOpen={isReviewModalOpen}
        onClose={() => setIsReviewModalOpen(false)}
        reviews={(selectedReviewPlatform === "All" ? allCustomerReviews : activeReviews) as ReviewItem[]}
        sentimentStats={sentimentStats}
        sentimentLabel={reviewData?.sentiment_label}
        isSimulated={isSimulatedReviews}
        simulationTitle={reviewData?.simulation_title}
        simulationDisclosure={reviewData?.simulation_disclosure}
        credibilityLabel={reviewData?.credibility_assessment_label}
        positiveThemes={reviewData?.positive_themes}
        negativeThemes={reviewData?.negative_themes}
      />
    </div>
  );
}
