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
  const [selectedPlatformForModal, setSelectedPlatformForModal] = useState<"Amazon" | "Daraz LK" | null>(null);

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

  // Central Bank of Sri Lanka (CBSL) benchmark exchange rate: 1 USD ≈ 308.50 LKR
  const USD_TO_LKR_RATE = 308.50;

  interface PriceFormatted {
    formattedLkr: string;
    subtext: string | null;
    isAvailable: boolean;
  }

  // Format currency & price helper (Sri Lankan Rupees primary)
  const formatPriceLKR = (price?: number | null, currency?: string | null): PriceFormatted => {
    if (!price || price <= 0) {
      return {
        formattedLkr: "Unavailable",
        subtext: null,
        isAvailable: false,
      };
    }

    const curr = (currency || "USD").toUpperCase();
    if (curr === "LKR" || curr === "RS" || curr === "RS.") {
      return {
        formattedLkr: `LKR ${price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
        subtext: null,
        isAvailable: true,
      };
    }

    if (curr === "USD" || curr === "$") {
      const converted = price * USD_TO_LKR_RATE;
      return {
        formattedLkr: `LKR ${converted.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
        subtext: `(Converted from $${price.toFixed(2)} USD)`,
        isAvailable: true,
      };
    }

    return {
      formattedLkr: `${curr} ${price.toFixed(2)}`,
      subtext: null,
      isAvailable: true,
    };
  };

  // Collect customer reviews (simulated or real)
  const allCustomerReviews: MarketplaceReview[] =
    reviewData?.simulated_reviews && reviewData.simulated_reviews.length > 0
      ? reviewData.simulated_reviews
      : reviewData?.analyzed_reviews && reviewData.analyzed_reviews.length > 0
      ? reviewData.analyzed_reviews
      : marketplaceListings.flatMap((m) => m.reviews || []);

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

  // Interface for independent platform review analysis
  interface PlatformReviewAnalysisData {
    platform: string;
    status: "completed" | "insufficient_data" | "unavailable";
    status_message: string;
    has_reviews: boolean;
    total_reviews_retrieved: number;
    total_reviews_analyzed: number;
    counts: {
      positive: number;
      neutral: number;
      negative: number;
    };
    positive_percentage: number;
    neutral_percentage: number;
    negative_percentage: number;
    overall_sentiment: string;
    positive_themes: string[];
    negative_themes: string[];
    analyzed_reviews: MarketplaceReview[];
    source_info: string;
  }

  const platformAnalyses = (reviewData as any)?.platform_review_analyses || {};

  const getPlatformReviewData = (platformName: "Amazon" | "Daraz LK" | "Temu"): PlatformReviewAnalysisData => {
    if (platformAnalyses[platformName]) {
      return platformAnalyses[platformName];
    }

    if (platformName === "Temu") {
      return {
        platform: "Temu",
        status: "unavailable",
        status_message: "Temu review data is currently unavailable.",
        has_reviews: false,
        total_reviews_retrieved: 0,
        total_reviews_analyzed: 0,
        counts: { positive: 0, neutral: 0, negative: 0 },
        positive_percentage: 0.0,
        neutral_percentage: 0.0,
        negative_percentage: 0.0,
        overall_sentiment: "Unavailable",
        positive_themes: [],
        negative_themes: [],
        analyzed_reviews: [],
        source_info: "Temu public endpoint (Review data not retrievable via server HTML)",
      };
    }

    const listing = platformName === "Amazon" ? amazonListing : darazListing;
    const revs: MarketplaceReview[] = (listing?.reviews || []).filter(
      (r) => (r.comment || (r as any).text || "").trim().length > 0
    );

    if (revs.length === 0) {
      return {
        platform: platformName,
        status: "insufficient_data",
        status_message: `Insufficient review data: No customer reviews retrieved for ${platformName}.`,
        has_reviews: false,
        total_reviews_retrieved: listing?.reviews?.length || 0,
        total_reviews_analyzed: 0,
        counts: { positive: 0, neutral: 0, negative: 0 },
        positive_percentage: 0.0,
        neutral_percentage: 0.0,
        negative_percentage: 0.0,
        overall_sentiment: "Insufficient review data",
        positive_themes: [],
        negative_themes: [],
        analyzed_reviews: [],
        source_info: `${platformName} verified listing`,
      };
    }

    const total = revs.length;
    let pos = 0;
    let neu = 0;
    let neg = 0;
    const posThemesSet = new Set<string>();
    const negThemesSet = new Set<string>();

    revs.forEach((r) => {
      const sent = ((r as any).sentiment || (r as any).predicted_sentiment || "").toLowerCase();
      const rating = r.rating || 0;
      let finalSent = sent;
      if (!finalSent) {
        if (rating >= 4) finalSent = "positive";
        else if (rating === 3) finalSent = "neutral";
        else if (rating > 0) finalSent = "negative";
        else finalSent = "neutral";
      }

      if (finalSent === "positive") {
        pos += 1;
        posThemesSet.add("Satisfactory product quality");
        posThemesSet.add("Verified buyer feedback");
      } else if (finalSent === "negative") {
        neg += 1;
        negThemesSet.add("Customer dissatisfaction indicator");
      } else {
        neu += 1;
      }
    });

    // Exact formulas:
    // Positive percentage = (Positive reviews / Total analysed reviews) * 100
    // Neutral percentage = (Neutral reviews / Total analysed reviews) * 100
    // Negative percentage = (Negative reviews / Total analysed reviews) * 100
    const posPct = Number(((pos / total) * 100).toFixed(1));
    const neuPct = Number(((neu / total) * 100).toFixed(1));
    const negPct = Number(((neg / total) * 100).toFixed(1));

    let overall = "Neutral";
    if (pos > neg && pos >= neu) overall = "Positive";
    else if (neg > pos && neg >= neu) overall = "Negative";

    return {
      platform: platformName,
      status: "completed",
      status_message: `Analyzed ${total} customer review(s) from ${platformName}.`,
      has_reviews: true,
      total_reviews_retrieved: total,
      total_reviews_analyzed: total,
      counts: { positive: pos, neutral: neu, negative: neg },
      positive_percentage: posPct,
      neutral_percentage: neuPct,
      negative_percentage: negPct,
      overall_sentiment: overall,
      positive_themes: Array.from(posThemesSet).slice(0, 3),
      negative_themes: Array.from(negThemesSet).slice(0, 2),
      analyzed_reviews: revs,
      source_info: `${platformName} verified customer feedback`,
    };
  };

  const amazonReviewData = getPlatformReviewData("Amazon");
  const darazReviewData = getPlatformReviewData("Daraz LK");
  const temuReviewData = getPlatformReviewData("Temu");

  // Helper to render responsive marketplace card for Section C
  const renderMarketplaceCard = (
    platformName: "Amazon" | "Daraz LK" | "Temu",
    listing: MarketplaceListing | undefined,
    defaultSearchUrl: string,
    accentColor: string
  ) => {
    const rawStatus = (listing?.retrieval_status || "").trim().toLowerCase();
    const isLive = rawStatus === "live" || rawStatus === "live data";
    const isFailed = rawStatus.includes("failed") || listing?.listing_status === "SCRAPER_ERROR";
    const retrievalStatus: "Live Data" | "Data Unavailable" | "Retrieval Failed" =
      isLive ? "Live Data" : isFailed ? "Retrieval Failed" : "Data Unavailable";

    const title =
      retrievalStatus !== "Live Data"
        ? (platformName === "Amazon" ? "Live marketplace data unavailable." : `No active listing found on ${platformName}.`)
        : (listing?.product_name || `${platformName} Listing`);

    const priceInfo = formatPriceLKR(listing?.price, listing?.currency);
    const rating = listing?.rating && listing.rating > 0 ? listing.rating : null;
    const reviewCount = listing?.review_count || 0;
    const seller = listing?.seller_name || null;
    const dataSource =
      retrievalStatus === "Live Data"
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
        className="flex flex-col justify-between p-6 sm:p-7 rounded-3xl bg-[#12121C] border border-[#303047] hover:border-[#A855F7]/40 transition-all shadow-xl h-full space-y-5"
      >
        <div className="space-y-4">
          {/* Header Row: Platform Name + Status Badge */}
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <span
                className="w-3 h-3 rounded-full shrink-0 shadow-sm"
                style={{ backgroundColor: accentColor }}
              />
              <h4 className="text-base font-extrabold text-[#F8FAFC] tracking-tight">
                {platformName}
              </h4>
            </div>

            {/* Retrieval Status Badge */}
            <span
              className={`text-[11px] font-extrabold px-3 py-1 rounded-full border uppercase tracking-wider shrink-0 ${
                retrievalStatus === "Live Data"
                  ? "bg-[#22C55E]/15 text-[#22C55E] border-[#22C55E]/30"
                  : retrievalStatus === "Retrieval Failed"
                  ? "bg-[#F87171]/15 text-[#F87171] border-[#F87171]/30"
                  : "bg-[#F59E0B]/15 text-[#F59E0B] border-[#F59E0B]/30"
              }`}
            >
              {retrievalStatus}
            </span>
          </div>

          {/* Product Title: spacious, natural line wrapping, no truncation */}
          <div className="min-h-[3rem] flex items-center">
            <h5
              className={`text-sm font-bold leading-snug break-words ${
                retrievalStatus !== "Live Data" ? "text-[#A1A1B5] italic font-normal" : "text-[#F8FAFC]"
              }`}
            >
              {title}
            </h5>
          </div>

          {/* Metadata Block: Price, Rating, Seller */}
          <div className="space-y-3 text-xs text-[#A1A1B5] pt-3 border-t border-[#303047]/60">
            {/* Price */}
            <div className="flex items-start justify-between gap-2">
              <span className="font-medium text-[#A1A1B5] shrink-0 pt-0.5">Price:</span>
              <div className="text-right">
                <span
                  className={`text-base font-extrabold block ${
                    priceInfo.isAvailable ? "text-[#F8FAFC]" : "text-[#A1A1B5]/60 italic font-normal"
                  }`}
                >
                  {priceInfo.formattedLkr}
                </span>
                {priceInfo.subtext && (
                  <span className="text-[11px] text-[#A1A1B5]/80 font-normal block mt-0.5">
                    {priceInfo.subtext}
                  </span>
                )}
              </div>
            </div>

            {/* Rating & Review Count */}
            <div className="flex items-center justify-between gap-2">
              <span className="font-medium text-[#A1A1B5] shrink-0">Customer Rating:</span>
              <div className="flex items-center gap-2">
                {rating ? (
                  <div className="flex items-center gap-1.5 text-[#F59E0B] font-extrabold text-xs">
                    <Star className="w-4 h-4 fill-[#F59E0B] shrink-0" />
                    <span>{rating.toFixed(1)} / 5.0</span>
                  </div>
                ) : (
                  <span className="text-[#A1A1B5]/60 italic">Unavailable</span>
                )}
                {reviewCount > 0 ? (
                  <span className="text-[11px] text-[#A1A1B5] font-medium">({reviewCount.toLocaleString()} reviews)</span>
                ) : (
                  <span className="text-[11px] text-[#A1A1B5]/60 italic">(0 reviews)</span>
                )}
              </div>
            </div>

            {/* Seller */}
            <div className="flex items-center justify-between gap-2">
              <span className="font-medium text-[#A1A1B5] shrink-0">Seller:</span>
              <span className="text-xs font-semibold text-[#F8FAFC] text-right truncate max-w-[180px]">
                {seller || <span className="text-[#A1A1B5]/60 italic font-normal">Unavailable</span>}
              </span>
            </div>

            {/* Data Source & Timestamp */}
            <div className="pt-2 flex items-center justify-between gap-2 flex-wrap text-[11px]">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#191925] border border-[#303047] text-[#A1A1B5] font-medium">
                <Database className="w-3.5 h-3.5 text-[#A855F7] shrink-0" />
                <span>{dataSource}</span>
              </span>

              {retrievalDate && (
                <span className="text-[#A1A1B5]/70 flex items-center gap-1 text-[11px]">
                  <Calendar className="w-3.5 h-3.5 shrink-0" />
                  <span>{retrievalDate}</span>
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Action Buttons: Direct Listing View & Working Search Link */}
        <div className="space-y-2.5 pt-4 border-t border-[#303047]/60 mt-auto">
          {retrievalStatus === "Live Data" && listing?.product_url && (
            <a
              href={listing.product_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-2 w-full py-3 px-4 text-xs font-bold text-white bg-gradient-to-r from-[#EC4899] via-[#A855F7] to-[#8B5CF6] hover:opacity-95 rounded-xl transition-all shadow-md touch-manipulation min-h-[44px] cursor-pointer"
            >
              <span>View Product on {platformName}</span>
              <ExternalLink className="w-4 h-4 shrink-0" />
            </a>
          )}

          <a
            href={listing?.search_url || defaultSearchUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center justify-center gap-2 w-full py-3 px-4 text-xs font-bold text-[#F8FAFC] bg-[#191925] hover:bg-[#202033] border border-[#303047] rounded-xl transition-colors touch-manipulation min-h-[44px] cursor-pointer"
          >
            <span>Search on {platformName}</span>
            <ExternalLink className="w-4 h-4 text-[#A855F7] shrink-0" />
          </a>
        </div>
      </div>
    );
  };

  // Helper to render independent review analysis card for Section D
  const renderPlatformReviewCard = (platform: "Amazon" | "Daraz LK" | "Temu") => {
    if (platform === "Temu") {
      return (
        <div
          key="Temu-review-card"
          className="flex flex-col justify-between p-6 sm:p-7 rounded-3xl bg-[#12121C] border border-[#303047] h-full space-y-5 shadow-xl"
        >
          <div className="space-y-4">
            {/* Header: Platform + Badge */}
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2.5">
                <span className="w-3 h-3 rounded-full bg-[#fb7701] shrink-0 shadow-sm" />
                <h4 className="text-base font-extrabold text-[#F8FAFC]">
                  Temu Review Analysis
                </h4>
              </div>
              <span className="text-[11px] font-extrabold px-3 py-1 rounded-full border uppercase tracking-wider bg-[#F59E0B]/15 text-[#F59E0B] border-[#F59E0B]/30 shrink-0">
                Data Unavailable
              </span>
            </div>

            {/* Status Statement */}
            <div className="p-4 rounded-2xl bg-[#191925] border border-[#303047] space-y-2">
              <div className="flex items-center gap-2 text-sm font-bold text-[#F59E0B]">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>Temu review data is currently unavailable.</span>
              </div>
              <p className="text-xs text-[#A1A1B5] leading-relaxed">
                Temu customer reviews cannot be retrieved because product pages require client-side JavaScript rendering and session tokens that cannot be accessed through simple HTTP requests.
              </p>
            </div>

            {/* Transparency Note */}
            <div className="p-3.5 bg-[#191925]/60 rounded-xl border border-[#303047]/60 text-[11px] text-[#A1A1B5]/80 space-y-1">
              <span className="font-semibold text-[#F8FAFC] block">Platform Policy:</span>
              <p>
                In accordance with data integrity guidelines, no simulated review counts, percentages, themes, or recommendations are generated for Temu.
              </p>
            </div>
          </div>

          {/* Action button pinned to bottom */}
          <div className="pt-4 border-t border-[#303047]/60 mt-auto">
            <a
              href={temuListing?.product_url || temuListing?.search_url || temuSearchUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-2 w-full py-3 px-4 text-xs font-bold text-[#F8FAFC] bg-[#191925] hover:bg-[#202033] border border-[#303047] rounded-xl transition-colors touch-manipulation min-h-[44px] cursor-pointer"
            >
              <span>Search Temu Directly</span>
              <ExternalLink className="w-4 h-4 text-[#fb7701] shrink-0" />
            </a>
          </div>
        </div>
      );
    }

    const isAmazon = platform === "Amazon";
    const data = isAmazon ? amazonReviewData : darazReviewData;
    const accentColor = isAmazon ? "#ff9900" : "#f57224";
    const directSearchUrl = isAmazon ? amazonSearchUrl : darazSearchUrl;
    const listing = isAmazon ? amazonListing : darazListing;

    return (
      <div
        key={`${platform}-review-card`}
        className="flex flex-col justify-between p-6 sm:p-7 rounded-3xl bg-[#12121C] border border-[#303047] h-full space-y-5 shadow-xl hover:border-[#A855F7]/30 transition-all"
      >
        <div className="space-y-4">
          {/* Header */}
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <span
                className="w-3 h-3 rounded-full shrink-0 shadow-sm"
                style={{ backgroundColor: accentColor }}
              />
              <h4 className="text-base font-extrabold text-[#F8FAFC]">
                {platform} Review Analysis
              </h4>
            </div>

            <span
              className={`text-[11px] font-extrabold px-3 py-1 rounded-full border uppercase tracking-wider shrink-0 ${
                data.has_reviews
                  ? "bg-[#22C55E]/15 text-[#22C55E] border-[#22C55E]/30"
                  : "bg-[#F59E0B]/15 text-[#F59E0B] border-[#F59E0B]/30"
              }`}
            >
              {data.has_reviews ? `${data.total_reviews_retrieved} Reviews` : "Insufficient Data"}
            </span>
          </div>

          {data.has_reviews ? (
            <>
              {/* Overall Sentiment Header */}
              <div className="p-3.5 bg-[#191925] rounded-2xl border border-[#303047] flex items-center justify-between">
                <span className="text-xs text-[#A1A1B5] font-medium">Overall Sentiment:</span>
                <span
                  className={`text-xs font-black uppercase px-2.5 py-0.5 rounded-full border ${
                    data.overall_sentiment.toLowerCase() === "positive"
                      ? "bg-[#22C55E]/15 text-[#22C55E] border-[#22C55E]/30"
                      : data.overall_sentiment.toLowerCase() === "negative"
                      ? "bg-[#F87171]/15 text-[#F87171] border-[#F87171]/30"
                      : "bg-[#A1A1B5]/15 text-[#A1A1B5] border-[#A1A1B5]/30"
                  }`}
                >
                  {data.overall_sentiment}
                </span>
              </div>

              {/* Sentiment Breakdown */}
              <div className="grid grid-cols-3 gap-2">
                {/* Positive */}
                <div className="p-3 rounded-xl bg-[#191925] border border-[#303047] space-y-1">
                  <div className="flex items-center justify-between text-[#22C55E] text-[11px] font-bold">
                    <span>Pos</span>
                    <ThumbsUp className="w-3 h-3 text-[#22C55E]" />
                  </div>
                  <div className="text-lg font-black text-[#F8FAFC]">{data.counts.positive}</div>
                  <div className="w-full bg-[#202033] rounded-full h-1 overflow-hidden">
                    <div
                      className="bg-[#22C55E] h-1 rounded-full"
                      style={{ width: `${data.positive_percentage}%` }}
                    />
                  </div>
                  <div className="text-[10px] text-[#A1A1B5] font-semibold">{data.positive_percentage}%</div>
                </div>

                {/* Neutral */}
                <div className="p-3 rounded-xl bg-[#191925] border border-[#303047] space-y-1">
                  <div className="flex items-center justify-between text-[#A1A1B5] text-[11px] font-bold">
                    <span>Neu</span>
                    <MinusCircle className="w-3 h-3 text-[#A1A1B5]" />
                  </div>
                  <div className="text-lg font-black text-[#F8FAFC]">{data.counts.neutral}</div>
                  <div className="w-full bg-[#202033] rounded-full h-1 overflow-hidden">
                    <div
                      className="bg-[#A1A1B5] h-1 rounded-full"
                      style={{ width: `${data.neutral_percentage}%` }}
                    />
                  </div>
                  <div className="text-[10px] text-[#A1A1B5] font-semibold">{data.neutral_percentage}%</div>
                </div>

                {/* Negative */}
                <div className="p-3 rounded-xl bg-[#191925] border border-[#303047] space-y-1">
                  <div className="flex items-center justify-between text-[#F87171] text-[11px] font-bold">
                    <span>Neg</span>
                    <ThumbsDown className="w-3 h-3 text-[#F87171]" />
                  </div>
                  <div className="text-lg font-black text-[#F8FAFC]">{data.counts.negative}</div>
                  <div className="w-full bg-[#202033] rounded-full h-1 overflow-hidden">
                    <div
                      className="bg-[#F87171] h-1 rounded-full"
                      style={{ width: `${data.negative_percentage}%` }}
                    />
                  </div>
                  <div className="text-[10px] text-[#A1A1B5] font-semibold">{data.negative_percentage}%</div>
                </div>
              </div>

              {/* Identified Themes */}
              <div className="space-y-2 text-xs">
                {data.positive_themes.length > 0 && (
                  <div className="space-y-1">
                    <div className="flex items-center gap-1 text-[11px] font-bold text-[#22C55E]">
                      <ThumbsUp className="w-3 h-3" />
                      <span>Positive Themes</span>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {data.positive_themes.map((t, idx) => (
                        <span
                          key={idx}
                          className="text-[10px] px-2 py-0.5 rounded bg-[#22C55E]/10 text-[#22C55E] border border-[#22C55E]/20"
                        >
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {data.negative_themes.length > 0 && (
                  <div className="space-y-1">
                    <div className="flex items-center gap-1 text-[11px] font-bold text-[#F87171]">
                      <ThumbsDown className="w-3 h-3" />
                      <span>Critical Themes</span>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {data.negative_themes.map((t, idx) => (
                        <span
                          key={idx}
                          className="text-[10px] px-2 py-0.5 rounded bg-[#F87171]/10 text-[#F87171] border border-[#F87171]/20"
                        >
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="p-4 rounded-2xl bg-[#191925] border border-[#303047] space-y-2">
              <div className="flex items-center gap-2 text-sm font-bold text-[#F59E0B]">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>Insufficient review data</span>
              </div>
              <p className="text-xs text-[#A1A1B5] leading-relaxed">
                No customer written reviews retrieved from {platform} for this product.
              </p>
            </div>
          )}
        </div>

        {/* Action Button pinned to bottom */}
        <div className="pt-4 border-t border-[#303047]/60 mt-auto">
          {data.has_reviews ? (
            <button
              type="button"
              onClick={() => {
                setSelectedPlatformForModal(platform);
                setIsReviewModalOpen(true);
              }}
              className="inline-flex items-center justify-center gap-2 w-full py-3 px-4 text-xs font-bold text-white bg-gradient-to-r from-[#EC4899] via-[#A855F7] to-[#8B5CF6] hover:opacity-95 rounded-xl transition-all shadow-md touch-manipulation min-h-[44px] cursor-pointer"
            >
              <FileText className="w-4 h-4 shrink-0" />
              <span>View All {platform} Reviews ({data.total_reviews_analyzed})</span>
            </button>
          ) : (
            <a
              href={listing?.search_url || directSearchUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-2 w-full py-3 px-4 text-xs font-bold text-[#F8FAFC] bg-[#191925] hover:bg-[#202033] border border-[#303047] rounded-xl transition-colors touch-manipulation min-h-[44px] cursor-pointer"
            >
              <span>Search {platform} Directly</span>
              <ExternalLink className="w-4 h-4 text-[#A855F7] shrink-0" />
            </a>
          )}
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

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* 1. Cosmetic Classification */}
          <div className="p-4 rounded-2xl bg-[#12121C] border border-[#303047] space-y-2">
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
          <div className="p-4 rounded-2xl bg-[#12121C] border border-[#303047] space-y-2">
            <div className="text-[11px] font-extrabold uppercase tracking-wider text-[#A1A1B5]">
              Catalog Match Status
            </div>
            <div className="flex items-center gap-1.5 text-sm font-black text-[#A855F7]">
              <Sparkles className="w-4 h-4 text-[#A855F7]" />
              <span>{clipData?.match_status || "Match Evaluated"}</span>
            </div>
            <p className="text-xs text-[#A1A1B5]">
              Confidence: <strong className="text-[#F8FAFC]">{clipData?.similarity_percentage || 0}%</strong>
            </p>
          </div>

          {/* 3. Marketplace Retrieval */}
          <div className="p-4 rounded-2xl bg-[#12121C] border border-[#303047] space-y-2">
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
          <div className="p-4 rounded-2xl bg-[#12121C] border border-[#303047] space-y-2">
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

        {/* Responsive 3 Marketplace Cards Grid: 1 col on mobile, 2 cols on medium, 3 cols on desktop */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8 items-stretch">
          {renderMarketplaceCard("Amazon", amazonListing, amazonSearchUrl, "#ff9900")}
          {renderMarketplaceCard("Daraz LK", darazListing, darazSearchUrl, "#f57224")}
          {renderMarketplaceCard("Temu", temuListing, temuSearchUrl, "#fb7701")}
        </div>
      </div>

      {/* 5. Section D: Separate Customer Review Analysis for Each Marketplace */}
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
              Independent sentiment analysis, review metrics, and customer feedback themes evaluated separately for each marketplace
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs font-semibold text-[#A1A1B5]">
            <Globe className="w-4 h-4 text-[#A855F7]" />
            <span>Independent Platform Verification</span>
          </div>
        </div>

        {/* Responsive 3 Independent Review Analysis Areas */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8 items-stretch">
          {renderPlatformReviewCard("Amazon")}
          {renderPlatformReviewCard("Daraz LK")}
          {renderPlatformReviewCard("Temu")}
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
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs font-extrabold uppercase tracking-widest text-[#EC4899]">
                  Section E: Marketplace Recommendation
                </span>
                <span
                  className={`text-[10px] font-extrabold uppercase px-2.5 py-0.5 rounded-full border ${
                    recommendedPlatform
                      ? "bg-[#22C55E]/15 text-[#22C55E] border-[#22C55E]/30"
                      : "bg-[#F59E0B]/15 text-[#F59E0B] border-[#F59E0B]/30"
                  }`}
                >
                  {recommendedPlatform
                    ? "Live Data Recommendation"
                    : "Recommendation unavailable: insufficient comparable marketplace data."}
                </span>
              </div>
              <h3 className="text-xl sm:text-2xl font-black text-[#F8FAFC]">
                {recommendedPlatform ? recommendedPlatform.platform : "Marketplace Comparison"}
              </h3>
            </div>
          </div>

          {recommendedPlatform && recommendedPlatform.listing && recommendedPlatform.listing.price ? (
            (() => {
              const recPrice = formatPriceLKR(recommendedPlatform.listing.price, recommendedPlatform.listing.currency);
              return (
                <div className="sm:text-right">
                  <div className="text-xs text-[#A1A1B5]">Recommended Listing Price</div>
                  <div className="text-2xl font-black text-[#22C55E]">
                    {recPrice.formattedLkr}
                  </div>
                  {recPrice.subtext && (
                    <div className="text-xs text-[#A1A1B5]">
                      {recPrice.subtext}
                    </div>
                  )}
                </div>
              );
            })()
          ) : null}
        </div>

        {recommendedPlatform && recommendedPlatform.listing ? (
          <div className="space-y-4">
            <div className="p-4 bg-[#12121C] rounded-2xl border border-[#303047] space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="space-y-1">
                  <h4 className="font-bold text-base text-[#F8FAFC]">
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
                    <div className="flex items-center gap-1 text-[#F59E0B] text-sm font-bold bg-[#191925] px-3 py-1 rounded-xl border border-[#303047]">
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
              <div className="pt-3 border-t border-[#303047] space-y-2">
                <div className="text-xs font-bold text-[#A1A1B5] uppercase tracking-wider flex items-center justify-between">
                  <span>Recommendation Scoring Formula (Total: {recommendedPlatform.total_score}/100)</span>
                  <span className="text-[11px] text-[#A855F7] font-semibold">Configured 5-Factor Weights</span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-center text-xs">
                  <div className="p-2.5 rounded-xl bg-[#191925] border border-[#303047]">
                    <div className="text-[10px] text-[#A1A1B5]">Product Match (35%)</div>
                    <div className="text-sm font-bold text-[#F8FAFC]">
                      {recommendedPlatform.score_breakdown.match_confidence_score}%
                    </div>
                  </div>
                  <div className="p-2.5 rounded-xl bg-[#191925] border border-[#303047]">
                    <div className="text-[10px] text-[#A1A1B5]">Rating/Volume (25%)</div>
                    <div className="text-sm font-bold text-[#F8FAFC]">
                      {recommendedPlatform.score_breakdown.rating_volume_score || recommendedPlatform.score_breakdown.rating_score}%
                    </div>
                  </div>
                  <div className="p-2.5 rounded-xl bg-[#191925] border border-[#303047]">
                    <div className="text-[10px] text-[#A1A1B5]">Seller Trust (20%)</div>
                    <div className="text-sm font-bold text-[#F8FAFC]">
                      {recommendedPlatform.score_breakdown.seller_trust_score}%
                    </div>
                  </div>
                  <div className="p-2.5 rounded-xl bg-[#191925] border border-[#303047]">
                    <div className="text-[10px] text-[#A1A1B5]">Price (10%)</div>
                    <div className="text-sm font-bold text-[#F8FAFC]">
                      {recommendedPlatform.score_breakdown.price_score || 85.0}%
                    </div>
                  </div>
                  <div className="p-2.5 rounded-xl bg-[#191925] border border-[#303047]">
                    <div className="text-[10px] text-[#A1A1B5]">Sentiment (10%)</div>
                    <div className="text-sm font-bold text-[#F8FAFC]">
                      {recommendedPlatform.score_breakdown.review_sentiment_score || 50.0}%
                    </div>
                  </div>
                </div>
              </div>

              {/* Rationale */}
              <div className="pt-2 text-xs text-[#A1A1B5] flex items-start gap-2">
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

      {/* Dedicated Functional Review Analysis Modal */}
      <ReviewAnalysisModal
        isOpen={isReviewModalOpen}
        onClose={() => {
          setIsReviewModalOpen(false);
          setSelectedPlatformForModal(null);
        }}
        reviews={
          selectedPlatformForModal === "Amazon"
            ? (amazonReviewData.analyzed_reviews as ReviewItem[])
            : selectedPlatformForModal === "Daraz LK"
            ? (darazReviewData.analyzed_reviews as ReviewItem[])
            : (allCustomerReviews as ReviewItem[])
        }
        sentimentStats={
          selectedPlatformForModal === "Amazon"
            ? {
                total: amazonReviewData.total_reviews_analyzed,
                positive_count: amazonReviewData.counts.positive,
                positive_percentage: amazonReviewData.positive_percentage,
                neutral_count: amazonReviewData.counts.neutral,
                neutral_percentage: amazonReviewData.neutral_percentage,
                negative_count: amazonReviewData.counts.negative,
                negative_percentage: amazonReviewData.negative_percentage,
                summary: `Amazon Customer Reviews: ${amazonReviewData.total_reviews_analyzed} reviews analyzed (${amazonReviewData.positive_percentage}% positive).`,
              }
            : selectedPlatformForModal === "Daraz LK"
            ? {
                total: darazReviewData.total_reviews_analyzed,
                positive_count: darazReviewData.counts.positive,
                positive_percentage: darazReviewData.positive_percentage,
                neutral_count: darazReviewData.counts.neutral,
                neutral_percentage: darazReviewData.neutral_percentage,
                negative_count: darazReviewData.counts.negative,
                negative_percentage: darazReviewData.negative_percentage,
                summary: `Daraz LK Customer Reviews: ${darazReviewData.total_reviews_analyzed} reviews analyzed (${darazReviewData.positive_percentage}% positive).`,
              }
            : sentimentStats
        }
        sentimentLabel={
          selectedPlatformForModal === "Amazon"
            ? amazonReviewData.overall_sentiment
            : selectedPlatformForModal === "Daraz LK"
            ? darazReviewData.overall_sentiment
            : reviewData?.sentiment_label
        }
        isSimulated={isSimulatedReviews && !selectedPlatformForModal}
        simulationTitle={reviewData?.simulation_title}
        simulationDisclosure={reviewData?.simulation_disclosure}
        credibilityLabel={reviewData?.credibility_assessment_label}
        positiveThemes={
          selectedPlatformForModal === "Amazon"
            ? amazonReviewData.positive_themes
            : selectedPlatformForModal === "Daraz LK"
            ? darazReviewData.positive_themes
            : reviewData?.positive_themes
        }
        negativeThemes={
          selectedPlatformForModal === "Amazon"
            ? amazonReviewData.negative_themes
            : selectedPlatformForModal === "Daraz LK"
            ? darazReviewData.negative_themes
            : reviewData?.negative_themes
        }
        platformName={selectedPlatformForModal || undefined}
      />
    </div>
  );
}
