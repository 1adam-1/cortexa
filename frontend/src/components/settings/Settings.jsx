import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Sun, Moon, Type, MessageSquareText, Trash2, UserRound } from "lucide-react";
import { useSettings } from "../../context/SettingsContext.jsx";
import styles from "./settings.module.css";

const API_BASE = "http://localhost:5000";

const FONT_OPTIONS = [
    { value: "small", label: "Small" },
    { value: "medium", label: "Medium" },
    { value: "large", label: "Large" },
];

const LENGTH_OPTIONS = [
    { value: "concise", label: "Concise", desc: "Short answers, essentials only" },
    { value: "balanced", label: "Balanced", desc: "Default answer length" },
    { value: "detailed", label: "Detailed", desc: "Thorough, structured answers" },
];

export default function Settings() {
    const { settings, updateSettings } = useSettings();
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    const [confirmClear, setConfirmClear] = useState(false);
    const [clearing, setClearing] = useState(false);

    useEffect(() => {
        if (success) {
            const t = setTimeout(() => setSuccess(null), 3000);
            return () => clearTimeout(t);
        }
    }, [success]);

    async function handleChange(partial) {
        setError(null);
        try {
            await updateSettings(partial);
            setSuccess("Settings saved.");
        } catch (err) {
            setError(err.message);
        }
    }

    async function handleClearHistory() {
        setClearing(true);
        setError(null);
        try {
            const token = localStorage.getItem("access_token");
            const res = await fetch(`${API_BASE}/settings/chat-history`, {
                method: "DELETE",
                headers: { Authorization: `Bearer ${token}` },
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.message || "Failed to clear history");
            setSuccess(`Chat history cleared (${data.deleted_messages} messages deleted).`);
        } catch (err) {
            setError(err.message);
        } finally {
            setClearing(false);
            setConfirmClear(false);
        }
    }

    return (
        <div className={styles.shell}>
            <div className={styles.page}>
                <h1 className={styles.title}>Settings</h1>

                {success && <div className={styles.toast}>{success}</div>}
                {error && <div className={styles.toastError}>{error}</div>}

                {/* ── Appearance ── */}
                <section className={styles.section}>
                    <h2 className={styles.sectionTitle}>Appearance</h2>

                    <div className={styles.row}>
                        <div className={styles.rowInfo}>
                            <span className={styles.rowLabel}>Theme</span>
                            <span className={styles.rowDesc}>Switch between light and dark mode</span>
                        </div>
                        <div className={styles.segmented}>
                            <button
                                className={`${styles.segment} ${settings.theme === "light" ? styles.segmentActive : ""}`}
                                onClick={() => handleChange({ theme: "light" })}
                            >
                                <Sun size={15} /> Light
                            </button>
                            <button
                                className={`${styles.segment} ${settings.theme === "dark" ? styles.segmentActive : ""}`}
                                onClick={() => handleChange({ theme: "dark" })}
                            >
                                <Moon size={15} /> Dark
                            </button>
                        </div>
                    </div>

                    <div className={styles.row}>
                        <div className={styles.rowInfo}>
                            <span className={styles.rowLabel}><Type size={14} /> Font size</span>
                            <span className={styles.rowDesc}>Adjust text size across the app</span>
                        </div>
                        <div className={styles.segmented}>
                            {FONT_OPTIONS.map((opt) => (
                                <button
                                    key={opt.value}
                                    className={`${styles.segment} ${settings.font_size === opt.value ? styles.segmentActive : ""}`}
                                    onClick={() => handleChange({ font_size: opt.value })}
                                >
                                    {opt.label}
                                </button>
                            ))}
                        </div>
                    </div>
                </section>

                {/* ── AI Responses ── */}
                <section className={styles.section}>
                    <h2 className={styles.sectionTitle}>AI Responses</h2>

                    <div className={styles.row}>
                        <div className={styles.rowInfo}>
                            <span className={styles.rowLabel}><MessageSquareText size={14} /> Answer length</span>
                            <span className={styles.rowDesc}>How detailed chat answers should be</span>
                        </div>
                    </div>
                    <div className={styles.cards}>
                        {LENGTH_OPTIONS.map((opt) => (
                            <button
                                key={opt.value}
                                className={`${styles.optionCard} ${settings.response_length === opt.value ? styles.optionCardActive : ""}`}
                                onClick={() => handleChange({ response_length: opt.value })}
                            >
                                <span className={styles.optionLabel}>{opt.label}</span>
                                <span className={styles.optionDesc}>{opt.desc}</span>
                            </button>
                        ))}
                    </div>
                </section>

                {/* ── Data ── */}
                <section className={styles.section}>
                    <h2 className={styles.sectionTitle}>Data</h2>

                    <div className={styles.row}>
                        <div className={styles.rowInfo}>
                            <span className={styles.rowLabel}><Trash2 size={14} /> Clear chat history</span>
                            <span className={styles.rowDesc}>
                                Deletes all chat messages in every notebook. Documents and summaries are kept.
                            </span>
                        </div>
                        {!confirmClear ? (
                            <button className={styles.btnDanger} onClick={() => setConfirmClear(true)}>
                                Clear history
                            </button>
                        ) : (
                            <div className={styles.confirmRow}>
                                <span className={styles.confirmText}>Are you sure?</span>
                                <button
                                    className={styles.btnDangerConfirm}
                                    onClick={handleClearHistory}
                                    disabled={clearing}
                                >
                                    {clearing ? "Clearing…" : "Yes, clear"}
                                </button>
                                <button className={styles.btnGhost} onClick={() => setConfirmClear(false)}>
                                    Cancel
                                </button>
                            </div>
                        )}
                    </div>
                </section>

                {/* ── Account ── */}
                <section className={styles.section}>
                    <h2 className={styles.sectionTitle}>Account</h2>
                    <div className={styles.row}>
                        <div className={styles.rowInfo}>
                            <span className={styles.rowLabel}><UserRound size={14} /> Profile & account</span>
                            <span className={styles.rowDesc}>
                                Edit your name and email, or delete your account
                            </span>
                        </div>
                        <Link to="/profile" className={styles.btnGhost}>
                            Go to Profile
                        </Link>
                    </div>
                </section>
            </div>
        </div>
    );
}
