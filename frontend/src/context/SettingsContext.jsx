import { createContext, useContext, useEffect, useState, useCallback } from "react";

const API_BASE = "http://localhost:5000";
const STORAGE_KEY = "app_settings";

const DEFAULTS = {
    theme: "light",
    font_size: "medium",
    response_length: "balanced",
};

const FONT_SIZES = {
    small: "15px",
    medium: "17px",
    large: "19px",
};

const SettingsContext = createContext({
    settings: DEFAULTS,
    updateSettings: () => {},
    loading: false,
});

function loadLocal() {
    try {
        const raw = localStorage.getItem(STORAGE_KEY);
        return raw ? { ...DEFAULTS, ...JSON.parse(raw) } : DEFAULTS;
    } catch {
        return DEFAULTS;
    }
}

function applyToDocument(settings) {
    document.documentElement.classList.toggle("dark", settings.theme === "dark");
    document.documentElement.style.fontSize = FONT_SIZES[settings.font_size] || FONT_SIZES.medium;
}

export function SettingsProvider({ children }) {
    const [settings, setSettings] = useState(loadLocal);
    const [loading, setLoading] = useState(false);

    // Apply theme + font size whenever settings change
    useEffect(() => {
        applyToDocument(settings);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    }, [settings]);

    // Sync from backend once when logged in
    useEffect(() => {
        const token = localStorage.getItem("access_token");
        if (!token) return;

        setLoading(true);
        fetch(`${API_BASE}/settings`, {
            headers: { Authorization: `Bearer ${token}` },
        })
            .then((res) => (res.ok ? res.json() : null))
            .then((data) => {
                if (data) setSettings((s) => ({ ...s, ...data }));
            })
            .catch(() => {})
            .finally(() => setLoading(false));
    }, []);

    const updateSettings = useCallback(async (partial) => {
        // Optimistic update — theme/font apply instantly
        setSettings((s) => ({ ...s, ...partial }));

        const token = localStorage.getItem("access_token");
        if (!token) return;

        const res = await fetch(`${API_BASE}/settings`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify(partial),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.message || "Failed to save settings");
        setSettings((s) => ({ ...s, ...data.settings }));
    }, []);

    return (
        <SettingsContext.Provider value={{ settings, updateSettings, loading }}>
            {children}
        </SettingsContext.Provider>
    );
}

export function useSettings() {
    return useContext(SettingsContext);
}
