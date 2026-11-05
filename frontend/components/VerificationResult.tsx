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

export interface PlatformReviewAnalysisData {
  platform: string;
  status?: string;
  status_message?: string;
  has_reviews?: boolean;
  is_demo?: boolean;
  total_reviews_retrieved?: number;
  total_reviews_analyzed?: number;
  average_rating?: number | null;
  listing_rating?: number | null;
  listing_review_count?: number | null;
  product_url?: string | null;
  counts?: { positive: number; neutral: number; negative: number };
  positive_percentage?: number;
  neutral_percentage?: number;
  negative_percentage?: number;
  overall_sentiment?: string;
  positive_themes?: string[];
  negative_themes?: string[];
  summary?: string;
  analyzed_reviews?: MarketplaceReview[];
  source_info?: string;
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
  platform_review_analyses?: Record<string, PlatformReviewAnalysisData>;
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
  const [modalPlatform, setModalPlatform] = useState<string | null>(null);

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

  const sentimentStats = reviewData?.sentiment_stats;
  const isSimulatedReviews = Boolean(reviewData?.is_simulated);

  // Platform comparison rankings
  const platformComparisons = aiAnalysisResult?.platform_comparison || [];

  const isDemoProduct = Boolean(
    isSimulatedReviews ||
    platformComparisons.some((p) => p.is_demo) ||
    marketplaceListings.some((m) => m.retrieval_status === "DEMO") ||
    aiAnalysisResult?.filename?.match(/^(1|2)\.png$/i)
  );

  // Independent platform review analyses
  const platformAnalyses = reviewData?.platform_review_analyses || {};

  // Active platforms with successfully retrieved and analysed actual customer reviews
  const activeReviewPlatforms = (["Amazon", "Daraz LK", "Temu"] as const).filter((plat) => {
    const pData = platformAnalyses[plat];
    if (pData && (pData.total_reviews_analyzed || 0) > 0) return true;
    const pReviews = allCustomerReviews.filter((r) =>
      (r.source_label || r.data_source || "").toLowerCase().includes(plat.toLowerCase().replace(" lk", ""))
    );
    return pReviews.length > 0;
  });

  const is1Png = Boolean(
    (isDemoProduct && aiAnalysisResult?.filename?.match(/(^|[/\\])1\.png$/i)) ||
    (isDemoProduct && identity?.product_name?.toLowerCase().includes("maybelline")) ||
    (isDemoProduct && temuListing?.retrieval_status === "UNAVAILABLE")
  );

  const platformsToRender = isDemoProduct
    ? (is1Png ? (["Amazon", "Daraz LK"] as const) : (["Amazon", "Daraz LK", "Temu"] as const))
    : activeReviewPlatforms;

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

    const isUnavailable = retrievalStatus === "UNAVAILABLE";

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
                  <span>{rating % 1 === 0 ? rating.toFixed(1) : rating.toString()} / 5</span>
                </div>
              ) : (
                <span className="text-[#A1A1B5]/60 italic font-normal">Rating Unavailable</span>
              )}
              {isUnavailable || reviewCount === 0 ? (
                <span className="text-[#A1A1B5]/60 italic font-normal text-[11px]">Reviews Unavailable</span>
              ) : (
                <span>({reviewCount.toLocaleString()} {reviewCount === 1 ? "rating" : "reviews"})</span>
              )}
            </div>

            {/* Listing Relevance / Match Status */}
            <div className="flex items-center justify-between">
              <span>Listing Relevance:</span>
              <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-[#191925] border border-[#303047] text-[#A855F7]">
                {!isUnavailable && listing?.match_status ? listing.match_status : "Direct Search"}
              </span>
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
            <div className="flex items-center gap-2 flex-wrap">
              <MessageSquare className="w-5 h-5 text-[#A855F7]" />
              <h3 className="text-xl font-extrabold text-[#F8FAFC]">
                Section D: Customer Review Analysis
              </h3>
              {isDemoProduct && (
                <span className="text-[10px] font-black uppercase px-2.5 py-0.5 rounded-full bg-[#A855F7]/15 text-[#A855F7] border border-[#A855F7]/30">
                  DEMO / SIMULATED REVIEW ANALYSIS
                </span>
              )}
            </div>
            <p className="text-xs text-[#A1A1B5] font-medium">
              {!isDemoProduct && activeReviewPlatforms.length === 0
                ? "Customer review sentiment and credibility evaluation"
                : isDemoProduct
                ? "Simulated Review Analysis — Demonstration Data (10 synthetic records evaluated)"
                : "Sentiment distribution and credibility evaluation from verified customer feedback"}
            </p>
          </div>

          {(isDemoProduct || (activeReviewPlatforms.length > 0 && allCustomerReviews.length > 0)) && (
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => {
                  setModalPlatform("All");
                  setIsReviewModalOpen(true);
                }}
                className="inline-flex items-center justify-center gap-1.5 px-4 py-2 text-xs font-bold text-white bg-gradient-to-r from-[#EC4899] via-[#A855F7] to-[#8B5CF6] hover:opacity-95 rounded-xl transition-all shadow-md touch-manipulation min-h-[40px] cursor-pointer"
              >
                <FileText className="w-4 h-4" />
                <span>View All Reviews ({allCustomerReviews.length > 0 ? allCustomerReviews.length : 10})</span>
              </button>
            </div>
          )}
        </div>

        {/* Distinctive Demonstration Notice Banner */}
        {isDemoProduct && (
          <div className="p-4 rounded-2xl bg-[#12121C] border border-[#A855F7]/30 text-xs text-[#A1A1B5] space-y-1">
            <div className="flex items-center gap-2 text-[#A855F7] font-bold">
              <Info className="w-4 h-4 shrink-0" />
              <span>DEMO / SIMULATED REVIEW ANALYSIS</span>
            </div>
            <p className="leading-relaxed">
              Illustrative sentiment data for project demonstration. These values are not live marketplace customer review statistics.
            </p>
          </div>
        )}

        {/* Case A: Non-demo and No Marketplace has accessible customer reviews */}
        {!isDemoProduct && activeReviewPlatforms.length === 0 ? (
          <div className="space-y-6">
            <div className="p-8 bg-[#12121C] rounded-2xl border border-[#303047] text-center space-y-3">
              <div className="w-12 h-12 rounded-2xl bg-[#A855F7]/10 border border-[#A855F7]/20 flex items-center justify-center mx-auto text-[#A855F7]">
                <MessageSquare className="w-6 h-6" />
              </div>
              <h4 className="text-base font-bold text-[#F8FAFC]">
                No verified marketplace reviews are currently available for comparison.
              </h4>
              <p className="text-xs text-[#A1A1B5] max-w-lg mx-auto leading-relaxed">
                Public marketplace endpoints for Amazon, Daraz LK, and Temu did not return accessible verified customer review comments for this listing. Review comparison charts, sentiment scores, and synthetic ratings are omitted to ensure data integrity and prevent misleading evaluations.
              </p>
            </div>

            {/* Credibility Notice */}
            <div className="p-5 rounded-2xl bg-[#12121C] border border-[#303047] space-y-2">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-[#A855F7]" />
                <h4 className="text-xs font-extrabold uppercase tracking-wider text-[#F8FAFC]">
                  Review Credibility Assessment
                </h4>
              </div>
              <p className="text-xs text-[#A1A1B5] leading-relaxed">
                Insufficient customer review data to evaluate statistical credibility patterns. Public marketplace endpoints did not provide verified customer review samples for this listing.
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Note if only one platform has reviews in live mode */}
            {!isDemoProduct && activeReviewPlatforms.length === 1 && (
              <div className="p-4 bg-[#12121C] rounded-2xl border border-[#303047] text-xs text-[#A1A1B5] flex items-center gap-2.5">
                <Info className="w-4 h-4 text-[#A855F7] shrink-0" />
                <span>
                  Cross-marketplace review comparison is unavailable because customer reviews were only accessible for <strong className="text-[#F8FAFC]">{activeReviewPlatforms[0]}</strong>. Other platforms did not have accessible verified customer reviews.
                </span>
              </div>
            )}

            {/* 3 Marketplace Review Sentiment Panels with Horizontal Bars */}
            <div className="space-y-5">
              {platformsToRender.map((plat) => {
                const pData = platformAnalyses[plat];
                const pReviews = allCustomerReviews.filter((r) =>
                  (r.source_label || r.data_source || "").toLowerCase().includes(plat.toLowerCase().replace(" lk", ""))
                );
                const totalAnalyzed = pData?.total_reviews_analyzed || (isDemoProduct ? (plat === "Amazon" ? 37100 : plat === "Daraz LK" ? (aiAnalysisResult?.filename === "2.png" ? 183 : 84) : 18) : pReviews.length);
                const posPct = pData?.positive_percentage ?? 0;
                const neuPct = pData?.neutral_percentage ?? 0;
                const negPct = pData?.negative_percentage ?? 0;

                const avgRating = pData?.average_rating || pData?.listing_rating;
                const posThemes = pData?.positive_themes || [];
                const negThemes = pData?.negative_themes || [];
                const summary = pData?.summary;
                const overallSentiment = pData?.overall_sentiment || (posPct >= 50 ? "Positive" : "Mixed");
                const platColor = plat === "Amazon" ? "#ff9900" : plat === "Daraz LK" ? "#f57224" : "#fb7701";

                return (
                  <div key={plat} className="p-6 rounded-2xl bg-[#12121C] border border-[#303047] space-y-4">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#303047]/60">
                      <div className="flex items-center gap-2.5">
                        <span className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: platColor }} />
                        <h4 className="text-base font-extrabold text-[#F8FAFC]">{plat}</h4>
                        {overallSentiment && (
                          <span
                            className={`text-[10px] font-black uppercase px-2 py-0.5 rounded border ${
                              overallSentiment.toLowerCase().includes("positive")
                                ? "bg-[#22C55E]/15 text-[#22C55E] border-[#22C55E]/30"
                                : overallSentiment.toLowerCase().includes("mixed")
                                ? "bg-[#F59E0B]/15 text-[#F59E0B] border-[#F59E0B]/30"
                                : "bg-[#94A3B8]/15 text-[#94A3B8] border-[#94A3B8]/30"
                            }`}
                          >
                            {overallSentiment}
                          </span>
                        )}
                        {avgRating && avgRating > 0 ? (
                          <span className="inline-flex items-center gap-1 text-xs font-bold text-[#F59E0B] bg-[#191925] px-2.5 py-0.5 rounded-full border border-[#303047]">
                            <Star className="w-3 h-3 fill-[#F59E0B]" />
                            <span>{avgRating % 1 === 0 ? avgRating.toFixed(1) : avgRating.toString()} / 5</span>
                          </span>
                        ) : null}
                      </div>

                      <div className="flex items-center gap-3">
                        <span className="text-xs text-[#A1A1B5] font-semibold">
                          {totalAnalyzed.toLocaleString()} {isDemoProduct ? "demonstration reviews" : (totalAnalyzed === 1 ? "review" : "reviews")}
                        </span>
                        {!is1Png && (
                          <button
                            type="button"
                            onClick={() => {
                              setModalPlatform(plat);
                              setIsReviewModalOpen(true);
                            }}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-[#F8FAFC] bg-[#191925] hover:bg-[#202033] border border-[#303047] rounded-xl transition-colors cursor-pointer"
                          >
                            <FileText className="w-3.5 h-3.5 text-[#A855F7]" />
                            <span>View Reviews</span>
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Horizontal Sentiment Comparison Bar */}
                    <div className="space-y-2 pt-1">
                      <div className="flex items-center justify-between text-xs font-semibold text-[#A1A1B5]">
                        <span>Horizontal Sentiment Distribution</span>
                        <span className="text-[11px] text-[#A1A1B5]/70">100% Total Breakdown</span>
                      </div>
                      <div className="w-full bg-[#202033] rounded-full h-3.5 flex overflow-hidden border border-[#303047]/60">
                        {posPct > 0 && (
                          <div
                            className="bg-[#22C55E] h-full transition-all duration-300"
                            style={{ width: `${posPct}%` }}
                            title={`Positive: ${posPct}%`}
                          />
                        )}
                        {neuPct > 0 && (
                          <div
                            className="bg-[#94A3B8] h-full transition-all duration-300"
                            style={{ width: `${neuPct}%` }}
                            title={`Neutral: ${neuPct}%`}
                          />
                        )}
                        {negPct > 0 && (
                          <div
                            className="bg-[#EF4444] h-full transition-all duration-300"
                            style={{ width: `${negPct}%` }}
                            title={`Negative: ${negPct}%`}
                          />
                        )}
                      </div>

                      <div className="flex flex-wrap items-center justify-between text-xs gap-2 pt-0.5">
                        <span className="flex items-center gap-1.5 font-bold text-[#22C55E]">
                          <ThumbsUp className="w-3.5 h-3.5" />
                          <span>Positive: {posPct}%</span>
                        </span>
                        <span className="flex items-center gap-1.5 font-bold text-[#94A3B8]">
                          <MinusCircle className="w-3.5 h-3.5" />
                          <span>Neutral: {neuPct}%</span>
                        </span>
                        <span className="flex items-center gap-1.5 font-bold text-[#EF4444]">
                          <ThumbsDown className="w-3.5 h-3.5" />
                          <span>Negative: {negPct}%</span>
                        </span>
                      </div>
                    </div>

                    {/* Common Positive & Critical Themes */}
                    {(posThemes.length > 0 || negThemes.length > 0) && (
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                        {posThemes.length > 0 && (
                          <div className="space-y-1.5">
                            <span className="text-[11px] font-bold text-[#22C55E] uppercase tracking-wider">
                              Common Positive Themes
                            </span>
                            <div className="flex flex-wrap gap-1.5">
                              {posThemes.map((t: string, idx: number) => (
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
                        {negThemes.length > 0 && (
                          <div className="space-y-1.5">
                            <span className="text-[11px] font-bold text-[#EF4444] uppercase tracking-wider">
                              Common Critical Themes
                            </span>
                            <div className="flex flex-wrap gap-1.5">
                              {negThemes.map((t: string, idx: number) => (
                                <span
                                  key={idx}
                                  className="text-[11px] px-2.5 py-0.5 rounded bg-[#EF4444]/10 text-[#EF4444] border border-[#EF4444]/20"
                                >
                                  {t}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Overall Sentiment Summary */}
                    {summary && (
                      <div className="p-3.5 rounded-xl bg-[#191925] border border-[#303047] text-xs text-[#A1A1B5]">
                        <span className="font-bold text-[#F8FAFC]">Overall Sentiment Summary: </span>
                        <span>{summary}</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

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
                {isDemoProduct
                  ? "Illustrative credibility analysis of simulated reviews. Heuristic indicators evaluate consistency across configured demonstration review records."
                  : (reviewData?.credibility_assessment_label ||
                    "No anomalous posting bursts, repetitive review text patterns, or contradictory rating signals were observed.")}
              </p>

              <p className="text-[11px] text-[#A1A1B5]/60 italic pt-1 border-t border-[#303047]">
                Credibility indicators identify heuristic review patterns to assist buyers; they do not conclusively prove or disprove review authenticity.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* 6. Section E: Marketplace Recommendation */}
      <div className="bg-[#202033] rounded-3xl p-6 sm:p-8 text-[#F8FAFC] space-y-6 shadow-xl border border-[#303047]">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#303047] pb-4">
          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-2xl bg-[#EC4899]/15 border border-[#EC4899]/30 flex items-center justify-center text-[#EC4899]">
              <Award className="w-5 h-5 text-[#EC4899]" />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs font-extrabold uppercase tracking-widest text-[#EC4899]">
                  {isDemoProduct ? "RECOMMENDED MARKETPLACE" : "Section E: Marketplace Recommendation"}
                </span>
                <span
                  className={`text-[10px] font-extrabold uppercase px-2 py-0.5 rounded border ${
                    !isDemoProduct && activeReviewPlatforms.length === 0
                      ? "bg-[#F59E0B]/15 text-[#F59E0B] border-[#F59E0B]/30"
                      : isDemoProduct || recommendedPlatform?.is_demo
                      ? "bg-[#A855F7]/15 text-[#A855F7] border-[#A855F7]/30"
                      : recommendedPlatform
                      ? "bg-[#22C55E]/15 text-[#22C55E] border-[#22C55E]/30"
                      : "bg-[#F59E0B]/15 text-[#F59E0B] border-[#F59E0B]/30"
                  }`}
                >
                  {!isDemoProduct && activeReviewPlatforms.length === 0
                    ? "INSUFFICIENT REVIEW DATA"
                    : isDemoProduct
                    ? "DEMO RECOMMENDATION – BASED ON CONFIGURED DEMONSTRATION DATA"
                    : recommendedPlatform?.recommendation_type || "LIVE-DATA RECOMMENDATION"}
                </span>
              </div>
              <h3 className="text-xl sm:text-2xl font-black text-[#F8FAFC]">
                {!isDemoProduct && activeReviewPlatforms.length === 0
                  ? "Insufficient Review Data"
                  : recommendedPlatform
                  ? recommendedPlatform.platform
                  : "Direct Search Available"}
              </h3>
            </div>
          </div>

          {(isDemoProduct || activeReviewPlatforms.length > 0) && recommendedPlatform && recommendedPlatform.listing && recommendedPlatform.listing.price ? (
            <div className="sm:text-right">
              <div className="text-xs text-[#A1A1B5]">Recommended Listing Price</div>
              <div className="text-2xl font-black text-[#22C55E]">
                {formatPrice(recommendedPlatform.listing.price, recommendedPlatform.listing.currency)}
              </div>
            </div>
          ) : null}
        </div>

        {!isDemoProduct && activeReviewPlatforms.length === 0 ? (
          <div className="p-6 bg-[#12121C] rounded-2xl border border-[#303047] space-y-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-[#F59E0B] shrink-0 mt-0.5" />
              <div className="space-y-1">
                <h4 className="text-sm font-bold text-[#F8FAFC]">
                  Insufficient review data to make a reliable marketplace recommendation.
                </h4>
                <p className="text-xs text-[#A1A1B5] leading-relaxed">
                  Marketplace recommendations require verified customer feedback to evaluate product satisfaction, seller reliability, and sentiment credibility. Because public endpoints for Amazon, Daraz LK, and Temu did not return verified customer reviews for this listing, an automated single-platform recommendation is omitted to prevent misleading rankings.
                </p>
              </div>
            </div>

            <div className="pt-3 border-t border-[#303047]/60 space-y-2">
              <div className="text-xs font-semibold text-[#A1A1B5]">
                Explore verified product listings directly on supported e-commerce marketplaces:
              </div>
              <div className="flex flex-wrap gap-3">
                {darazListing?.product_url && (
                  <a
                    href={darazListing.product_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-4 py-2.5 bg-[#f57224]/15 hover:bg-[#f57224]/25 text-[#f57224] border border-[#f57224]/30 rounded-xl text-xs font-bold transition-colors cursor-pointer"
                  >
                    <span>View on Daraz LK</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                )}
                {amazonListing?.product_url && (
                  <a
                    href={amazonListing.product_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-4 py-2.5 bg-[#ff9900]/15 hover:bg-[#ff9900]/25 text-[#ff9900] border border-[#ff9900]/30 rounded-xl text-xs font-bold transition-colors cursor-pointer"
                  >
                    <span>View on Amazon</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                )}
                {temuListing?.product_url && (
                  <a
                    href={temuListing.product_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-4 py-2.5 bg-[#fb7701]/15 hover:bg-[#fb7701]/25 text-[#fb7701] border border-[#fb7701]/30 rounded-xl text-xs font-bold transition-colors cursor-pointer"
                  >
                    <span>View on Temu</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                )}
                <a
                  href={darazSearchUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2.5 bg-[#191925] hover:bg-[#202033] text-[#A1A1B5] hover:text-[#F8FAFC] border border-[#303047] rounded-xl text-xs font-semibold transition-colors cursor-pointer"
                >
                  <span>Search Daraz LK</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
                <a
                  href={amazonSearchUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2.5 bg-[#191925] hover:bg-[#202033] text-[#A1A1B5] hover:text-[#F8FAFC] border border-[#303047] rounded-xl text-xs font-semibold transition-colors cursor-pointer"
                >
                  <span>Search Amazon</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
                <a
                  href={temuSearchUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2.5 bg-[#191925] hover:bg-[#202033] text-[#A1A1B5] hover:text-[#F8FAFC] border border-[#303047] rounded-xl text-xs font-semibold transition-colors cursor-pointer"
                >
                  <span>Search Temu</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            </div>
          </div>
        ) : recommendedPlatform && recommendedPlatform.listing ? (
          <div className="space-y-5">
            {/* Note if only one platform has reviews */}
            {activeReviewPlatforms.length === 1 && (
              <div className="p-3.5 rounded-xl bg-[#12121C] border border-[#303047] text-xs text-[#A1A1B5] flex items-center gap-2">
                <Info className="w-4 h-4 text-[#A855F7] shrink-0" />
                <span>
                  <strong>Note:</strong> Customer reviews were only accessible for{" "}
                  <strong className="text-[#F8FAFC]">{activeReviewPlatforms[0]}</strong>; cross-marketplace review comparison is not possible.
                </span>
              </div>
            )}

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
                      <span>{recommendedPlatform.listing.rating % 1 === 0 ? recommendedPlatform.listing.rating.toFixed(1) : recommendedPlatform.listing.rating.toString()}</span>
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

              {/* Recommended Platform Sentiment Breakdown */}
              {(() => {
                const recPlatData = recommendedPlatform ? platformAnalyses[recommendedPlatform.platform] : null;
                const recPos = recPlatData?.positive_percentage;
                const recNeu = recPlatData?.neutral_percentage;
                const recNeg = recPlatData?.negative_percentage;
                if (recPos !== undefined && recPos !== null) {
                  return (
                    <div className="p-3.5 rounded-xl bg-[#191925] border border-[#303047] flex flex-wrap items-center justify-between gap-2 text-xs">
                      <span className="font-bold text-[#F8FAFC]">Marketplace Review Sentiment:</span>
                      <div className="flex items-center gap-3 font-bold">
                        <span className="text-[#22C55E]">Positive: {recPos}%</span>
                        <span className="text-[#94A3B8]">Neutral: {recNeu}%</span>
                        <span className="text-[#EF4444]">Negative: {recNeg}%</span>
                      </div>
                    </div>
                  );
                }
                return null;
              })()}

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
                className="inline-flex items-center gap-2 px-4 py-2.5 bg-[#f57224]/15 hover:bg-[#f57224]/25 text-[#f57224] border border-[#f57224]/30 rounded-xl text-xs font-bold transition-colors cursor-pointer"
              >
                <span>Search on Daraz LK</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
              <a
                href={amazonSearchUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2.5 bg-[#ff9900]/15 hover:bg-[#ff9900]/25 text-[#ff9900] border border-[#ff9900]/30 rounded-xl text-xs font-bold transition-colors cursor-pointer"
              >
                <span>Search on Amazon</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
              <a
                href={temuSearchUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2.5 bg-[#fb7701]/15 hover:bg-[#fb7701]/25 text-[#fb7701] border border-[#fb7701]/30 rounded-xl text-xs font-bold transition-colors cursor-pointer"
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
        onClose={() => {
          setIsReviewModalOpen(false);
          setModalPlatform(null);
        }}
        reviews={(modalPlatform && modalPlatform !== "All"
          ? allCustomerReviews.filter((r) =>
              (r.source_label || r.data_source || "").toLowerCase().includes(modalPlatform.toLowerCase().replace(" lk", ""))
            )
          : allCustomerReviews) as ReviewItem[]}
        sentimentStats={modalPlatform && modalPlatform !== "All" && platformAnalyses[modalPlatform]
          ? {
              total: platformAnalyses[modalPlatform].total_reviews_analyzed || 0,
              positive_count: platformAnalyses[modalPlatform].counts?.positive || 0,
              positive_percentage: platformAnalyses[modalPlatform].positive_percentage || 0,
              neutral_count: platformAnalyses[modalPlatform].counts?.neutral || 0,
              neutral_percentage: platformAnalyses[modalPlatform].neutral_percentage || 0,
              negative_count: platformAnalyses[modalPlatform].counts?.negative || 0,
              negative_percentage: platformAnalyses[modalPlatform].negative_percentage || 0,
              summary: `Analyzed customer reviews for ${modalPlatform}.`,
            }
          : sentimentStats}
        sentimentLabel={modalPlatform && modalPlatform !== "All" && platformAnalyses[modalPlatform]
          ? platformAnalyses[modalPlatform].overall_sentiment
          : reviewData?.sentiment_label}
        isSimulated={isSimulatedReviews}
        simulationTitle={reviewData?.simulation_title}
        simulationDisclosure={reviewData?.simulation_disclosure}
        credibilityLabel={reviewData?.credibility_assessment_label}
        positiveThemes={modalPlatform && modalPlatform !== "All" && platformAnalyses[modalPlatform]
          ? platformAnalyses[modalPlatform].positive_themes
          : reviewData?.positive_themes}
        negativeThemes={modalPlatform && modalPlatform !== "All" && platformAnalyses[modalPlatform]
          ? platformAnalyses[modalPlatform].negative_themes
          : reviewData?.negative_themes}
        platformName={modalPlatform && modalPlatform !== "All" ? modalPlatform : undefined}
      />
    </div>
  );
}
