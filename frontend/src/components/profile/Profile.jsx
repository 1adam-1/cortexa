import { useState, useEffect } from "react";
import styles from "./profile.module.css";

const API_BASE = "http://localhost:5000";

async function apiFetch(path, options = {}) {
  const token = localStorage.getItem("access_token");
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(options.headers || {}),
    },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.message || "Request failed");
  return data;
}

export default function Profile() {
  const [user, setUser] = useState(null);
  const [form, setForm] = useState({ nom: "", prenom: "", email: "" });
  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(false);

  useEffect(() => {
    fetchProfile();
  }, []);

  useEffect(() => {
    if (success) {
      const t = setTimeout(() => setSuccess(null), 3000);
      return () => clearTimeout(t);
    }
  }, [success]);

  async function fetchProfile() {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch("/profile");
      setUser(data);
      setForm({ nom: data.nom, prenom: data.prenom, email: data.email });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      const data = await apiFetch("/update", {
        method: "PUT",
        body: JSON.stringify(form),
      });
      setUser(data.user);
      setForm({ nom: data.user.nom, prenom: data.user.prenom, email: data.user.email });
      setEditing(false);
      setSuccess("Profile updated successfully.");
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    try {
      await apiFetch("/delete", { method: "DELETE" });
      localStorage.removeItem("access_token");
      window.location.href = "/login";
    } catch (err) {
      setError(err.message);
      setConfirmDelete(false);
    }
  }

  function handleCancel() {
    setForm({ nom: user.nom, prenom: user.prenom, email: user.email });
    setEditing(false);
    setError(null);
  }

  const initials = user
    ? `${user.prenom?.[0] ?? ""}${user.nom?.[0] ?? ""}`.toUpperCase()
    : "??";

  if (loading) {
    return (
      <div className={styles.shell}>
        <div className={styles.loadingState}>
          <div className={styles.spinner} />
          <span>Loading profile…</span>
        </div>
      </div>
    );
  }

  if (error && !user) {
    return (
      <div className={styles.shell}>
        <div className={styles.errorState}>
          <span className={styles.errorIcon}>⚠</span>
          <p>{error}</p>
          <button className={styles.btnPrimary} onClick={fetchProfile}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.shell}>
      <div className={styles.card}>

        {/* ── Left panel ── */}
        <aside className={styles.sidebar}>
          <div className={styles.avatarRing}>
            <div className={styles.avatar}>{initials}</div>
          </div>
          <p className={styles.fullName}>
            {user.prenom} {user.nom}
          </p>
          <p className={styles.userId}>ID #{user.id}</p>

          <div className={styles.metaBlock}>
            <span className={styles.metaLabel}>Email</span>
            <span className={styles.metaValue}>{user.email}</span>
          </div>

          {!editing && (
            <button
              className={styles.btnPrimary}
              onClick={() => { setEditing(true); setError(null); }}
            >
              Edit Profile
            </button>
          )}
        </aside>

        {/* ── Right panel ── */}
        <main className={styles.content}>

          {/* Toast */}
          {success && <div className={styles.toast}>{success}</div>}
          {error && user && <div className={styles.toastError}>{error}</div>}

          <div className={styles.sectionHeader}>
            <h2 className={styles.sectionTitle}>
              {editing ? "Edit Profile" : "Account Details"}
            </h2>
            {editing && (
              <span className={styles.editingBadge}>Editing</span>
            )}
          </div>

          <div className={styles.fields}>
            <Field
              label="First Name"
              value={form.prenom}
              editing={editing}
              onChange={(v) => setForm((f) => ({ ...f, prenom: v }))}
              placeholder="Prénom"
            />
            <Field
              label="Last Name"
              value={form.nom}
              editing={editing}
              onChange={(v) => setForm((f) => ({ ...f, nom: v }))}
              placeholder="Nom"
            />
            <Field
              label="Email Address"
              value={form.email}
              editing={editing}
              onChange={(v) => setForm((f) => ({ ...f, email: v }))}
              placeholder="email@example.com"
              type="email"
              fullWidth
            />
          </div>

          {editing && (
            <div className={styles.actions}>
              <button
                className={styles.btnPrimary}
                onClick={handleSave}
                disabled={saving}
              >
                {saving ? "Saving…" : "Save Changes"}
              </button>
              <button className={styles.btnGhost} onClick={handleCancel}>
                Cancel
              </button>
            </div>
          )}

          {/* ── Danger zone ── */}
          {!editing && (
            <div className={styles.dangerZone}>
              <div className={styles.dangerHeader}>
                <span className={styles.dangerLabel}>Danger Zone</span>
                <div className={styles.dangerRule} />
              </div>
              <div className={styles.dangerBody}>
                <div>
                  <p className={styles.dangerTitle}>Delete Account</p>
                  <p className={styles.dangerDesc}>
                    This action is permanent and cannot be undone. All your data will be erased.
                  </p>
                </div>
                {!confirmDelete ? (
                  <button
                    className={styles.btnDanger}
                    onClick={() => setConfirmDelete(true)}
                  >
                    Delete Account
                  </button>
                ) : (
                  <div className={styles.confirmRow}>
                    <span className={styles.confirmText}>Are you sure?</span>
                    <button className={styles.btnDangerConfirm} onClick={handleDelete}>
                      Yes, delete
                    </button>
                    <button className={styles.btnGhost} onClick={() => setConfirmDelete(false)}>
                      Cancel
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

function Field({ label, value, editing, onChange, placeholder, type = "text", fullWidth }) {
  return (
    <div className={`${styles.fieldGroup} ${fullWidth ? styles.fullWidth : ""}`}>
      <label className={styles.fieldLabel}>{label}</label>
      {editing ? (
        <input
          className={styles.fieldInput}
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
        />
      ) : (
        <p className={styles.fieldValue}>{value || <span className={styles.empty}>—</span>}</p>
      )}
    </div>
  );
}