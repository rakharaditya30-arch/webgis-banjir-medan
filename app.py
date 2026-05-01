"""
=============================================================================
  SISTEM INFORMASI GEOGRAFIS KERAWANAN BANJIR KOTA MEDAN
  WebGIS Dashboard v2.1 — Analisis Risiko Banjir
  Dibuat dengan: Streamlit + Leafmap + Localtileserver
=============================================================================
"""

import os
import random
import streamlit as st
import leafmap.foliumap as leafmap

# ─────────────────────────────────────────────────────────────
#  KONFIGURASI HALAMAN
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Banjir Kota Medan",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
#  SESSION STATE — inisialisasi semua state di sini
# ─────────────────────────────────────────────────────────────
if "panel_open"   not in st.session_state: st.session_state.panel_open   = False
if "ctrl_opacity" not in st.session_state: st.session_state.ctrl_opacity = 0.75
if "ctrl_basemap" not in st.session_state: st.session_state.ctrl_basemap = "CartoDB.DarkMatter"

# ─────────────────────────────────────────────────────────────
#  KONSTANTA
# ─────────────────────────────────────────────────────────────
RASTER_FILE  = "risiko_banjir_medan.tif"
MEDAN_CENTER = [3.5952, 98.6722]
DEFAULT_ZOOM = 11

RISK_COLORMAP = {
    "colors": ["#22c55e", "#eab308", "#f97316", "#ef4444"],
    "vmin": 1,
    "vmax": 4,
}

LEGEND_ENTRIES = {
    "Risiko Rendah":        "#22c55e",
    "Risiko Sedang":        "#eab308",
    "Risiko Tinggi":        "#f97316",
    "Risiko Sangat Tinggi": "#ef4444",
}

BASEMAP_OPTIONS = [
    "CartoDB.DarkMatter",
    "SATELLITE",
    "OpenStreetMap",
    "CartoDB.Positron",
]

# CATATAN: Ikon/simbol pada basemap telah dihapus untuk tampilan minimalis
BASEMAP_ICONS = {
    "CartoDB.DarkMatter": "",
    "SATELLITE":          "",
    "OpenStreetMap":      "",
    "CartoDB.Positron":   "",
}

RISK_DISTRIBUTION = {
    "Rendah":        {"km2": 82, "pct": 31, "color": "#22c55e"},
    "Sedang":        {"km2": 74, "pct": 28, "color": "#eab308"},
    "Tinggi":        {"km2": 63, "pct": 24, "color": "#f97316"},
    "Sangat Tinggi": {"km2": 46, "pct": 17, "color": "#ef4444"},
}

EVAKUASI_TIPS = [
    ("map",    "Kenali Rute",      "Hafal minimal 2 jalur evakuasi dari rumah menuju titik aman terdekat."),
    ("bag",    "Tas Siaga",        "Siapkan tas darurat: dokumen penting, obat, air, makanan 3 hari, senter."),
    ("phone",  "Pantau Info",      "Ikuti siaran BMKG & BPBD Medan untuk peringatan dini cuaca ekstrem."),
    ("home",   "Amankan Rumah",    "Matikan listrik & gas sebelum meninggalkan rumah saat banjir datang."),
    ("family", "Evakuasi Bersama", "Pastikan lansia & anak-anak dievakuasi lebih dulu ke titik aman."),
    ("phone2", "Nomor Darurat",    "BPBD Medan: 119 ext 5 · Basarnas: 115 · PMI: (061) 4511476"),
]

KECAMATAN_RISIKO = [
    ("Medan Deli",     "Sangat Tinggi", "#ef4444"),
    ("Medan Belawan",  "Sangat Tinggi", "#ef4444"),
    ("Medan Labuhan",  "Tinggi",        "#f97316"),
    ("Medan Marelan",  "Tinggi",        "#f97316"),
    ("Medan Helvetia", "Sedang",        "#eab308"),
    ("Medan Sunggal",  "Sedang",        "#eab308"),
    ("Medan Baru",     "Rendah",        "#22c55e"),
    ("Medan Selayang", "Rendah",        "#22c55e"),
]


# ─────────────────────────────────────────────────────────────
#  CSS
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
.stApp { background: #07101c; color: #e2e8f0; }

/* ── Keyframes ── */
@keyframes rain-fall {
    0%  { transform:translateY(-20px);opacity:0; }
    10% { opacity:.55; }
    90% { opacity:.55; }
    100%{ transform:translateY(140px);opacity:0; }
}
@keyframes fade-up   { from{opacity:0;transform:translateY(18px)} to{opacity:1;transform:translateY(0)} }
@keyframes slide-in  { from{opacity:0;transform:translateX(-14px)} to{opacity:1;transform:translateX(0)} }
@keyframes slide-down{ from{opacity:0;transform:translateY(-10px)} to{opacity:1;transform:translateY(0)} }
@keyframes bar-grow  { from{width:0} to{width:var(--bw)} }
@keyframes glow-pulse{ 0%,100%{opacity:.4} 50%{opacity:1} }
@keyframes count-in  { from{opacity:0;transform:scale(.9)} to{opacity:1;transform:scale(1)} }
@keyframes spin      { to{transform:rotate(360deg)} }

/* ─── HERO ─────────────────────────────────────── */
.hero-banner {
    position:relative;
    background:linear-gradient(135deg,#040d1a 0%,#091e3a 45%,#0c2b4d 75%,#050c1a 100%);
    border:1px solid rgba(56,189,248,.18); border-radius:20px;
    padding:34px 38px; margin-bottom:16px; overflow:hidden;
    animation:fade-up .55s ease both;
}
.hero-banner::after {
    content:'';position:absolute;inset:0;
    background:radial-gradient(ellipse 55% 90% at 92% 50%,rgba(56,189,248,.07) 0%,transparent 70%);
    pointer-events:none;
}
.hero-title {
    font-size:1.8rem;font-weight:900;color:#f0f9ff;
    letter-spacing:-.03em;margin:0 0 6px;line-height:1.15;
}
.hero-subtitle { font-size:.83rem;color:#7dd3fc;letter-spacing:.1em;text-transform:uppercase;font-weight:600; }
.hero-badge {
    display:inline-flex;align-items:center;gap:5px;
    background:rgba(56,189,248,.09);border:1px solid rgba(56,189,248,.28);
    color:#38bdf8;font-size:.7rem;font-weight:700;
    padding:4px 12px;border-radius:99px;margin-bottom:14px;
    letter-spacing:.07em;text-transform:uppercase;
}
.rain-container{position:absolute;inset:0;pointer-events:none;overflow:hidden;}
.raindrop {
    position:absolute;width:1.5px;height:14px;
    background:linear-gradient(to bottom,transparent,rgba(56,189,248,.3));
    border-radius:2px;animation:rain-fall linear infinite;
}

/* ─── BURGER STRIP ──────────────────────────────── */
.burger-strip {
    display:flex;align-items:center;gap:12px;margin-bottom:10px;
}
.burger-status {
    font-size:.76rem;color:#334155;font-weight:600;letter-spacing:.04em;
    transition:color .2s;
}
.burger-status.open{ color:#38bdf8; }

/* Style the Streamlit burger button via JS-injected class */
button.gis-burger {
    background: linear-gradient(135deg,#091e38 0%,#0c2847 100%) !important;
    border: 1px solid rgba(56,189,248,.45) !important;
    color: #38bdf8 !important;
    font-size: 1.15rem !important;
    font-weight: 700 !important;
    width: 46px !important;
    height: 46px !important;
    min-height: 46px !important;
    padding: 0 !important;
    border-radius: 13px !important;
    box-shadow: 0 0 18px rgba(56,189,248,.12) !important;
    transition: all .2s ease !important;
    line-height: 1 !important;
    letter-spacing: 0 !important;
}
button.gis-burger:hover {
    background: linear-gradient(135deg,#0f2d50 0%,#113460 100%) !important;
    border-color: rgba(56,189,248,.75) !important;
    box-shadow: 0 0 28px rgba(56,189,248,.28) !important;
    transform: scale(1.05) !important;
}
button.gis-burger.panel-open {
    background: rgba(56,189,248,.15) !important;
    border-color: #38bdf8 !important;
    box-shadow: 0 0 24px rgba(56,189,248,.35) !important;
}

/* Style the close button */
button.gis-close {
    background: rgba(239,68,68,.12) !important;
    border: 1px solid rgba(239,68,68,.3) !important;
    color: #f87171 !important;
    font-size: .78rem !important;
    font-weight: 700 !important;
    padding: 4px 14px !important;
    border-radius: 8px !important;
    transition: all .2s !important;
    height: 34px !important;
    min-height: 34px !important;
    white-space: nowrap !important;
}
button.gis-close:hover {
    background: rgba(239,68,68,.22) !important;
    border-color: rgba(239,68,68,.55) !important;
    box-shadow: 0 0 12px rgba(239,68,68,.2) !important;
}

/* ─── CONTROL PANEL ─────────────────────────────── */
.ctrl-panel-card {
    background: linear-gradient(135deg, rgba(6,15,30,.97) 0%, rgba(8,20,40,.97) 100%);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border: 1px solid rgba(56,189,248,.22);
    border-radius: 18px;
    padding: 22px 26px 18px;
    margin-bottom: 12px;
    box-shadow: 0 12px 40px rgba(0,0,0,.55), 0 0 0 1px rgba(56,189,248,.05), inset 0 1px 0 rgba(56,189,248,.07);
    animation: slide-down .28s cubic-bezier(.22,.68,0,1.2) both;
    position: relative;
}
.ctrl-panel-card::before {
    content:'';position:absolute;top:0;left:0;right:0;height:1px;
    background:linear-gradient(90deg,transparent,rgba(56,189,248,.35),transparent);
    border-radius:18px 18px 0 0;
}
.ctrl-header {
    display:flex;align-items:center;justify-content:space-between;
    margin-bottom:18px;
}
.ctrl-header-title {
    font-size:.82rem;font-weight:800;color:#7dd3fc;
    text-transform:uppercase;letter-spacing:.1em;
    display:flex;align-items:center;gap:8px;
}
.ctrl-section-label {
    font-size:.67rem;font-weight:800;color:#1e3a5f;
    text-transform:uppercase;letter-spacing:.12em;margin-bottom:8px;
}
.ctrl-divider {
    border:none;border-left:1px solid rgba(56,189,248,.1);
    height:auto;align-self:stretch;margin:0 4px;
}

/* Opacity display badge */
.opacity-badge {
    display:inline-flex;align-items:center;
    background:rgba(56,189,248,.1);border:1px solid rgba(56,189,248,.2);
    color:#38bdf8;font-family:'JetBrains Mono',monospace;
    font-size:.8rem;font-weight:600;padding:3px 10px;
    border-radius:8px;margin-top:4px;
}

/* Basemap option cards */
.bm-grid { display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-top:4px; }
.bm-card {
    background:rgba(12,35,62,.5);border:1px solid rgba(56,189,248,.1);
    border-radius:9px;padding:7px 10px;cursor:pointer;
    transition:all .15s;text-align:center;font-size:.72rem;
    color:#64748b;font-weight:600;
}
.bm-card.active { background:rgba(56,189,248,.12);border-color:rgba(56,189,248,.45);color:#38bdf8; }
.bm-card:hover  { border-color:rgba(56,189,248,.3);color:#94a3b8; }

/* Legend mini in panel */
.panel-legend { margin-top:4px; }
.pl-item {
    display:flex;align-items:center;gap:8px;
    font-size:.76rem;color:#94a3b8;padding:4px 0;
    border-bottom:1px solid rgba(255,255,255,.03);
}
.pl-item:last-child { border-bottom:none; }
.pl-dot { width:10px;height:10px;border-radius:3px;flex-shrink:0; }

/* ─── SIDEBAR ───────────────────────────────────── */
[data-testid="stSidebar"] {
    background:linear-gradient(180deg,#060d1a 0%,#07101c 100%) !important;
    border-right:1px solid rgba(56,189,248,.1) !important;
}
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"] {
    visibility:visible !important;opacity:1 !important;display:flex !important;
}
#sb-toggle-tab {
    position:fixed;top:50%;left:0;transform:translateY(-50%);
    z-index:99999;width:22px;height:80px;
    background:linear-gradient(180deg,#091e38 0%,#0a1628 100%);
    border:1px solid rgba(56,189,248,.45);border-left:none;
    border-radius:0 14px 14px 0;display:flex;align-items:center;
    justify-content:center;cursor:pointer;
    box-shadow:5px 0 18px rgba(56,189,248,.15);
    transition:width .2s,box-shadow .2s,background .2s;user-select:none;
}
#sb-toggle-tab:hover {
    width:32px;background:linear-gradient(180deg,#0f2d48 0%,#0a2038 100%);
    box-shadow:7px 0 26px rgba(56,189,248,.32);
}
#sb-toggle-tab::after {
    content:'';position:absolute;top:10px;right:5px;
    width:5px;height:5px;background:#38bdf8;border-radius:50%;
    animation:glow-pulse 2s ease-in-out infinite;
}
#sb-toggle-tab svg{flex-shrink:0;transition:transform .25s;}

.sb-section{font-size:.67rem;font-weight:800;color:#1e3a5f;text-transform:uppercase;letter-spacing:.12em;margin:14px 0 7px;}
.sb-divider{border:none;border-top:1px solid rgba(56,189,248,.09);margin:10px 0;}
.stat-grid{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin:8px 0;}
.stat-card{background:rgba(12,35,62,.5);border:1px solid rgba(56,189,248,.1);border-radius:10px;padding:10px 7px;text-align:center;animation:count-in .5s ease both;transition:border-color .2s,transform .2s;}
.stat-card:hover{border-color:rgba(56,189,248,.3);transform:translateY(-2px);}
.stat-value{font-size:1.3rem;font-weight:900;color:#38bdf8;font-family:'JetBrains Mono',monospace;}
.stat-label{font-size:.62rem;color:#334155;text-transform:uppercase;letter-spacing:.05em;margin-top:3px;font-weight:700;}
.legend-item{display:flex;align-items:center;gap:9px;padding:6px 9px;border-radius:8px;margin-bottom:3px;font-size:.79rem;color:#94a3b8;border:1px solid transparent;transition:background .15s,border-color .15s;}
.legend-item:hover{background:rgba(56,189,248,.05);border-color:rgba(56,189,248,.12);}
.legend-dot{width:11px;height:11px;border-radius:3px;flex-shrink:0;}

/* ─── TABS ──────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"]{background:rgba(7,16,28,.9) !important;border-bottom:1px solid rgba(56,189,248,.1) !important;gap:3px;}
.stTabs [data-baseweb="tab"]{color:#334155 !important;font-size:.82rem !important;font-weight:700 !important;padding:8px 18px !important;border-radius:8px 8px 0 0 !important;transition:color .2s !important;}
.stTabs [aria-selected="true"]{color:#38bdf8 !important;background:rgba(56,189,248,.07) !important;border-bottom:2px solid #38bdf8 !important;}
.stTabs [data-baseweb="tab-panel"]{background:rgba(7,16,28,.7) !important;border:1px solid rgba(56,189,248,.09) !important;border-top:none !important;border-radius:0 0 14px 14px !important;padding:22px !important;}

/* ─── RISK BARS ─────────────────────────────────── */
.risk-bar-wrap{margin-bottom:14px;animation:slide-in .4s ease both;}
.risk-bar-label{display:flex;justify-content:space-between;font-size:.78rem;color:#64748b;margin-bottom:5px;font-weight:600;}
.risk-bar-track{height:9px;background:rgba(255,255,255,.04);border-radius:99px;overflow:hidden;}
.risk-bar-fill{height:100%;border-radius:99px;animation:bar-grow 1.1s cubic-bezier(.4,0,.2,1) both;}

/* ─── TIP CARDS ─────────────────────────────────── */
.tip-card{
    background:rgba(9,28,56,.5);border:1px solid rgba(56,189,248,.09);
    border-radius:12px;padding:16px 18px;margin-bottom:9px;
    animation:fade-up .4s ease both;
    transition:border-color .2s,transform .2s,box-shadow .2s;
}
.tip-card:hover{border-color:rgba(56,189,248,.28);transform:translateY(-2px);box-shadow:0 6px 20px rgba(0,0,0,.3);}
.tip-title{font-size:.84rem;font-weight:700;color:#e2e8f0;margin-bottom:4px;}
.tip-body {font-size:.77rem;color:#475569;line-height:1.55;}

/* ─── KEC TABLE ─────────────────────────────────── */
.kec-table{width:100%;border-collapse:collapse;}
.kec-table th{font-size:.67rem;text-transform:uppercase;letter-spacing:.09em;color:#1e3a5f;font-weight:800;padding:6px 12px;border-bottom:1px solid rgba(56,189,248,.09);text-align:left;}
.kec-table td{font-size:.81rem;color:#94a3b8;padding:9px 12px;border-bottom:1px solid rgba(255,255,255,.03);}
.kec-table tr:hover td{background:rgba(56,189,248,.03);}
.risk-badge{display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border-radius:99px;font-size:.71rem;font-weight:700;}

/* ─── CALC RESULT ───────────────────────────────── */
.calc-result{border-radius:14px;padding:22px 24px;margin-top:16px;text-align:center;animation:fade-up .35s ease both;border:2px solid;}
.cr-level{font-size:1.15rem;font-weight:800;margin-bottom:6px;}
.cr-desc {font-size:.81rem;line-height:1.6;color:#94a3b8;}

/* ─── BOTTOM CARDS ──────────────────────────────── */
.ibc{
    background:rgba(9,28,56,.4);border:1px solid rgba(56,189,248,.1);
    border-radius:12px;padding:16px 16px;text-align:center;
    transition:border-color .2s,transform .2s;height:100%;
    animation:fade-up .5s ease both;
}
.ibc:hover{border-color:rgba(56,189,248,.28);transform:translateY(-3px);}
.ibc-label{font-size:.67rem;color:#7dd3fc;font-weight:800;text-transform:uppercase;letter-spacing:.07em;margin-bottom:5px;}
.ibc-val  {font-size:.88rem;color:#e2e8f0;font-weight:600;}

/* ─── WARNING ───────────────────────────────────── */
.warning-box{background:rgba(239,68,68,.07);border:1px solid rgba(239,68,68,.22);border-radius:12px;padding:14px 18px;color:#fca5a5;font-size:.82rem;line-height:1.6;margin-bottom:14px;}

/* ─── FOOTER ────────────────────────────────────── */
.footer{text-align:center;color:#1e293b;font-size:.74rem;padding:16px 0 6px;border-top:1px solid rgba(56,189,248,.06);margin-top:18px;}

/* ─── HIDE SLIDER LABEL (internal panel widgets) ── */
div[data-ctrl-slider="1"] label { display:none !important; }
div[data-ctrl-slider="1"] [data-baseweb="slider"] { margin-top:2px; }

/* ─── HIDE CHROME ───────────────────────────────── */
#MainMenu{visibility:hidden;}
footer   {visibility:hidden;}
header   {visibility:hidden;}

/* ─── HIDE ANCHOR LINK SYMBOLS ──────────────────── */
/* Sembunyikan semua simbol tautan/rantai di samping heading secara permanen */
.header-anchor,
[data-testid="stHeaderActionElements"],
[data-testid="StyledLinkIconContainer"],
a.anchor-link,
a[href^="#"] svg,
h1 a, h2 a, h3 a, h4 a,
h1 .anchor, h2 .anchor, h3 .anchor, h4 .anchor,
.stMarkdown h1 a,
.stMarkdown h2 a,
.stMarkdown h3 a {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
    width: 0 !important;
    height: 0 !important;
    overflow: hidden !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
#  JAVASCRIPT — sidebar tab + burger button styler
#  (Jam real-time telah dihapus untuk performa lebih ringan)
# ─────────────────────────────────────────────────────────────
st.markdown("""
<script>
(function () {
  'use strict';

  /* ── 1. Sidebar edge tab ─── */
  var CHEVRON = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" '
    + 'stroke="#38bdf8" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">'
    + '<polyline points="9 18 15 12 9 6"></polyline></svg>';

  function createSidebarTab() {
    if (document.getElementById('sb-toggle-tab')) return;
    var tab = document.createElement('div');
    tab.id = 'sb-toggle-tab';
    tab.innerHTML = CHEVRON;
    tab.title = 'Buka / Tutup Panel Sidebar';
    tab.addEventListener('click', function () {
      var btn = document.querySelector('[data-testid="stSidebarCollapseButton"] button')
             || document.querySelector('[data-testid="collapsedControl"] button')
             || document.querySelector('button[aria-label="Close sidebar"]')
             || document.querySelector('button[aria-label="Open sidebar"]');
      if (btn) { btn.click(); }
      else {
        var sb = document.querySelector('[data-testid="stSidebar"]');
        if (sb) {
          var hidden = sb.style.marginLeft === '-21rem';
          sb.style.transition = 'margin-left .3s ease';
          sb.style.marginLeft = hidden ? '0' : '-21rem';
        }
      }
      var svg = tab.querySelector('svg');
      if (svg) svg.style.transform = svg.style.transform.includes('scaleX(-1)') ? '' : 'scaleX(-1)';
    });
    document.body.appendChild(tab);
  }

  /* ── 2. Style burger & close buttons by text ─── */
  function styleSpecialButtons() {
    document.querySelectorAll('button').forEach(function(btn) {
      var txt = btn.textContent.trim();
      if (txt === '☰' || txt === '☰ ') {
        btn.classList.add('gis-burger');
      }
      if (txt === '✕ Tutup Panel' || txt.includes('Tutup Panel')) {
        btn.classList.add('gis-close');
      }
    });
  }

  /* ── 3. Sync basemap radio selection UI ─── */
  function syncBasemapUI() {
    var sel = document.getElementById('active-basemap-name');
    if (!sel) return;
    var active = sel.value || 'CartoDB.DarkMatter';
    document.querySelectorAll('.bm-card').forEach(function(c) {
      c.classList.toggle('active', c.dataset.bm === active);
    });
  }

  /* ── Init ─── */
  function init() {
    createSidebarTab();
    styleSpecialButtons();
    setInterval(createSidebarTab,  1800);
    setInterval(styleSpecialButtons, 600);
    setInterval(syncBasemapUI,       800);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    setTimeout(init, 80);
  }
})();
</script>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
#  SIDEBAR — info only (kontrol peta dipindah ke burger panel)
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding-bottom:2px'>
        <div style='font-size:1rem;font-weight:900;color:#f0f9ff;margin-top:6px;line-height:1.25'>
            Dashboard Risiko Banjir<br>Kota Medan
        </div>
        <div style='font-size:.69rem;color:#7dd3fc;margin-top:5px;font-weight:700;
                    letter-spacing:.07em;text-transform:uppercase'>BMKG · BIG · UPI</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<hr class='sb-divider'>", unsafe_allow_html=True)

    # Tip buka panel
    st.markdown("""
    <div style='background:rgba(56,189,248,.07);border:1px solid rgba(56,189,248,.15);
                border-radius:10px;padding:10px 13px;font-size:.76rem;color:#64748b;
                line-height:1.55;margin-bottom:4px'>
        <strong style='color:#38bdf8'>☰</strong> Klik tombol burger di atas peta
        untuk mengatur <strong style='color:#7dd3fc'>transparansi, basemap,</strong>
        dan kontrol peta lainnya.
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<hr class='sb-divider'>", unsafe_allow_html=True)

    # Statistik
    st.markdown("<div class='sb-section'>Statistik Wilayah</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='stat-grid'>
        <div class='stat-card'><div class='stat-value'>265</div><div class='stat-label'>km² Luas</div></div>
        <div class='stat-card'><div class='stat-value'>21</div><div class='stat-label'>Kecamatan</div></div>
        <div class='stat-card'><div class='stat-value'>2.7M</div><div class='stat-label'>Penduduk</div></div>
        <div class='stat-card'><div class='stat-value'>4</div><div class='stat-label'>Kelas Risiko</div></div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<hr class='sb-divider'>", unsafe_allow_html=True)

    # Legenda
    st.markdown("<div class='sb-section'>Legenda</div>", unsafe_allow_html=True)
    for label, color in LEGEND_ENTRIES.items():
        st.markdown(f"""
        <div class='legend-item'>
            <div class='legend-dot' style='background:{color};box-shadow:0 0 5px {color}55'></div>
            <span>{label}</span>
        </div>""", unsafe_allow_html=True)
    st.markdown("<hr class='sb-divider'>", unsafe_allow_html=True)

    # Metadata
    st.markdown("<div class='sb-section'>Metadata</div>", unsafe_allow_html=True)
    for k, v in [("Sumber","BMKG, BIG, Sentinel-2"),("Metode","Weighted Overlay (AHP)"),
                 ("Resolusi","10 m / piksel"),("Sistem","WGS 84 / UTM 47N"),("Tahun","2024")]:
        st.markdown(
            f"<div style='display:flex;gap:8px;margin-bottom:5px;font-size:.78rem'>"
            f"<span style='color:#7dd3fc;font-weight:700;min-width:58px'>{k}</span>"
            f"<span style='color:#334155'>{v}</span></div>",
            unsafe_allow_html=True,
        )


# ─────────────────────────────────────────────────────────────
#  HERO HEADER
# ─────────────────────────────────────────────────────────────
random.seed(42)
rain_html = "".join(
    f"<div class='raindrop' style='left:{random.randint(0,100)}%;"
    f"animation-duration:{round(random.uniform(1.2,2.6),2)}s;"
    f"animation-delay:{round(random.uniform(0,4),2)}s'></div>"
    for _ in range(30)
)
st.markdown(f"""
<div class='hero-banner'>
    <div class='rain-container'>{rain_html}</div>
    <div class='hero-badge'>WebGIS · Analisis Spasial · Kota Medan</div>
    <h1 class='hero-title'>Sistem Informasi Geografis<br>Kerawanan Banjir Kota Medan</h1>
    <p class='hero-subtitle'>Spatial Flood Risk Analysis Dashboard 2024</p>
</div>
""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════
#  BURGER MENU + CONTROL PANEL
# ═════════════════════════════════════════════════════════════

# ── Baca nilai saat ini dari session state ──
opacity        = st.session_state.ctrl_opacity
basemap_choice = st.session_state.ctrl_basemap

# ── Strip: tombol burger + status ──
burger_col, status_col, spacer_col = st.columns([0.045, 0.3, 0.655])

with burger_col:
    if st.button("☰", key="burger_toggle"):
        st.session_state.panel_open = not st.session_state.panel_open

with status_col:
    if st.session_state.panel_open:
        st.markdown(
            "<div class='burger-status open' style='padding-top:10px'>"
            "Pengaturan Peta Aktif</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<div class='burger-status' style='padding-top:10px'>"
            f"{basemap_choice} &nbsp;·&nbsp; "
            f"<span style='color:#38bdf8'>{int(opacity*100)}%</span> opasitas</div>",
            unsafe_allow_html=True,
        )

# ── Panel kontrol (muncul jika burger diklik) ──
if st.session_state.panel_open:

    st.markdown("<div class='ctrl-panel-card'>", unsafe_allow_html=True)

    # Header panel + tombol tutup
    hdr_l, hdr_r = st.columns([0.8, 0.2])
    with hdr_l:
        st.markdown(
            "<div class='ctrl-header-title'>Pengaturan Layer Peta</div>",
            unsafe_allow_html=True,
        )
    with hdr_r:
        if st.button("✕ Tutup Panel", key="close_panel"):
            st.session_state.panel_open = False
            st.rerun()

    st.markdown("<hr style='border:none;border-top:1px solid rgba(56,189,248,.1);margin:10px 0 16px'>",
                unsafe_allow_html=True)

    # ── Tiga kolom kontrol ──
    col_opacity, col_basemap, col_legend = st.columns([1.2, 1.4, 1.4])

    # ── Kolom 1: Opacity ──
    with col_opacity:
        st.markdown("<div class='ctrl-section-label'>Transparansi Layer Risiko</div>",
                    unsafe_allow_html=True)

        new_opacity = st.slider(
            "Opacity",
            min_value=0.0, max_value=1.0,
            value=st.session_state.ctrl_opacity,
            step=0.05,
            key="opacity_slider_panel",
            label_visibility="collapsed",
        )
        # Simpan ke session_state
        st.session_state.ctrl_opacity = new_opacity
        opacity = new_opacity

        # Visual bar opacity
        bar_w   = int(new_opacity * 100)
        bar_col = "#22c55e" if bar_w < 40 else "#eab308" if bar_w < 70 else "#38bdf8"
        st.markdown(f"""
        <div style='margin-top:6px'>
            <div style='display:flex;justify-content:space-between;
                        font-size:.7rem;color:#334155;margin-bottom:4px;font-family:JetBrains Mono,monospace'>
                <span>0%</span><span>50%</span><span>100%</span>
            </div>
            <div style='height:6px;background:rgba(255,255,255,.05);border-radius:99px;overflow:hidden'>
                <div style='height:100%;width:{bar_w}%;background:{bar_col};
                            border-radius:99px;transition:width .3s;
                            box-shadow:0 0 8px {bar_col}66'></div>
            </div>
            <div style='text-align:center;margin-top:6px'>
                <span class='opacity-badge'>{bar_w}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Kolom 2: Basemap ──
    with col_basemap:
        st.markdown("<div class='ctrl-section-label'>Pilih Basemap</div>",
                    unsafe_allow_html=True)

        new_basemap = st.radio(
            "Basemap",
            options=BASEMAP_OPTIONS,
            index=BASEMAP_OPTIONS.index(st.session_state.ctrl_basemap),
            key="basemap_radio_panel",
            label_visibility="collapsed",
        )
        st.session_state.ctrl_basemap = new_basemap
        basemap_choice = new_basemap

        # Tampilkan nama basemap aktif
        st.markdown(
            f"<div style='margin-top:8px;display:flex;align-items:center;gap:8px;"
            f"font-size:.78rem;color:#64748b'>"
            f"Aktif: <strong style='color:#38bdf8'>{new_basemap}</strong>"
            f"</div>",
            unsafe_allow_html=True,
        )

    # ── Kolom 3: Legenda + info ──
    with col_legend:
        st.markdown("<div class='ctrl-section-label'>Legenda Kelas Risiko</div>",
                    unsafe_allow_html=True)
        st.markdown("<div class='panel-legend'>", unsafe_allow_html=True)
        for lbl, col_hex in LEGEND_ENTRIES.items():
            st.markdown(
                f"<div class='pl-item'>"
                f"<div class='pl-dot' style='background:{col_hex};box-shadow:0 0 5px {col_hex}55'></div>"
                f"<span>{lbl}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

        # Distribusi singkat
        st.markdown("<br>", unsafe_allow_html=True)
        for name, d in RISK_DISTRIBUTION.items():
            st.markdown(
                f"<div style='display:flex;align-items:center;gap:7px;margin-bottom:5px'>"
                f"<div style='width:{d['pct']}%;max-width:90px;height:5px;"
                f"background:{d['color']};border-radius:99px;"
                f"box-shadow:0 0 5px {d['color']}44'></div>"
                f"<span style='font-size:.7rem;color:#334155'>{name}: {d['pct']}%</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)  # close ctrl-panel-card


# ─────────────────────────────────────────────────────────────
#  PETA
# ─────────────────────────────────────────────────────────────
raster_exists = os.path.isfile(RASTER_FILE)

if not raster_exists:
    st.markdown(
        f"<div class='warning-box'><strong>File Raster Tidak Ditemukan</strong> — "
        f"Salin <code>{RASTER_FILE}</code> ke folder yang sama dengan <code>app.py</code> "
        f"lalu jalankan ulang.</div>",
        unsafe_allow_html=True,
    )

m = leafmap.Map(
    center=MEDAN_CENTER, zoom=DEFAULT_ZOOM,
    draw_control=False, measure_control=False,
    fullscreen_control=True, attribution_control=True,
)
try:
    m.add_basemap("SATELLITE" if basemap_choice == "SATELLITE" else basemap_choice)
except Exception:
    m.add_basemap("CartoDB.DarkMatter")

if raster_exists:
    try:
        m.add_raster(
            source=RASTER_FILE,
            colormap=RISK_COLORMAP["colors"],
            vmin=RISK_COLORMAP["vmin"],
            vmax=RISK_COLORMAP["vmax"],
            layer_name="risiko_banjir_medan.tif",
            opacity=opacity,
            fit_bounds=True,
        )
        m.add_legend(
            title="Tingkat Risiko Banjir",
            legend_dict={
                "Rendah":        "#22c55e",
                "Sedang":        "#eab308",
                "Tinggi":        "#f97316",
                "Sangat Tinggi": "#ef4444",
            },
            position="bottomright",
        )
    except Exception as e:
        st.markdown(
            f"<div class='warning-box'><strong>Gagal Memuat Raster</strong><br>"
            f"<code>{e}</code></div>", unsafe_allow_html=True
        )

m.add_layer_control()
m.to_streamlit(height=570, responsive=True, scrolling=False)


# ─────────────────────────────────────────────────────────────
#  INFO CARDS — tanpa ikon, hanya label & nilai
# ─────────────────────────────────────────────────────────────
cols = st.columns(5)
cards = [
    ("Proyeksi",     "WGS 84 / UTM 47N"),
    ("Resolusi",     "10 m / piksel"),
    ("Pembaruan",    "Triwulanan"),
    ("Instansi",     "BMKG · BIG · UPI"),
    ("Curah Hujan",  "≥ 2.200 mm/th"),
]
for col, (lbl, val) in zip(cols, cards):
    with col:
        st.markdown(f"""
        <div class='ibc'>
            <div class='ibc-label'>{lbl}</div>
            <div class='ibc-val'>{val}</div>
        </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
#  TAB INTERAKTIF — tanpa emoji
# ─────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
tab1, tab2, tab3, tab4 = st.tabs([
    "Distribusi Risiko",
    "Per Kecamatan",
    "Tips Evakuasi",
    "Kalkulator Risiko",
])

with tab1:
    st.markdown(
        "<p style='font-size:.84rem;color:#334155;margin-bottom:18px'>"
        "Persentase luas wilayah Kota Medan berdasarkan kelas kerawanan banjir "
        "hasil pemodelan spasial multikriteria (AHP-GIS, 2024).</p>",
        unsafe_allow_html=True,
    )
    for i, (name, d) in enumerate(RISK_DISTRIBUTION.items()):
        st.markdown(f"""
        <div class='risk-bar-wrap' style='animation-delay:{i*.1}s'>
            <div class='risk-bar-label'>
                <span style='color:{d["color"]};font-weight:700'>{name}</span>
                <span style='font-family:JetBrains Mono,monospace'>{d["km2"]} km² · {d["pct"]}%</span>
            </div>
            <div class='risk-bar-track'>
                <div class='risk-bar-fill'
                     style='--bw:{d["pct"]}%;width:{d["pct"]}%;
                            background:{d["color"]};box-shadow:0 0 7px {d["color"]}55;
                            animation-delay:{i*.15}s'></div>
            </div>
        </div>""", unsafe_allow_html=True)
    st.markdown("""
    <div style='margin-top:20px;padding:13px 16px;background:rgba(56,189,248,.04);
                border:1px solid rgba(56,189,248,.1);border-radius:10px;
                font-size:.79rem;color:#334155;line-height:1.7'>
        <strong style='color:#7dd3fc'>Metodologi:</strong>
        Parameter: DEM (30%), jarak sungai (25%), curah hujan (20%), tutupan lahan (15%),
        jenis tanah (6%), kemiringan (4%). Pembobotan via Analytical Hierarchy Process (AHP).
    </div>""", unsafe_allow_html=True)

with tab2:
    st.markdown(
        "<p style='font-size:.84rem;color:#334155;margin-bottom:14px'>"
        "Tingkat kerawanan banjir per kecamatan berdasarkan indeks risiko dominan.</p>",
        unsafe_allow_html=True,
    )
    rows = "".join(
        f"<tr><td>{k}</td>"
        f"<td><span class='risk-badge' "
        f"style='background:{c}1a;color:{c};border:1px solid {c}44'>● {lv}</span></td></tr>"
        for k, lv, c in KECAMATAN_RISIKO
    )
    st.markdown(f"""
    <table class='kec-table'>
        <thead><tr><th>Kecamatan</th><th>Tingkat Risiko</th></tr></thead>
        <tbody>{rows}</tbody>
    </table>
    <p style='font-size:.71rem;color:#1e293b;margin-top:10px'>
        * Data diperbarui setiap triwulan. Sumber: BIG & BPBD Kota Medan.</p>
    """, unsafe_allow_html=True)

with tab3:
    st.markdown(
        "<p style='font-size:.84rem;color:#334155;margin-bottom:14px'>"
        "Panduan kesiapsiagaan dan evakuasi banjir untuk warga Kota Medan.</p>",
        unsafe_allow_html=True,
    )
    col_l, col_r = st.columns(2)
    for i, (key, title, body) in enumerate(EVAKUASI_TIPS):
        target = col_l if i % 2 == 0 else col_r
        with target:
            st.markdown(f"""
            <div class='tip-card' style='animation-delay:{i*.07}s'>
                <div class='tip-title'>{title}</div>
                <div class='tip-body'>{body}</div>
            </div>""", unsafe_allow_html=True)

with tab4:
    st.markdown(
        "<p style='font-size:.84rem;color:#334155;margin-bottom:16px'>"
        "Estimasi tingkat risiko banjir berdasarkan kondisi lokasi Anda.</p>",
        unsafe_allow_html=True,
    )
    ka, kb = st.columns(2)
    with ka:
        ketinggian   = st.selectbox("Ketinggian dari permukaan laut",
            ["< 5 m (sangat rendah)","5 – 15 m (rendah)","15 – 30 m (sedang)","> 30 m (tinggi)"])
        jarak_sungai = st.selectbox("Jarak dari sungai terdekat",
            ["< 100 m","100 – 500 m","500 m – 1 km","> 1 km"])
    with kb:
        tutupan  = st.selectbox("Tutupan lahan dominan",
            ["Permukiman padat","Permukiman jarang","Lahan terbuka / sawah","Hutan / RTH"])
        drainase = st.selectbox("Kondisi drainase sekitar",
            ["Buruk / sering tersumbat","Sedang","Baik","Sangat baik"])

    if st.button("Hitung Estimasi Risiko", use_container_width=True):
        skor  = 0
        skor += {"< 5 m (sangat rendah)":4,"5 – 15 m (rendah)":3,"15 – 30 m (sedang)":2,"> 30 m (tinggi)":1}[ketinggian]
        skor += {"< 100 m":4,"100 – 500 m":3,"500 m – 1 km":2,"> 1 km":1}[jarak_sungai]
        skor += {"Permukiman padat":4,"Permukiman jarang":3,"Lahan terbuka / sawah":2,"Hutan / RTH":1}[tutupan]
        skor += {"Buruk / sering tersumbat":4,"Sedang":3,"Baik":2,"Sangat baik":1}[drainase]
        if   skor <= 6:  lv,col,desc = "Risiko Rendah","#22c55e","Lokasi Anda relatif aman. Tetap waspada saat musim hujan dan jaga drainase sekitar."
        elif skor <= 9:  lv,col,desc = "Risiko Sedang","#eab308","Berpotensi terdampak saat hujan ekstrem. Siapkan tas siaga dan kenali jalur evakuasi."
        elif skor <= 12: lv,col,desc = "Risiko Tinggi","#f97316","Lokasi Anda rawan banjir. Siapkan rencana evakuasi, amankan dokumen, pantau BMKG."
        else:            lv,col,desc = "Risiko Sangat Tinggi","#ef4444","Zona merah kerawanan banjir. Koordinasikan evakuasi dengan RT/RW dan pertimbangkan relokasi sementara."
        st.markdown(f"""
        <div class='calc-result' style='background:{col}0d;border-color:{col}3a'>
            <div class='cr-level' style='color:{col}'>{lv}</div>
            <div class='cr-desc'>{desc}</div>
            <div style='margin-top:10px;font-size:.7rem;color:#1e3a5f'>
                Skor: {skor}/16 · Metode: Simple Additive Weighting (SAW)</div>
        </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────────────────────────
st.markdown("""
<div class='footer'>
    &copy; 2024 Laboratorium Pemodelan Spasial &amp; Mitigasi Bencana — BMKG / UPI Bandung<br>
    Dibangun menggunakan <strong>Streamlit</strong>,
    <strong>Leafmap</strong> &amp; <strong>Localtileserver</strong>
</div>
""", unsafe_allow_html=True)
