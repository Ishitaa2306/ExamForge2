"""
ExamForge Editorial Styling for Streamlit.
Provides custom CSS injection matching the academic editorial design system:
Ivory, Charcoal, Terracotta, Sage, Sand, Warm Gray.
Ensures high contrast, legible typography, and responsive interactive states.
"""

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --color-ivory: #F6F2EB;
    --color-charcoal: #262422;
    --color-text-dark: #1E1C1A;
    --color-terracotta: #B8755D;
    --color-terracotta-dark: #9A5B45;
    --color-sage: #788875;
    --color-sand: #E9DFD1;
    --color-warmgray: #5A554E;
    --color-olive: #A4A17C;
    --color-lavender: #A99AAF;
}

/* Overall page background & base typography */
.stApp {
    background-color: var(--color-ivory) !important;
    color: var(--color-charcoal) !important;
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* Headings */
h1, h2, h3, h4 {
    font-family: 'Cinzel', serif !important;
    color: var(--color-text-dark) !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
}

/* Paragraphs & generic text */
p, span, div, label {
    color: var(--color-charcoal);
}

/* ─── SIDEBAR — MODERN PROFESSIONAL LAYOUT ─────────────────────────────────── */
section[data-testid="stSidebar"] {
    background-color: #EDE7DC !important;
    border-right: 1px solid #D8CFC2 !important;
}

section[data-testid="stSidebar"] h1, 
section[data-testid="stSidebar"] h2, 
section[data-testid="stSidebar"] h3 {
    color: var(--color-text-dark) !important;
}

/* ── Sidebar Brand ────────────────────────────────────────────────────── */
.sidebar-brand {
    padding: 16px 0 20px 0;
    border-bottom: 1px solid #D8CFC2;
}
.sidebar-brand-name {
    font-size: 26px;
    font-weight: 700;
    font-family: 'Cinzel', serif;
    color: var(--color-charcoal);
    letter-spacing: -0.02em;
    line-height: 1.2;
}
.sidebar-brand-tagline {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--color-terracotta);
    font-weight: 600;
    margin-top: 4px;
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* ── Sidebar User Card ────────────────────────────────────────────────── */
.sidebar-user-card {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px;
    background: #FFFFFF;
    border: 1px solid #D8CFC2;
    border-radius: 10px;
    margin: 18px 0 10px 0;
    box-shadow: 0 2px 8px rgba(48, 46, 43, 0.05);
}
.sidebar-user-avatar {
    width: 38px;
    height: 38px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--color-terracotta), var(--color-terracotta-dark));
    color: #FFFFFF;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    font-weight: 700;
    font-family: 'Cinzel', serif;
    flex-shrink: 0;
}
.sidebar-user-info {
    overflow: hidden;
}
.sidebar-user-name {
    font-weight: 700;
    font-size: 14px;
    color: var(--color-charcoal);
    font-family: 'Plus Jakarta Sans', sans-serif;
    line-height: 1.3;
}
.sidebar-user-email {
    font-size: 11px;
    color: var(--color-warmgray);
    font-family: 'Plus Jakarta Sans', sans-serif;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

/* ── Navigation Section Labels ────────────────────────────────────────── */
.nav-section-label {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    color: #9B9389;
    padding: 0 12px 6px 12px;
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* ── Sidebar Nav Buttons — Icon + Label style ────────────────────────── */
section[data-testid="stSidebar"] button[data-testid="baseButton-secondary"] {
    background: transparent !important;
    border: none !important;
    border-radius: 8px !important;
    color: var(--color-charcoal) !important;
    font-weight: 500 !important;
    font-size: 13.5px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    text-align: left !important;
    justify-content: flex-start !important;
    padding: 9px 14px !important;
    margin: 1px 0 !important;
    box-shadow: none !important;
    transition: all 0.18s ease !important;
    opacity: 1 !important;
}

section[data-testid="stSidebar"] button[data-testid="baseButton-secondary"] p,
section[data-testid="stSidebar"] button[data-testid="baseButton-secondary"] span {
    color: #3D3A36 !important;
    font-weight: 500 !important;
    font-size: 13.5px !important;
    opacity: 1 !important;
}

section[data-testid="stSidebar"] button[data-testid="baseButton-secondary"]:hover {
    background: rgba(184, 117, 93, 0.08) !important;
    border: none !important;
    box-shadow: none !important;
    transform: none !important;
}

section[data-testid="stSidebar"] button[data-testid="baseButton-secondary"]:hover p,
section[data-testid="stSidebar"] button[data-testid="baseButton-secondary"]:hover span {
    color: var(--color-terracotta) !important;
    font-weight: 600 !important;
}

/* Active nav item — target buttons right before the active marker */
section[data-testid="stSidebar"] .nav-active-marker {
    display: none !important;
}

/* We can't use CSS sibling selectors reliably across Streamlit widget divs,
   so we use a small JS snippet below to highlight the active nav button. */

/* Fallback active-button styling (applied via JS class) */
section[data-testid="stSidebar"] button.ef-nav-active {
    background: rgba(184, 117, 93, 0.12) !important;
    border-left: 3px solid var(--color-terracotta) !important;
    border-radius: 0 8px 8px 0 !important;
}
section[data-testid="stSidebar"] button.ef-nav-active p,
section[data-testid="stSidebar"] button.ef-nav-active span {
    color: var(--color-terracotta-dark) !important;
    font-weight: 700 !important;
}

/* ── Sign-Out Button Special Styling ──────────────────────────────────── */
.sidebar-signout-spacer {
    height: 24px;
}

section[data-testid="stSidebar"] button[key="btn_signout"],
section[data-testid="stSidebar"] div:last-child button[data-testid="baseButton-secondary"] {
    background-color: #FFFFFF !important;
    border: 1px solid #D4C9BA !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 10px 16px !important;
    box-shadow: 0 2px 6px rgba(48, 46, 43, 0.04) !important;
    margin-top: 8px !important;
}

/* ─── FORM ELEMENTS, LABELS & INPUTS ───────────────────────────────────────── */
/* Input Labels: Crisp Dark Text */
label[data-testid="stWidgetLabel"] p,
div[data-testid="stTextInput"] label p,
div[data-testid="stTextArea"] label p,
div[data-testid="stSelectbox"] label p,
div[data-testid="stSlider"] label p {
    color: #242220 !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    opacity: 1 !important;
    margin-bottom: 4px !important;
}

/* Input Fields (Text inputs, password fields) */
div[data-baseweb="input"],
div[data-baseweb="input"] > div {
    background-color: #FFFFFF !important;
    border: 1px solid #D4C9BA !important;
    border-radius: 8px !important;
    color: #1E1C1A !important;
}

div[data-baseweb="input"] input {
    color: #1E1C1A !important;
    background-color: transparent !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    padding: 10px 12px !important;
}

div[data-baseweb="input"] input::placeholder {
    color: #8C857B !important;
    opacity: 1 !important;
}

div[data-baseweb="input"]:focus-within {
    border-color: var(--color-terracotta) !important;
    box-shadow: 0 0 0 2px rgba(184, 117, 93, 0.2) !important;
}

/* Password Eye Icon */
div[data-baseweb="input"] button {
    color: #6E685F !important;
}

/* Text Area */
div[data-baseweb="textarea"] textarea {
    background-color: #FFFFFF !important;
    color: #1E1C1A !important;
    border: 1px solid #D4C9BA !important;
    border-radius: 8px !important;
    font-size: 14px !important;
}

/* ─── BUTTONS (HIGH CONTRAST & VISIBLE BEFORE HOVER) ───────────────────────── */
/* Primary & Form Submit Buttons */
div[data-testid="stFormSubmitButton"] button,
button[kind="primary"],
button[data-testid="baseButton-primary"] {
    background-color: var(--color-terracotta) !important;
    border: 1px solid var(--color-terracotta-dark) !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    letter-spacing: 0.02em !important;
    border-radius: 8px !important;
    padding: 12px 20px !important;
    box-shadow: 0 2px 8px rgba(184, 117, 93, 0.25) !important;
    opacity: 1 !important;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    cursor: pointer !important;
}

/* Inner Text of Primary Buttons — Fully Visible White */
div[data-testid="stFormSubmitButton"] button p,
div[data-testid="stFormSubmitButton"] button span,
button[kind="primary"] p,
button[kind="primary"] span,
button[data-testid="baseButton-primary"] p,
button[data-testid="baseButton-primary"] span {
    color: #FFFFFF !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    opacity: 1 !important;
}

/* Primary Button Hover State */
div[data-testid="stFormSubmitButton"] button:hover,
button[kind="primary"]:hover,
button[data-testid="baseButton-primary"]:hover {
    background-color: var(--color-terracotta-dark) !important;
    border-color: #7D4532 !important;
    color: #FFFFFF !important;
    box-shadow: 0 6px 18px rgba(184, 117, 93, 0.4) !important;
    transform: translateY(-1px) !important;
}

div[data-testid="stFormSubmitButton"] button:hover p,
div[data-testid="stFormSubmitButton"] button:hover span,
button[kind="primary"]:hover p,
button[kind="primary"]:hover span,
button[data-testid="baseButton-primary"]:hover p,
button[data-testid="baseButton-primary"]:hover span {
    color: #FFFFFF !important;
}

/* Secondary / Generic Buttons (outside sidebar) */
.stApp > div > div > section[data-testid="stMain"] button[kind="secondary"],
.stApp > div > div > section[data-testid="stMain"] button[data-testid="baseButton-secondary"] {
    background-color: #FFFFFF !important;
    border: 1px solid #D4C9BA !important;
    color: var(--color-charcoal) !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    border-radius: 8px !important;
    box-shadow: 0 2px 6px rgba(48, 46, 43, 0.04) !important;
    transition: all 0.2s ease !important;
    opacity: 1 !important;
}

.stApp > div > div > section[data-testid="stMain"] button[kind="secondary"] p,
.stApp > div > div > section[data-testid="stMain"] button[kind="secondary"] span,
.stApp > div > div > section[data-testid="stMain"] button[data-testid="baseButton-secondary"] p,
.stApp > div > div > section[data-testid="stMain"] button[data-testid="baseButton-secondary"] span {
    color: var(--color-charcoal) !important;
    font-weight: 600 !important;
    opacity: 1 !important;
}

.stApp > div > div > section[data-testid="stMain"] button[kind="secondary"]:hover,
.stApp > div > div > section[data-testid="stMain"] button[data-testid="baseButton-secondary"]:hover {
    background-color: #FAF6F0 !important;
    border-color: var(--color-terracotta) !important;
    color: var(--color-terracotta) !important;
    box-shadow: 0 4px 12px rgba(184, 117, 93, 0.15) !important;
}

.stApp > div > div > section[data-testid="stMain"] button[kind="secondary"]:hover p,
.stApp > div > div > section[data-testid="stMain"] button[kind="secondary"]:hover span,
.stApp > div > div > section[data-testid="stMain"] button[data-testid="baseButton-secondary"]:hover p,
.stApp > div > div > section[data-testid="stMain"] button[data-testid="baseButton-secondary"]:hover span {
    color: var(--color-terracotta) !important;
}

/* ─── TABS STYLING (HIGH CONTRAST & LEGIBLE) ───────────────────────────────── */
button[data-baseweb="tab"] {
    font-weight: 600 !important;
    font-size: 15px !important;
    color: #555048 !important; /* Visible dark warm-gray */
    opacity: 1 !important;
    padding: 10px 16px !important;
    transition: all 0.15s ease !important;
}

button[data-baseweb="tab"] p,
button[data-baseweb="tab"] span {
    color: #555048 !important;
    font-weight: 600 !important;
    opacity: 1 !important;
}

button[data-baseweb="tab"]:hover {
    color: var(--color-terracotta) !important;
}

button[data-baseweb="tab"]:hover p,
button[data-baseweb="tab"]:hover span {
    color: var(--color-terracotta) !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: var(--color-terracotta) !important;
    border-bottom: 2px solid var(--color-terracotta) !important;
    font-weight: 700 !important;
}

button[data-baseweb="tab"][aria-selected="true"] p,
button[data-baseweb="tab"][aria-selected="true"] span {
    color: var(--color-terracotta) !important;
    font-weight: 700 !important;
}

/* ─── EDITORIAL CARDS & STAT BOXES ─────────────────────────────────────────── */
.editorial-card {
    background: #FFFFFF;
    border: 1px solid var(--color-sand);
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 4px 14px rgba(48, 46, 43, 0.05);
    margin-bottom: 20px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.editorial-card:hover {
    box-shadow: 0 8px 24px rgba(48, 46, 43, 0.08);
}

.stat-card {
    background: #FFFFFF;
    border: 1px solid var(--color-sand);
    border-radius: 10px;
    padding: 16px 20px;
    text-align: left;
    border-left: 4px solid var(--color-terracotta);
    box-shadow: 0 2px 8px rgba(48, 46, 43, 0.04);
}
.stat-value {
    font-size: 28px;
    font-weight: 700;
    font-family: 'Cinzel', serif;
    color: var(--color-text-dark);
}
.stat-label {
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--color-warmgray);
}

/* Badges */
.badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.badge-terracotta {
    background: rgba(184, 117, 93, 0.15);
    color: #9A5B45;
    border: 1px solid rgba(184, 117, 93, 0.3);
}
.badge-sage {
    background: rgba(120, 136, 117, 0.15);
    color: #4C5D49;
    border: 1px solid rgba(120, 136, 117, 0.3);
}
.badge-olive {
    background: rgba(164, 161, 124, 0.2);
    color: #635F3D;
    border: 1px solid rgba(164, 161, 124, 0.35);
}
.badge-sand {
    background: #E9DFD1;
    color: var(--color-text-dark);
}

/* Question Banner */
.question-banner {
    background: #FFFFFF;
    border-left: 5px solid var(--color-terracotta);
    border-radius: 8px;
    padding: 20px;
    margin: 16px 0;
    border: 1px solid var(--color-sand);
    border-left-width: 5px;
    box-shadow: 0 2px 8px rgba(48, 46, 43, 0.04);
}
.question-text {
    font-size: 17px;
    font-weight: 600;
    line-height: 1.5;
    color: var(--color-text-dark);
}
</style>
"""

# JavaScript snippet to highlight the active sidebar nav button and suppress
# browser autocomplete on sign-in password fields.
SIDEBAR_JS = """
<script>
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        // ── Active Nav Button Highlighting ──
        var sidebar = document.querySelector('section[data-testid="stSidebar"]');
        if (!sidebar) return;
        var markers = sidebar.querySelectorAll('.nav-active-marker');
        markers.forEach(function(marker) {
            // Walk backwards through previous sibling wrappers to find the button
            var prev = marker.closest('div[data-testid="stVerticalBlock"] > div, div[data-testid="column"] > div');
            if (!prev) prev = marker.parentElement;
            // Try to find the button in the immediately preceding Streamlit element block
            var parent = marker.parentElement;
            if (parent && parent.previousElementSibling) {
                var btn = parent.previousElementSibling.querySelector('button');
                if (btn) btn.classList.add('ef-nav-active');
            }
        });

        // ── Suppress autocomplete on Sign-In password field ──
        var loginForm = document.querySelector('[data-testid="stForm"]');
        if (loginForm) {
            var pwInputs = loginForm.querySelectorAll('input[type="password"]');
            pwInputs.forEach(function(inp) {
                inp.setAttribute('autocomplete', 'current-password');
            });
        }
    }, 500);
});

// Re-run on Streamlit rerenders
var _efObserver = new MutationObserver(function() {
    // Active nav
    var sidebar = document.querySelector('section[data-testid="stSidebar"]');
    if (sidebar) {
        sidebar.querySelectorAll('button.ef-nav-active').forEach(function(b) {
            b.classList.remove('ef-nav-active');
        });
        sidebar.querySelectorAll('.nav-active-marker').forEach(function(marker) {
            var parent = marker.parentElement;
            if (parent && parent.previousElementSibling) {
                var btn = parent.previousElementSibling.querySelector('button');
                if (btn) btn.classList.add('ef-nav-active');
            }
        });
    }
    // Autocomplete suppression
    document.querySelectorAll('[data-testid="stForm"]').forEach(function(form) {
        form.querySelectorAll('input[type="password"]').forEach(function(inp) {
            if (!inp.getAttribute('autocomplete') || inp.getAttribute('autocomplete') === 'new-password') {
                inp.setAttribute('autocomplete', 'current-password');
            }
        });
    });
});
_efObserver.observe(document.body, { childList: true, subtree: true });
</script>
"""


def apply_styles():
    import streamlit as st
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    st.markdown(SIDEBAR_JS, unsafe_allow_html=True)
