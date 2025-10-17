import streamlit as st
from dataclasses import dataclass
import pandas as pd

# ---------- Defaults & Constants ----------
DEFAULTS = {
    "leistungszulage_pct": 5.6,
    "urlaubsgeld_faktor": 0.7,
    "weihnachtsgeld_faktor": 0.55,
    "t_zug_a_faktor": 0.275,
    "t_zug_b": 630,
    "t_geld_faktor": 0.184,
    "abgaben_standard": 0.38,
    "abgaben_sonderzahlungen": 0.395,
}

TARIFGRUPPEN = [
    {"entgeltgruppe": "EG09", "stufe": "B", "grundentgelt": 4841, "jahr": 2025},
    {"entgeltgruppe": "EG10", "stufe": "A", "grundentgelt": 5103, "jahr": 2025},
    {"entgeltgruppe": "EG10", "stufe": "B", "grundentgelt": 5362, "jahr": 2025},
    {"entgeltgruppe": "EG11", "stufe": "A", "grundentgelt": 5528, "jahr": 2025},
    {"entgeltgruppe": "EG09", "stufe": "B", "grundentgelt": 4991, "jahr": 2026},
    {"entgeltgruppe": "EG10", "stufe": "A", "grundentgelt": 5261, "jahr": 2026},
    {"entgeltgruppe": "EG10", "stufe": "B", "grundentgelt": 5528, "jahr": 2026},
    {"entgeltgruppe": "EG11", "stufe": "A", "grundentgelt": 5792, "jahr": 2026},
]


# ---------- Data structures ----------
@dataclass
class TarifInfo:
    entgeltgruppe: str
    grundentgelt: float
    jahr: int
    stufe: str
    leistungszulage_pct: float = DEFAULTS["leistungszulage_pct"]
    urlaubsgeld_faktor: float = DEFAULTS["urlaubsgeld_faktor"]
    weihnachtsgeld_faktor: float = DEFAULTS["weihnachtsgeld_faktor"]
    t_zug_a_faktor: float = DEFAULTS["t_zug_a_faktor"]
    t_zug_b: float = DEFAULTS["t_zug_b"]
    t_geld_faktor: float = DEFAULTS["t_geld_faktor"]
    t_geld_aktiv: bool = False
    abgaben_standard: float = DEFAULTS["abgaben_standard"]
    abgaben_sonderzahlungen: float = DEFAULTS["abgaben_sonderzahlungen"]


# ---------- Helper functions ----------
def berechne_jahresgehalt(info: TarifInfo) -> dict:
    leistungszulage_amount = info.grundentgelt * (info.leistungszulage_pct / 100)
    grundgehalt = info.grundentgelt + leistungszulage_amount
    urlaubsgeld = info.urlaubsgeld_faktor * grundgehalt
    weihnachtsgeld = info.weihnachtsgeld_faktor * grundgehalt
    t_zug_a = info.t_zug_a_faktor * grundgehalt
    t_zug_b = info.t_zug_b
    t_geld = info.t_geld_faktor * grundgehalt if info.t_geld_aktiv else 0

    jahresgrundgehalt = grundgehalt * 12
    jahressonderzahlungen = urlaubsgeld + weihnachtsgeld + t_zug_a + t_zug_b + t_geld
    jahresbrutto = jahresgrundgehalt + jahressonderzahlungen

    nettogrundgehalt = jahresgrundgehalt * (1 - info.abgaben_standard)
    netto_sonder = jahressonderzahlungen * (1 - info.abgaben_sonderzahlungen)
    jahresnetto = nettogrundgehalt + netto_sonder
    durchschnittsmonatsnetto = jahresnetto / 12

    return {
        "Entgeltgruppe": info.entgeltgruppe,
        "Stufe": info.stufe,
        "Jahr": info.jahr,
        "Grundgehalt": round(grundgehalt),
        "Leistungszulage": round(leistungszulage_amount),
        "Urlaubsgeld": round(urlaubsgeld),
        "Weihnachtsgeld": round(weihnachtsgeld),
        "T-ZUG A": round(t_zug_a),
        "T-ZUG B": round(t_zug_b),
        "T-Geld": round(t_geld),
        "Jahresbruttogehalt": round(jahresbrutto),
        "Nettojahresgehalt": round(jahresnetto),
        "Ø Monatsnetto": round(durchschnittsmonatsnetto),
    }


def build_index_label(entgeltgruppe: str, stufe: str, jahr: int, lz_pct: float) -> str:
    return f"{entgeltgruppe} {stufe} {jahr} {lz_pct:.2f}%"


def compute_comparison_df(jahr: int, leistungszulage_pct: float, t_geld_aktiv: bool) -> pd.DataFrame:
    rows = []
    for tg in TARIFGRUPPEN:
        if tg["jahr"] != jahr:
            continue
        defaults = DEFAULTS.copy()
        defaults["leistungszulage_pct"] = leistungszulage_pct
        defaults["t_geld_aktiv"] = t_geld_aktiv
        info = TarifInfo(**defaults, **tg)
        res = berechne_jahresgehalt(info)
        res["Leistungszulage_pct"] = float(defaults["leistungszulage_pct"])
        rows.append(res)

    df = pd.DataFrame(rows)
    df["Index"] = df.apply(lambda r: build_index_label(r["Entgeltgruppe"], r["Stufe"], r["Jahr"], r["Leistungszulage_pct"]), axis=1)
    df = df.set_index("Index")
    return df


def format_diff_table(df: pd.DataFrame, selected_index: str, cols=None) -> pd.io.formats.style.Styler:
    if cols is None:
        cols = ["Jahresbruttogehalt", "Nettojahresgehalt", "Ø Monatsnetto"]

    base = df.loc[selected_index, cols].astype(float)

    nums = df[cols].copy()
    display_nums = nums.copy()
    for idx in nums.index:
        if idx == selected_index:
            display_nums.loc[idx] = nums.loc[idx].astype(int)
        else:
            display_nums.loc[idx] = (nums.loc[idx] - base).astype(int)

    # build formatted strings (object dtype)
    formatted = pd.DataFrame(index=display_nums.index, columns=display_nums.columns, dtype=object)
    for idx in display_nums.index:
        is_sel = (idx == selected_index)
        for col in display_nums.columns:
            v = int(display_nums.at[idx, col])
            formatted.at[idx, col] = f"{v}" if is_sel else (f"+{v}" if v > 0 else f"{v}")

    # styling
    styles = pd.DataFrame("", index=formatted.index, columns=formatted.columns, dtype=object)
    for r_pos, idx in enumerate(formatted.index):
        is_sel = (idx == selected_index)
        for c_pos, col in enumerate(formatted.columns):
            if is_sel:
                styles.iat[r_pos, c_pos] = "color: black"
            else:
                vv = int(display_nums.iat[r_pos, c_pos])
                styles.iat[r_pos, c_pos] = "color: green" if vv > 0 else ("color: red" if vv < 0 else "")

    styler = formatted.style
    styler = styler.apply(lambda _: styles, axis=None)
    return styler


def build_two_row_styler(me_res: dict, cmp_res: dict, me_lz: float, cmp_lz: float) -> pd.io.formats.style.Styler:
    cols = ["Jahresbruttogehalt", "Nettojahresgehalt", "Ø Monatsnetto"]
    my_index = build_index_label(me_res["Entgeltgruppe"], me_res["Stufe"], me_res["Jahr"], me_lz)
    cmp_index = build_index_label(cmp_res["Entgeltgruppe"], cmp_res["Stufe"], cmp_res["Jahr"], cmp_lz)

    my_vals = [int(me_res[c]) for c in cols]
    cmp_vals = [int(cmp_res[c]) for c in cols]
    diff_vals = [cmp_vals[i] - my_vals[i] for i in range(len(cols))]

    # ensure unique index
    if cmp_index == my_index:
        cmp_index = cmp_index + " (cmp)"

    df = pd.DataFrame([my_vals, diff_vals], index=[my_index, cmp_index], columns=cols)

    # format and style similar to format_diff_table
    formatted = pd.DataFrame(index=df.index, columns=df.columns, dtype=object)
    for idx in df.index:
        is_my = idx == my_index
        for col in df.columns:
            v = int(df.at[idx, col])
            formatted.at[idx, col] = f"{v}" if is_my else (f"+{v}" if v > 0 else f"{v}")

    styles = pd.DataFrame("", index=formatted.index, columns=formatted.columns, dtype=object)
    for r_pos, idx in enumerate(formatted.index):
        is_my = idx == my_index
        for c_pos, col in enumerate(formatted.columns):
            if is_my:
                styles.iat[r_pos, c_pos] = "color: black; font-weight: normal"
            else:
                vv = int(df.iat[r_pos, c_pos])
                styles.iat[r_pos, c_pos] = "color: green" if vv > 0 else ("color: red" if vv < 0 else "")

    styler = formatted.style
    styler = styler.apply(lambda _: styles, axis=None)
    return styler


# ---------- UI ----------
st.title("IG Metall Gehaltsrechner Bayern")
st.subheader("Meine Tarifgruppe")

# Inputs
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    jahr = st.selectbox("Jahr", sorted({tg["jahr"] for tg in TARIFGRUPPEN}))
with col2:
    entgeltgruppe = st.selectbox("Entgeltgruppe", sorted({tg["entgeltgruppe"] for tg in TARIFGRUPPEN if tg["jahr"] == jahr}))
with col3:
    stufe = st.selectbox("Stufe", sorted({tg["stufe"] for tg in TARIFGRUPPEN if tg["jahr"] == jahr and tg["entgeltgruppe"] == entgeltgruppe}))
with col4:
    leistungszulage_pct = st.number_input("Leistungszulage (%)", value=DEFAULTS.get("leistungszulage_pct", 5.6), min_value=0.0, max_value=100.0, step=0.1, format="%.1f")
with col5:
    t_geld_aktiv = st.checkbox("T-Geld aktiv?", value=False)

# Compute user's result
defaults_copy = DEFAULTS.copy()
defaults_copy["t_geld_aktiv"] = t_geld_aktiv
defaults_copy["leistungszulage_pct"] = leistungszulage_pct
auswahl = next(tg for tg in TARIFGRUPPEN if tg["jahr"] == jahr and tg["entgeltgruppe"] == entgeltgruppe and tg["stufe"] == stufe)
meine_info = TarifInfo(**defaults_copy, **auswahl)
meine_ergebnis = berechne_jahresgehalt(meine_info)

# Components table
st.subheader("Gehaltskomponenten meiner Tarifgruppe")
meine_index_label = build_index_label(meine_ergebnis["Entgeltgruppe"], meine_ergebnis["Stufe"], meine_ergebnis["Jahr"], leistungszulage_pct)
st.write(pd.DataFrame([
    {
        "Grundgehalt": meine_ergebnis["Grundgehalt"],
        "Leistungszulage": meine_ergebnis.get("Leistungszulage", 0),
        "Urlaubsgeld": meine_ergebnis["Urlaubsgeld"],
        "Weihnachtsgeld": meine_ergebnis["Weihnachtsgeld"],
        "T-ZUG A": meine_ergebnis["T-ZUG A"],
        "T-ZUG B": meine_ergebnis["T-ZUG B"],
        "T-Geld": meine_ergebnis["T-Geld"],
    }
], index=[meine_index_label]))

# Comparison: all groups same year
st.subheader("Vergleich mit allen Tarifgruppen desselben Jahres")
vergleich_df = compute_comparison_df(jahr, leistungszulage_pct, t_geld_aktiv)
selected_index = build_index_label(meine_ergebnis["Entgeltgruppe"], meine_ergebnis["Stufe"], meine_ergebnis["Jahr"], leistungszulage_pct)
try:
    styled_all = format_diff_table(vergleich_df, selected_index)
    st.table(styled_all)
except KeyError:
    st.error("Ausgewählte Gruppe nicht in der Vergleichstabelle gefunden.")

# Comparison: specific group
st.subheader("Vergleich mit bestimmter Tarifgruppe")
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    jahr_cmp = st.selectbox("Jahr", sorted({tg["jahr"] for tg in TARIFGRUPPEN}), index=0, key="jahr_cmp")
with col2:
    entgeltgruppe_cmp = st.selectbox("Entgeltgruppe", sorted({tg["entgeltgruppe"] for tg in TARIFGRUPPEN if tg["jahr"] == jahr_cmp}), key="eg_cmp")
with col3:
    stufe_cmp = st.selectbox("Stufe (Vergleich)", sorted({tg["stufe"] for tg in TARIFGRUPPEN if tg["jahr"] == jahr_cmp and tg["entgeltgruppe"] == entgeltgruppe_cmp}), key="st_cmp")
with col4:
    leistungszulage_pct_cmp = st.number_input("Leistungszulage (%)", value=leistungszulage_pct, min_value=0.0, max_value=100.0, step=0.1, format="%.1f", key="lz_cmp")
with col5:
    t_geld_aktiv_cmp = st.checkbox("T-Geld aktiv?", value=t_geld_aktiv, key="t_geld_cmp")

auswahl_cmp = next(tg for tg in TARIFGRUPPEN if tg["jahr"] == jahr_cmp and tg["entgeltgruppe"] == entgeltgruppe_cmp and tg["stufe"] == stufe_cmp)
cmp_defaults = DEFAULTS.copy()
cmp_defaults["leistungszulage_pct"] = leistungszulage_pct_cmp
cmp_defaults["t_geld_aktiv"] = t_geld_aktiv_cmp
cmp_info = TarifInfo(**cmp_defaults, **auswahl_cmp)
cmp_res = berechne_jahresgehalt(cmp_info)

styler_cmp = build_two_row_styler(meine_ergebnis, cmp_res, leistungszulage_pct, leistungszulage_pct_cmp)
st.table(styler_cmp)

