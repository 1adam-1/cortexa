import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, RefreshCcw } from "lucide-react";
import styles from "./EvaluationPage.module.css";

const clamp = (value, min, max) => Math.min(max, Math.max(min, value));

const toNumber = (value, fallback = 0) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

const formatDate = (iso) => {
  if (!iso) return "--";
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? "--" : date.toLocaleString();
};

const formatScore = (value, digits = 3) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed.toFixed(digits) : "--";
};

const formatPercent = (value, digits = 0) => {
  const pct = clamp(toNumber(value, 0) * 100, 0, 100);
  return `${pct.toFixed(digits)}%`;
};

export default function EvaluationPage() {
  const navigate = useNavigate();

  const [dashboard, setDashboard] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDashboard = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const token = localStorage.getItem("access_token");
      const response = await fetch(
        "http://localhost:5000/api/evaluations/dashboard",
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error("Failed to fetch dashboard");
      }

      const data = await response.json();
      setDashboard(data);
    } catch (err) {
      setError("Could not load the evaluation dashboard.");
      setDashboard(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  const summary = dashboard?.summary || {};
  const distribution = dashboard?.distribution || {};

  const evaluationsCount = toNumber(summary.evaluations_count, 0);
  const qaGenerations = toNumber(summary.qa_generations, 0);
  const avgFaithfulness = toNumber(summary.avg_faithfulness, 0);
  const avgRerank = toNumber(summary.avg_rerank_score, 0);
  const totalSentences = toNumber(summary.total_sentences, 0);
  const totalEntailed = toNumber(summary.total_entailed, 0);
  const totalHallucinations = toNumber(summary.total_hallucinations, 0);

  const coveragePercent = qaGenerations
    ? Math.round((evaluationsCount / qaGenerations) * 100)
    : 0;
  const entailedPercent = totalSentences
    ? Math.round((totalEntailed / totalSentences) * 100)
    : 0;

  const distLow = toNumber(distribution.low, 0);
  const distMid = toNumber(distribution.mid, 0);
  const distHigh = toNumber(distribution.high, 0);
  const distTotal = distLow + distMid + distHigh;

  const lowPct = distTotal ? (distLow / distTotal) * 100 : 0;
  const midPct = distTotal ? (distMid / distTotal) * 100 : 0;
  const highPct = distTotal ? (distHigh / distTotal) * 100 : 0;

  const heroStats = useMemo(
    () => [
      {
        label: "Sessions",
        value:
          summary.sessions_count !== undefined
            ? `${summary.sessions_count}`
            : "--",
      },
      { label: "Evaluations", value: `${evaluationsCount}` },
      {
        label: "Coverage",
        value: qaGenerations ? `${coveragePercent}%` : "--",
      },
    ],
    [summary.sessions_count, evaluationsCount, qaGenerations, coveragePercent]
  );

  const metricCards = useMemo(
    () => [
      {
        label: "Avg faithfulness",
        value: evaluationsCount ? formatPercent(avgFaithfulness, 1) : "--",
        hint: "Share of sentences supported by context.",
      },
      {
        label: "Avg rerank score",
        value: evaluationsCount ? formatScore(avgRerank, 3) : "--",
        hint: "Higher means better context alignment.",
      },
      {
        label: "Entailed rate",
        value: totalSentences ? `${entailedPercent}%` : "--",
        hint: `${totalEntailed} of ${totalSentences} sentences supported.`,
      },
      {
        label: "Evaluations",
        value: `${evaluationsCount}`,
        hint: `${qaGenerations} total Q/A generations.`,
      },
    ],
    [
      evaluationsCount,
      avgFaithfulness,
      avgRerank,
      totalSentences,
      entailedPercent,
      totalEntailed,
      qaGenerations,
    ]
  );

  const handleRefresh = async () => {
    await fetchDashboard();
  };

  const hasData = evaluationsCount > 0;

  return (
    <div className={styles.page}>
      <section className={styles.hero}>
        <div className={styles.heroTop}>
          <button
            className={styles.backButton}
            onClick={() => navigate("/Notebooks")}
          >
            <ArrowLeft size={16} />
            Back to Notebooks
          </button>
          <button
            className={styles.refreshButton}
            onClick={handleRefresh}
            disabled={isLoading}
          >
            <RefreshCcw size={16} />
            Refresh
          </button>
        </div>

        <div className={styles.heroContent}>
          <span className={styles.kicker}>Evaluation Lab</span>
          <h1 className={styles.title}>Faithfulness Dashboard</h1>
          <p className={styles.subcopy}>
            Monitor quality signals across all answers. See how well responses
            align with retrieved context at a glance.
          </p>
        </div>

        <div className={styles.heroMeta}>
          {heroStats.map((item) => (
            <div key={item.label} className={styles.metaItem}>
              <span className={styles.metaLabel}>{item.label}</span>
              <span className={styles.metaValue}>{item.value}</span>
            </div>
          ))}
        </div>
      </section>

      <section className={styles.content}>
        {isLoading ? (
          <div className={styles.loadingBox}>Loading dashboard...</div>
        ) : error ? (
          <div className={styles.emptyState}>{error}</div>
        ) : !hasData ? (
          <div className={styles.emptyState}>
            No evaluations yet. Generate Q/A answers to populate the dashboard.
          </div>
        ) : (
          <>
            <div className={styles.metricsGrid}>
              {metricCards.map((metric) => (
                <div key={metric.label} className={styles.metricCard}>
                  <span className={styles.metricLabel}>{metric.label}</span>
                  <span className={styles.metricValue}>{metric.value}</span>
                  <span className={styles.metricHint}>{metric.hint}</span>
                </div>
              ))}
            </div>

            <div className={styles.panelGrid}>
              <div className={styles.panel}>
                <div className={styles.panelHeader}>
                  <h3>Faithfulness distribution</h3>
                  <span className={styles.panelTag}>Low / Mid / High</span>
                </div>
                <div className={styles.distributionBar}>
                  <span
                    className={`${styles.distSegment} ${styles.distLow}`}
                    style={{ width: `${lowPct}%` }}
                  />
                  <span
                    className={`${styles.distSegment} ${styles.distMid}`}
                    style={{ width: `${midPct}%` }}
                  />
                  <span
                    className={`${styles.distSegment} ${styles.distHigh}`}
                    style={{ width: `${highPct}%` }}
                  />
                </div>
                <div className={styles.legend}>
                  <div className={styles.legendItem}>
                    <span className={`${styles.legendDot} ${styles.distLow}`} />
                    <span>Low &lt; 50%</span>
                    <span className={styles.legendValue}>{distLow}</span>
                  </div>
                  <div className={styles.legendItem}>
                    <span className={`${styles.legendDot} ${styles.distMid}`} />
                    <span>Mid 50-80%</span>
                    <span className={styles.legendValue}>{distMid}</span>
                  </div>
                  <div className={styles.legendItem}>
                    <span className={`${styles.legendDot} ${styles.distHigh}`} />
                    <span>High 80%+</span>
                    <span className={styles.legendValue}>{distHigh}</span>
                  </div>
                </div>
              </div>

              <div className={styles.panel}>
                <div className={styles.panelHeader}>
                  <h3>Sentence accounting</h3>
                  <span className={styles.panelTag}>Entailed rate</span>
                </div>
                <div className={styles.progressWrap}>
                  <div className={styles.progressBar}>
                    <span
                      className={styles.progressFill}
                      style={{ width: `${entailedPercent}%` }}
                    />
                  </div>
                  <div className={styles.progressMeta}>
                    <span className={styles.progressValue}>
                      {entailedPercent}% entailed
                    </span>
                    <span className={styles.progressHint}>
                      {totalEntailed} of {totalSentences} sentences supported.
                    </span>
                  </div>
                </div>
                <div className={styles.accountGrid}>
                  <div className={styles.accountItem}>
                    <span>Entailed</span>
                    <strong>{totalEntailed}</strong>
                  </div>
                  <div className={styles.accountItem}>
                    <span>Hallucinations</span>
                    <strong>{totalHallucinations}</strong>
                  </div>
                </div>
              </div>

              <div className={styles.panel}>
                <div className={styles.panelHeader}>
                  <h3>Totals</h3>
                  <span className={styles.panelTag}>Session summary</span>
                </div>
                <div className={styles.totalList}>
                  <div className={styles.totalItem}>
                    <span>Total evaluations</span>
                    <strong>{evaluationsCount}</strong>
                  </div>
                  <div className={styles.totalItem}>
                    <span>Total sentences</span>
                    <strong>{totalSentences}</strong>
                  </div>
                  <div className={styles.totalItem}>
                    <span>Coverage</span>
                    <strong>{qaGenerations ? `${coveragePercent}%` : "--"}</strong>
                  </div>
                  <div className={styles.totalItem}>
                    <span>Last update</span>
                    <strong>{formatDate(summary.last_updated)}</strong>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </section>
    </div>
  );
}
