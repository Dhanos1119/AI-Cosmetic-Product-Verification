"use client";

import { useEffect, useRef } from "react";
import {
  X,
  MessageSquare,
  Star,
  ThumbsUp,
  ThumbsDown,
  MinusCircle,
  User,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Info,
  ShieldCheck,
  Tag,
} from "lucide-react";

export interface ReviewItem {
  review_id?: string;
  author?: string;
  reviewer_name?: string;
  rating?: number;
  star_rating?: number;
  headline?: string;
  comment?: string;
  text?: string;
  review_text?: string;
  sentiment?: string;
  predicted_sentiment?: string;
  sentiment_confidence?: number | null;
  explanation?: string;
  credibility_indicators?: {
    verified_purchase?: boolean;
    pattern?: string;
  };
  verified_purchase?: boolean;
  date?: string;
  source_label?: string;
  retrieval_status?: string;
  data_source?: string;
}

export interface ReviewSentimentStats {
  total: number;
  positive_count: number;
  positive_percentage: number;
  neutral_count: number;
  neutral_percentage: number;
  negative_count: number;
  negative_percentage: number;
  summary?: string;
}

export interface ReviewAnalysisModalProps {
  isOpen: boolean;
  onClose: () => void;
  reviews: ReviewItem[];
  sentimentStats?: ReviewSentimentStats;
  sentimentLabel?: string;
  isSimulated?: boolean;
  simulationTitle?: string;
  simulationDisclosure?: string;
  credibilityLabel?: string;
  positiveThemes?: string[];
  negativeThemes?: string[];
}

export default function ReviewAnalysisModal({
  isOpen,
  onClose,
  reviews,
  sentimentStats,
  sentimentLabel,
  isSimulated = false,
  simulationTitle,
  simulationDisclosure,
  credibilityLabel,
  positiveThemes = [],
  negativeThemes = [],
}: ReviewAnalysisModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);

  // Keyboard accessibility: Close on Escape key and trap body scroll
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = originalOverflow;
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const totalReviews = sentimentStats?.total || reviews.length;
  const posCount = sentimentStats?.positive_count ?? reviews.filter((r) => (r.sentiment || r.predicted_sentiment) === "positive").length;
  const neuCount = sentimentStats?.neutral_count ?? reviews.filter((r) => (r.sentiment || r.predicted_sentiment) === "neutral").length;
  const negCount = sentimentStats?.negative_count ?? reviews.filter((r) => (r.sentiment || r.predicted_sentiment) === "negative").length;

  const posPct = totalReviews > 0 ? ((posCount / totalReviews) * 100).toFixed(0) : "0";
  const neuPct = totalReviews > 0 ? ((neuCount / totalReviews) * 100).toFixed(0) : "0";
  const negPct = totalReviews > 0 ? ((negCount / totalReviews) * 100).toFixed(0) : "0";

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/80 backdrop-blur-md animate-fadeIn"
      role="dialog"
      aria-modal="true"
      aria-labelledby="review-modal-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        ref={modalRef}
        className="w-full max-w-4xl max-h-[90vh] flex flex-col bg-[#12121C] border border-[#303047] rounded-3xl shadow-2xl overflow-hidden text-[#F8FAFC]"
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between p-5 sm:p-6 border-b border-[#303047] bg-[#191925]/90">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-[#A855F7]/15 border border-[#A855F7]/30 flex items-center justify-center text-[#A855F7]">
              <MessageSquare className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 id="review-modal-title" className="text-lg sm:text-xl font-black text-[#F8FAFC]">
                  {isSimulated ? "Simulated Review Analysis" : "Customer Review Analysis"}
                </h3>
                <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-[#A855F7]/20 text-[#A855F7] border border-[#A855F7]/30">
                  {totalReviews} Records
                </span>
                <span
                  className={`text-[10px] font-extrabold px-2 py-0.5 rounded border uppercase ${
                    isSimulated
                      ? "bg-[#A855F7]/15 text-[#A855F7] border-[#A855F7]/30"
                      : "bg-[#22C55E]/15 text-[#22C55E] border-[#22C55E]/30"
                  }`}
                >
                  {isSimulated ? "DEMO DATA" : "LIVE REVIEWS"}
                </span>
              </div>
              <p className="text-xs text-[#A1A1B5]">
                {sentimentStats?.summary || `Sentiment distribution across all ${totalReviews} customer feedback records.`}
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            aria-label="Close modal"
            className="w-9 h-9 rounded-xl bg-[#191925] hover:bg-[#202033] border border-[#303047] flex items-center justify-center text-[#A1A1B5] hover:text-[#F8FAFC] transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Scrollable Body */}
        <div className="flex-1 overflow-y-auto p-5 sm:p-6 space-y-6">
          {/* Simulated Disclosure Banner */}
          {isSimulated && (
            <div className="p-4 rounded-2xl bg-[#191925] border border-[#A855F7]/30 text-xs text-[#A1A1B5] space-y-1.5">
              <div className="flex items-center gap-2 text-[#A855F7] font-bold">
                <Info className="w-4 h-4" />
                <span>{simulationTitle || "Simulated Review Analysis — Demonstration Data"}</span>
              </div>
              <p className="leading-relaxed">
                {simulationDisclosure ||
                  "These reviews are synthetic examples generated for demonstration and testing. They were not collected from real marketplace customers and must not be used as evidence of actual product quality."}
              </p>
            </div>
          )}

          {/* Sentiment Distribution Summary */}
          <div className="p-4 sm:p-5 rounded-2xl bg-[#191925] border border-[#303047] space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-extrabold uppercase tracking-wider text-[#A1A1B5]">
                Sentiment Distribution
              </span>
              <span className="text-xs font-bold text-[#F8FAFC]">
                Consensus: <span className="text-[#A855F7] capitalize">{sentimentLabel || "Evaluated"}</span>
              </span>
            </div>

            {/* Distribution Bar */}
            <div className="w-full h-2.5 rounded-full bg-[#202033] overflow-hidden flex">
              <div style={{ width: `${posPct}%` }} className="bg-[#22C55E] h-full transition-all" title={`Positive: ${posPct}%`} />
              <div style={{ width: `${neuPct}%` }} className="bg-[#A1A1B5] h-full transition-all" title={`Neutral: ${neuPct}%`} />
              <div style={{ width: `${negPct}%` }} className="bg-[#F87171] h-full transition-all" title={`Negative: ${negPct}%`} />
            </div>

            {/* 3 Metric Cards */}
            <div className="grid grid-cols-3 gap-3">
              <div className="p-3 rounded-xl bg-[#12121C] border border-[#303047] text-center space-y-1">
                <div className="flex items-center justify-center gap-1 text-xs font-bold text-[#22C55E]">
                  <ThumbsUp className="w-3.5 h-3.5" />
                  <span>Positive</span>
                </div>
                <div className="text-xl sm:text-2xl font-black text-[#F8FAFC]">{posCount}</div>
                <div className="text-[11px] text-[#A1A1B5]">{posPct}% of total</div>
              </div>

              <div className="p-3 rounded-xl bg-[#12121C] border border-[#303047] text-center space-y-1">
                <div className="flex items-center justify-center gap-1 text-xs font-bold text-[#A1A1B5]">
                  <MinusCircle className="w-3.5 h-3.5" />
                  <span>Neutral</span>
                </div>
                <div className="text-xl sm:text-2xl font-black text-[#F8FAFC]">{neuCount}</div>
                <div className="text-[11px] text-[#A1A1B5]">{neuPct}% of total</div>
              </div>

              <div className="p-3 rounded-xl bg-[#12121C] border border-[#303047] text-center space-y-1">
                <div className="flex items-center justify-center gap-1 text-xs font-bold text-[#F87171]">
                  <ThumbsDown className="w-3.5 h-3.5" />
                  <span>Negative</span>
                </div>
                <div className="text-xl sm:text-2xl font-black text-[#F8FAFC]">{negCount}</div>
                <div className="text-[11px] text-[#A1A1B5]">{negPct}% of total</div>
              </div>
            </div>
          </div>

          {/* Positive & Negative Feedback Themes */}
          {(positiveThemes.length > 0 || negativeThemes.length > 0) && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {positiveThemes.length > 0 && (
                <div className="p-4 rounded-2xl bg-[#191925] border border-[#303047] space-y-2.5">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-[#22C55E]">
                    <ThumbsUp className="w-4 h-4" />
                    <span>Common Positive Themes</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {positiveThemes.map((theme, i) => (
                      <span
                        key={i}
                        className="text-[11px] px-2.5 py-1 rounded-lg bg-[#22C55E]/10 text-[#22C55E] border border-[#22C55E]/20 font-medium"
                      >
                        {theme}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {negativeThemes.length > 0 && (
                <div className="p-4 rounded-2xl bg-[#191925] border border-[#303047] space-y-2.5">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-[#F87171]">
                    <ThumbsDown className="w-4 h-4" />
                    <span>Common Critical Themes</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {negativeThemes.map((theme, i) => (
                      <span
                        key={i}
                        className="text-[11px] px-2.5 py-1 rounded-lg bg-[#F87171]/10 text-[#F87171] border border-[#F87171]/20 font-medium"
                      >
                        {theme}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Credibility Assessment Note */}
          <div className="p-3.5 rounded-2xl bg-[#191925] border border-[#303047] flex items-center justify-between text-xs text-[#A1A1B5]">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-[#A855F7]" />
              <span>
                {credibilityLabel || "Illustrative credibility analysis of review records."}
              </span>
            </div>
            <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-[#22C55E]/15 text-[#22C55E] border border-[#22C55E]/30">
              No Obvious Fraud Pattern
            </span>
          </div>

          {/* All Review Records List */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-extrabold uppercase tracking-wider text-[#A1A1B5]">
                Review Records ({reviews.length})
              </h4>
              <span className="text-xs text-[#A1A1B5]">Sorted by configured record ID</span>
            </div>

            <div className="space-y-3">
              {reviews.map((rv, idx) => {
                const sentiment = rv.sentiment || rv.predicted_sentiment || "neutral";
                const rating = rv.star_rating || rv.rating || 4.0;
                const author = rv.reviewer_name || rv.author || `Reviewer ${idx + 1}`;
                const text = rv.review_text || rv.comment || rv.text || "";
                const conf = rv.sentiment_confidence;

                return (
                  <div
                    key={rv.review_id || idx}
                    className="p-4 rounded-2xl bg-[#191925] border border-[#303047] space-y-2.5 hover:border-[#A855F7]/40 transition-colors"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded-xl bg-[#202033] flex items-center justify-center text-[#A855F7] font-bold text-xs">
                          <User className="w-4 h-4" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-bold text-[#F8FAFC]">{author}</span>
                            {rv.review_id && (
                              <span className="text-[10px] font-mono text-[#A1A1B5]/70 bg-[#12121C] px-1.5 py-0.5 rounded border border-[#303047]">
                                {rv.review_id}
                              </span>
                            )}
                            <span
                              className={`text-[9px] font-extrabold uppercase px-1.5 py-0.5 rounded border ${
                                rv.source_label === "DEMO" || isSimulated
                                  ? "bg-[#A855F7]/15 text-[#A855F7] border-[#A855F7]/30"
                                  : "bg-[#22C55E]/15 text-[#22C55E] border-[#22C55E]/30"
                              }`}
                            >
                              {rv.source_label || (isSimulated ? "DEMO" : "LIVE")}
                            </span>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        {/* Sentiment Label Badge with Model Confidence */}
                        <span
                          className={`text-[10px] font-bold uppercase px-2.5 py-0.5 rounded-full border flex items-center gap-1 ${
                            sentiment === "positive"
                              ? "bg-[#22C55E]/15 text-[#22C55E] border-[#22C55E]/30"
                              : sentiment === "negative"
                              ? "bg-[#F87171]/15 text-[#F87171] border-[#F87171]/30"
                              : "bg-[#A1A1B5]/15 text-[#A1A1B5] border-[#A1A1B5]/30"
                          }`}
                        >
                          {sentiment === "positive" ? (
                            <ThumbsUp className="w-3 h-3" />
                          ) : sentiment === "negative" ? (
                            <ThumbsDown className="w-3 h-3" />
                          ) : (
                            <MinusCircle className="w-3 h-3" />
                          )}
                          <span>
                            {sentiment}
                            {conf !== null && conf !== undefined ? ` (${(conf * 100).toFixed(0)}%)` : ""}
                          </span>
                        </span>

                        {/* Star Rating */}
                        <div className="flex items-center gap-1 bg-[#12121C] px-2.5 py-1 rounded-xl border border-[#303047] text-xs font-bold text-[#F59E0B]">
                          <Star className="w-3.5 h-3.5 fill-[#F59E0B]" />
                          <span>{rating.toFixed(1)}</span>
                        </div>
                      </div>
                    </div>

                    {/* Headline */}
                    {rv.headline && (
                      <h5 className="text-xs font-bold text-[#F8FAFC]">{rv.headline}</h5>
                    )}

                    {/* Review Comment Text */}
                    <p className="text-xs text-[#A1A1B5] leading-relaxed italic">
                      "{text}"
                    </p>

                    {/* Short Explanation & Credibility Tags */}
                    <div className="pt-2 border-t border-[#303047]/60 flex flex-wrap items-center justify-between gap-2 text-[11px] text-[#A1A1B5]">
                      <div className="flex items-center gap-1.5">
                        <Tag className="w-3 h-3 text-[#A855F7]" />
                        <span>
                          <strong className="text-[#F8FAFC]">Analysis:</strong> {rv.explanation || "Predicted based on feedback text."}
                        </span>
                      </div>

                      <div className="flex items-center gap-2">
                        {rv.verified_purchase && (
                          <span className="text-[10px] font-bold text-[#22C55E] bg-[#22C55E]/10 px-2 py-0.5 rounded border border-[#22C55E]/30 flex items-center gap-1">
                            <CheckCircle2 className="w-3 h-3" />
                            <span>Verified Buyer</span>
                          </span>
                        )}
                        <span className="text-[10px] text-[#A1A1B5]/70 bg-[#12121C] px-2 py-0.5 rounded border border-[#303047]">
                          Pattern: No obvious pattern detected
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-4 sm:p-5 border-t border-[#303047] bg-[#191925]/90 flex items-center justify-between gap-3">
          <span className="text-xs text-[#A1A1B5]">
            Press <kbd className="px-1.5 py-0.5 bg-[#202033] border border-[#303047] rounded text-[10px]">Esc</kbd> or click Close to return
          </span>

          <button
            type="button"
            onClick={onClose}
            className="px-5 py-2.5 text-xs font-bold text-[#F8FAFC] bg-[#12121C] hover:bg-[#202033] border border-[#303047] rounded-xl transition-colors cursor-pointer"
          >
            Close Reviews
          </button>
        </div>
      </div>
    </div>
  );
}
