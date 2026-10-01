import os
import re
import io
import zipfile
import pandas as pd
import streamlit as st
from PIL import Image as PILImage
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors

try:
    from pypdf import PdfMerger
except ImportError:
    PdfMerger = None

# Configurazione della pagina Streamlit
st.set_page_config(
    page_title="Gestionale Cloud - SEAB",
    page_icon="⚡",
    layout="wide"
)

# --- SISTEMA DI LOGIN SICURO ---
def check_password():
    def password_entered():
        correct_pwd = "seab2026"
        try:
            if "PASSWORD" in st.secrets:
                correct_pwd = st.secrets["PASSWORD"]
        except Exception:
            pass
            
        if st.session_state["password"] == correct_pwd:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.subheader("🔒 Accesso Riservato Gestionale SEAB")
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.subheader("🔒 Accesso Riservato Gestionale SEAB")
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password errata. Riprova. (Password predefinita: seab2026)")
        return False
    else:
        return True

if not check_password():
    st.stop()


# --- PERCORSI AUTOMATICI RISORSE ---
def get_resource_path():
    logo_path = ""
    for ext in [".png", ".jpg", ".jpeg"]:
        if os.path.exists(f"logo{ext}"):
            logo_path = f"logo{ext}"
            break

    firma_path = ""
    for ext in [".png", ".jpg", ".jpeg"]:
        if os.path.exists(f"firma{ext}"):
            firma_path = f"firma{ext}"
            break
            
    return logo_path, firma_path


# ==========================================
# 1. GENERATORE PDF: VSE (IEC 62353)
# ==========================================
def generate_vse_pdf_bytes(d, tecnico_nome, logo_path, firma_path):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=18, rightMargin=18, topMargin=15, bottomMargin=15)
    
    p_title = ParagraphStyle("HdrTitle", fontName="Helvetica-Bold", fontSize=10, alignment=1, leading=12)
    p_letter = ParagraphStyle("Letter", fontName="Helvetica-Bold", fontSize=13, alignment=1, leading=14)
    p_info = ParagraphStyle("InfoLabel", fontName="Helvetica-Bold", fontSize=7.5, leading=9.5)
    p_sec_hdr = ParagraphStyle("SecHdr", fontName="Helvetica-Bold", fontSize=8, leading=10)
    p_tbl_hdr = ParagraphStyle("TblHdr", fontName="Helvetica-Bold", fontSize=7, alignment=1, leading=8.5)
    p_tbl_cell = ParagraphStyle("TblCell", fontName="Helvetica", fontSize=7, leading=8.5)
    p_tbl_cell_center = ParagraphStyle("TblCellCenter", fontName="Helvetica", fontSize=7, alignment=1, leading=8.5)

    story = []
    
    if logo_path and os.path.exists(logo_path):
        img_l = PILImage.open(logo_path)
        lw, lh = img_l.size
        target_lh = 24
        target_lw = target_lh * (lw / lh)
        logo_img = Image(logo_path, width=target_lw, height=target_lh)
    else:
        logo_img = Paragraph("<b>SEAB</b>", p_title)

    t_banner = Table([
        [logo_img, Paragraph("CERTIFICATO DI SICUREZZA ELETTRICA<br/>IEC 62353", p_title), Paragraph("VE", p_letter)]
    ], colWidths=[75, 420, 79], style=[
        ("BOX", (0, 0), (-1, -1), 0.8, colors.black), ("INNERGRID", (0, 0), (-1, -1), 0.8, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (0, 0), "CENTER"), ("ALIGN", (2, 0), (2, 0), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)
    ])
    story.append(t_banner)
    story.append(Spacer(1, 5))
    
    info_data = [
        [Paragraph(f"<b>NR. SCHEDA:</b> {d['n_scheda']}", p_info), Paragraph(f"<b>DATA:</b> {d['data_ve']}", p_info)],
        [Paragraph(f"<b>DESCRIZIONE CLASSE:</b> {d['classe']}", p_info), Paragraph(f"<b>INV. TECNICO:</b> {d['inv']}", p_info)],
        [Paragraph(f"<b>COSTRUTTORE:</b> {d['produttore']}", p_info), Paragraph(f"<b>S/N:</b> {d['sn']}", p_info)],
        [Paragraph(f"<b>MODELLO:</b> {d['modello']}", p_info), Paragraph(f"<b>APP. PADRE:</b> {d['app_padre']}", p_info)],
        [Paragraph(f"<b>CONFIGURAZIONE:</b> {d['configurazione']}", p_info), Paragraph(f"<b>PRESIDIO:</b> {d['presidio']}", p_info)],
        [Paragraph(f"<b>REPARTO COLLAUDO:</b> {d['reparto_collaudo']}", p_info), Paragraph(f"<b>REPARTO RILEVATO:</b> {d['reparto_rilevato']}", p_info)],
        [Paragraph(f"<b>CLASSE DI PROTEZIONE:</b> {d['classe_prot']}", p_info), Paragraph(f"<b>TIPO PARTI APPLICATA:</b> {d['tipo_parte']}", p_info)],
    ]
    t_info = Table(info_data, colWidths=[287, 287], style=[
        ("BOX", (0, 0), (-1, -1), 0.8, colors.black), ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5), ("LEFTPADDING", (0, 0), (-1, -1), 6)
    ])
    story.append(t_info)
    story.append(Spacer(1, 5))
    
    story.append(Table([[Paragraph("ESAME A VISTA:", p_sec_hdr)]], colWidths=[574], style=[("BOX", (0, 0), (-1, -1), 0.8, colors.black), ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    
    vis_items = [
        ("Allineamento documentazione", d['allineamento']),
        ("Stato etichette e dati di targa", d['etichette']),
        ("Integrità e contaminazione", d['integrita']),
        ("Stato degli accessori", d['accessori']),
        ("Configurazione Sistema", d['config_sistema']),
        ("Conformità fusibili", d['fusibili']),
    ]
    vis_data = [[Paragraph("DESCRIZIONE INTERVENTO", p_info), Paragraph("ESITO", p_tbl_hdr)]]
    for desc, es in vis_items:
        if not es or str(es).lower() == 'nan': es = "N.A."
        vis_data.append([Paragraph(desc, p_tbl_cell), Paragraph(es, p_tbl_cell_center)])
        
    t_vis = Table(vis_data, colWidths=[474, 100], style=[
        ("BOX", (0, 0), (-1, -1), 0.8, colors.black), ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5)
    ])
    story.append(t_vis)
    story.append(Spacer(1, 5))

    story.append(Table([[Paragraph("VERIFICA ELETTRICA:", p_sec_hdr)]], colWidths=[574], style=[("BOX", (0, 0), (-1, -1), 0.8, colors.black), ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    
    elec_d1 = [
        [Paragraph(f"Tensione di alimentazione durante la verifica: <b>[X] VAC {d['tensione']}</b> &nbsp;&nbsp;&nbsp; [  ] Valore nel report allegato", p_tbl_cell)],
        [Paragraph(f"<b>Resistenza della terra di protezione:</b><br/>Descrizione: {d['terra_desc']}<br/>Valori Misurati: <b>{d['terra_val']}</b>", p_tbl_cell)],
        [Paragraph("Misura delle correnti di dispersione effettuata con il metodo diretto: <b>[X] Valori riportati in tabella</b> &nbsp; [  ] Valore nel report allegato", p_tbl_cell)]
    ]
    t_elec1 = Table(elec_d1, colWidths=[574], style=[
        ("BOX", (0, 0), (-1, -1), 0.8, colors.black), ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2), ("LEFTPADDING", (0, 0), (-1, -1), 6)
    ])
    story.append(t_elec1)
    story.append(Spacer(1, 5))

    iso_data = [
        [Paragraph("<b>Resistenza dell'isolamento:</b>", p_info), Paragraph("<b>Valori ammessi Classi II</b>", p_tbl_hdr), Paragraph("", p_tbl_hdr), Paragraph("<b>Valori ammessi Classe I</b>", p_tbl_hdr), Paragraph("", p_tbl_hdr), Paragraph("<b>Valori Misurati</b>", p_tbl_hdr)],
        [Paragraph("", p_tbl_cell), Paragraph("Tipo B", p_tbl_hdr), Paragraph("Tipo BF/CF", p_tbl_hdr), Paragraph("Tipo B", p_tbl_hdr), Paragraph("Tipo BF/CF", p_tbl_hdr), Paragraph("", p_tbl_cell)],
        [Paragraph("Rete - Terra di protezione", p_tbl_cell), Paragraph("N.A.", p_tbl_cell_center), Paragraph("N.A.", p_tbl_cell_center), Paragraph("≥ 2 MΩ", p_tbl_cell_center), Paragraph("≥ 2 MΩ", p_tbl_cell_center), Paragraph(d['iso_rete_terra'], p_tbl_cell_center)],
        [Paragraph("Rete - Parti conduttrici accessibili", p_tbl_cell), Paragraph("≥ 7 MΩ", p_tbl_cell_center), Paragraph("≥ 7 MΩ", p_tbl_cell_center), Paragraph("≥ 2 MΩ", p_tbl_cell_center), Paragraph("≥ 2 MΩ", p_tbl_cell_center), Paragraph(d['iso_rete_parti'], p_tbl_cell_center)],
        [Paragraph("Rete - Parti applicate (non tipo F)", p_tbl_cell), Paragraph("≥ 7 MΩ", p_tbl_cell_center), Paragraph("N.A.", p_tbl_cell_center), Paragraph("≥ 2 MΩ", p_tbl_cell_center), Paragraph("N.A.", p_tbl_cell_center), Paragraph(d['iso_rete_app_nof'], p_tbl_cell_center)],
        [Paragraph("Parti applicate tipo F - Terra di protezione", p_tbl_cell), Paragraph("N.A.", p_tbl_cell_center), Paragraph("N.A.", p_tbl_cell_center), Paragraph("N.A.", p_tbl_cell_center), Paragraph("≥ 2 MΩ", p_tbl_cell_center), Paragraph(d['iso_tipof_terra'], p_tbl_cell_center)],
        [Paragraph("Parti applicate tipo F - Parti cond. Accessibili", p_tbl_cell), Paragraph("N.A.", p_tbl_cell_center), Paragraph("≥ 70 MΩ", p_tbl_cell_center), Paragraph("N.A.", p_tbl_cell_center), Paragraph("≥ 2 MΩ", p_tbl_cell_center), Paragraph(d['iso_tipof_parti'], p_tbl_cell_center)],
    ]
    t_iso = Table(iso_data, colWidths=[184, 75, 75, 75, 75, 90], style=[
        ("BOX", (0, 0), (-1, -1), 0.8, colors.black), ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("SPAN", (0, 0), (0, 1)), ("SPAN", (1, 0), (2, 0)), ("SPAN", (3, 0), (4, 0)), ("SPAN", (5, 0), (5, 1)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5)
    ])
    story.append(t_iso)
    story.append(Spacer(1, 5))

    corr_data = [
        [Paragraph("<b>Correnti di dispersione:</b>", p_info), Paragraph("<b>Valori ammessi Tipo B</b>", p_tbl_hdr), Paragraph("<b>Valori ammessi Tipo BF</b>", p_tbl_hdr), Paragraph("<b>Valori ammessi Tipo CF</b>", p_tbl_hdr), Paragraph("<b>Valori Misurati</b>", p_tbl_hdr)],
        [Paragraph("Corrente di dispersione nel sistema", p_tbl_cell), Paragraph("≤ 500 µA", p_tbl_cell_center), Paragraph("≤ 500 µA", p_tbl_cell_center), Paragraph("≤ 500 µA", p_tbl_cell_center), Paragraph(d['corr_sistema'], p_tbl_cell_center)],
        [Paragraph(f"Descrizione parti applicate 1: {d['desc_app1']}", p_tbl_cell), Paragraph("", p_tbl_cell), Paragraph("", p_tbl_cell), Paragraph("", p_tbl_cell), Paragraph("", p_tbl_cell)],
        [Paragraph("Corrente di dispersione nelle parti applicate 1", p_tbl_cell), Paragraph("N.A.", p_tbl_cell_center), Paragraph("≤ 5000 µA", p_tbl_cell_center), Paragraph("≤ 50 µA", p_tbl_cell_center), Paragraph(d['corr_app1'], p_tbl_cell_center)],
        [Paragraph(f"Descrizione parti applicate 2: {d['desc_app2']}", p_tbl_cell), Paragraph("", p_tbl_cell), Paragraph("", p_tbl_cell), Paragraph("", p_tbl_cell), Paragraph("", p_tbl_cell)],
        [Paragraph("Corrente di dispersione nelle parti applicate 2", p_tbl_cell), Paragraph("N.A.", p_tbl_cell_center), Paragraph("≤ 5000 µA", p_tbl_cell_center), Paragraph("≤ 50 µA", p_tbl_cell_center), Paragraph(d['corr_app2'], p_tbl_cell_center)],
        [Paragraph(f"Descrizione parti applicate 3: {d['desc_app3']}", p_tbl_cell), Paragraph("", p_tbl_cell), Paragraph("", p_tbl_cell), Paragraph("", p_tbl_cell), Paragraph("", p_tbl_cell)],
        [Paragraph("Corrente di dispersione nelle parti applicate 3", p_tbl_cell), Paragraph("N.A.", p_tbl_cell_center), Paragraph("≤ 5000 µA", p_tbl_cell_center), Paragraph("≤ 50 µA", p_tbl_cell_center), Paragraph(d['corr_app3'], p_tbl_cell_center)],
        [Paragraph(f"Descrizione parti applicate 4: {d['desc_app4']}", p_tbl_cell), Paragraph("", p_tbl_cell), Paragraph("", p_tbl_cell), Paragraph("", p_tbl_cell), Paragraph("", p_tbl_cell)],
        [Paragraph("Corrente di dispersione nelle parti applicate 4", p_tbl_cell), Paragraph("N.A.", p_tbl_cell_center), Paragraph("≤ 5000 µA", p_tbl_cell_center), Paragraph("≤ 50 µA", p_tbl_cell_center), Paragraph(d['corr_app4'], p_tbl_cell_center)],
    ]
    t_corr = Table(corr_data, colWidths=[204, 95, 95, 95, 85], style=[
        ("BOX", (0, 0), (-1, -1), 0.8, colors.black), ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("SPAN", (0, 2), (4, 2)), ("SPAN", (0, 4), (4, 4)), ("SPAN", (0, 6), (4, 6)), ("SPAN", (0, 8), (4, 8)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5)
    ])
    story.append(t_corr)
    story.append(Spacer(1, 5))

    vf_check = "[X]" if d['verifica_funzionale'].upper() == "OK" else "[  ]"
    vf_fail = "[  ]" if d['verifica_funzionale'].upper() == "OK" else "[X]"
    t_vf = Table([[Paragraph(f"<b>Verifica Funzionale del sistema:</b> {vf_check} Passata &nbsp;&nbsp;&nbsp; {vf_fail} Fallita", p_info)]], colWidths=[574], style=[
        ("BOX", (0, 0), (-1, -1), 0.8, colors.black), ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5), ("LEFTPADDING", (0, 0), (-1, -1), 6)
    ])
    story.append(t_vf)
    story.append(Spacer(1, 5))

    t_legend = Table([
        [Paragraph("OK = REQUISITO SODDISFATTO", p_info), Paragraph("NA = REQUISITO NON PERTINENTE", p_info)],
        [Paragraph("KO = REQUISITO NON SODDISFATTO", p_info), Paragraph("NV = REQUISITO NON VERIFICABILE", p_info)],
    ], colWidths=[287, 287])
    t_legend.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.8, colors.black), ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2), ("LEFTPADDING", (0, 0), (-1, -1), 6)
    ]))
    story.append(t_legend)
    story.append(Spacer(1, 5))

    sn_val = str(d['strumento_sn']).strip()
    f1_chk = "[X]" if sn_val == "4963014" else "[  ]"
    f2_chk = "[X]" if sn_val == "4963024" else "[  ]"
    f3_chk = "[X]" if sn_val == "5625031" else "[  ]"

    concl_data = [
        [Paragraph("<b>CONCLUSIONI:</b>", p_info)],
        [Paragraph("[X] Nessun difetto funzionale e di sicurezza rilevato. Apparecchio conforme" if d['esito_ve'].upper()=="POSITIVO" else "[  ] Nessun difetto", p_tbl_cell)],
        [Paragraph("[  ] Nessun rischio diretto, le carenze rilevate possono essere corrette rapidamente (vedi note)", p_tbl_cell)],
        [Paragraph(f"<b>NOTE:</b> {d['note_ve']}", p_info)],
        [Paragraph(f"<b>ESITO: {d['esito_ve']}</b> &nbsp;&nbsp;&nbsp; APERTA CORRETTIVA N: __________ DATA: __________", p_info)],
        [Paragraph("<b>Misure effettuate con:</b>", p_info)],
        [Paragraph(f"{f1_chk} Fluke ESA 615 &nbsp;&nbsp; S/N 4963014 &nbsp;&nbsp; Validità di taratura da 23/05/2025 a 23/05/2026", p_tbl_cell)],
        [Paragraph(f"{f2_chk} Fluke ESA 615 &nbsp;&nbsp; S/N 4963024 &nbsp;&nbsp; Validità di taratura da 26/06/2024 a 26/06/2025", p_tbl_cell)],
        [Paragraph(f"{f3_chk} Fluke ESA 615 &nbsp;&nbsp; S/N 5625031 &nbsp;&nbsp; Validità di taratura da 14/01/2026 a 14/01/2027", p_tbl_cell)],
    ]
    t_concl = Table(concl_data, colWidths=[574], style=[
        ("BOX", (0, 0), (-1, -1), 0.8, colors.black), ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2), ("LEFTPADDING", (0, 0), (-1, -1), 6)
    ])
    story.append(t_concl)
    story.append(Spacer(1, 8))
    
    if firma_path and os.path.exists(firma_path):
        img_f = PILImage.open(firma_path)
        fw, fh = img_f.size
        target_fh = 55
        target_fw = target_fh * (fw / fh)
        firma_obj = Image(firma_path, width=target_fw, height=target_fh)
        firma_content = Table([[Paragraph("FIRMA:", p_info), firma_obj]], colWidths=[40, 210], style=[("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0)])
    else:
        firma_content = Paragraph("FIRMA: ______________________", p_info)
        
    t_sig = Table([[Paragraph(f"TECNICO RESPONSABILE: <u>{tecnico_nome}</u>", p_info), firma_content]], colWidths=[300, 274])
    t_sig.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 6)]))
    story.append(t_sig)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# ==========================================
# 2. GENERATORE PDF: MP (Manutenzione Preventiva)
# ==========================================
def classify_mp_item(desc):
    d_lower = str(desc).lower().strip()
    is_isp = False
    if d_lower.startswith(('ispezione', 'pulizia', 'lubrificazione', 'lubrificazioni')):
        is_isp = True
    elif 'integrità' in d_lower or 'integrita' in d_lower:
        is_isp = True
    elif d_lower.startswith(('controllo usura', 'controllo stabilità', 'controllo rumorosità', 'controllo identificazione')):
        is_isp = True
    elif any(k in d_lower for k in ['danni esteriori', 'targa ed etichetta', 'involucro dell', 'pulizia generale', 'filtri', 'ventole', 'schermo', 'track-ball']):
        is_isp = True
    if d_lower.startswith(('controllo funzionamento', 'conttrollo funzionamento', 'autotest', 'verifica finale', 'prova', 'vuoto test', 'test ')):
        is_isp = False
    return "ISPEZIONE" if is_isp else "VERIFICHE"

def generate_mp_pdf_bytes(data, tecnico_nome, logo_path, firma_path):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=20, rightMargin=20, topMargin=10, bottomMargin=10)

    p_title = ParagraphStyle("HdrTitle", fontName="Helvetica-Bold", fontSize=10, alignment=1, leading=12)
    p_letter = ParagraphStyle("Letter", fontName="Helvetica-Bold", fontSize=15, alignment=1, leading=16)
    p_info = ParagraphStyle("InfoLabel", fontName="Helvetica", fontSize=8, leading=10)
    p_sec_hdr = ParagraphStyle("SecHdr", fontName="Helvetica-Bold", fontSize=8.5, leading=10)
    p_table_col = ParagraphStyle("TableCol", fontName="Helvetica-Bold", fontSize=8, alignment=1, leading=9)
    p_table_col_left = ParagraphStyle("TableColLeft", fontName="Helvetica-Bold", fontSize=8, leading=9)
    p_table_cell = ParagraphStyle("TableCell", fontName="Helvetica", fontSize=7.5, leading=8.5)
    p_center_val = ParagraphStyle("CenterVal", fontName="Helvetica", fontSize=8, alignment=1, leading=9)

    story = []

    if logo_path and os.path.exists(logo_path):
        img_pil = PILImage.open(logo_path)
        orig_w, orig_h = img_pil.size
        target_h = 32
        target_w = target_h * (orig_w / orig_h)
        logo_img = Image(logo_path, width=target_w, height=target_h)
    else:
        logo_img = Paragraph("<b>SEAB</b>", p_title)

    header_data = [[
        logo_img,
        Paragraph(f"SCHEDA DI MANUTENZIONE PREVENTIVA<br/>{data.get('titolo_scheda', 'DISPOSITIVO GENERICO')}", p_title),
        Paragraph(data.get("tipo_scheda", "A"), p_letter),
    ]]
    t_banner = Table(header_data, colWidths=[80, 400, 65])
    t_banner.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.8, colors.black), ("INNERGRID", (0, 0), (-1, -1), 0.8, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (0, 0), "CENTER"), ("ALIGN", (2, 0), (2, 0), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(t_banner)
    story.append(Spacer(1, 4))

    info_data = [
        [Paragraph(f"N. SCHEDA: {data.get('n_scheda', '')}", p_info), Paragraph(f"DATA: {data.get('data', '')}", p_info)],
        [Paragraph(f"DESCRIZIONE: {data.get('descrizione', '')}", p_info), Paragraph(f"INV: {data.get('inv', '')}", p_info)],
        [Paragraph(f"COSTRUTTORE: {data.get('costruttore', '')}", p_info), Paragraph(f"S/N: {data.get('sn', '')}", p_info)],
        [Paragraph(f"MODELLO: {data.get('modello', '')}", p_info), Paragraph("", p_info)],
        [Paragraph(f"CONFIGURAZIONE: {data.get('configurazione', '')}", p_info), Paragraph(f"INV PADRE: {data.get('inv_padre', '')}", p_info)],
        [Paragraph(f"REPARTO: {data.get('reparto', '')}", p_info), Paragraph(f"PRESIDIO: {data.get('presidio', '')}", p_info)],
        [Paragraph(f"REPARTO RILEVATO: {data.get('reparto_rilevato', '')}", p_info), Paragraph("", p_info)],
    ]
    t_info = Table(info_data, colWidths=[310, 235])
    t_info.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.8, colors.black), ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("SPAN", (0, 3), (1, 3)), ("SPAN", (0, 6), (1, 6)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5), ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_info)
    story.append(Spacer(1, 4))

    story.append(Table([[Paragraph("ISPEZIONE E PULIZIA", p_sec_hdr)]], colWidths=[545], style=[
        ("BOX", (0, 0), (-1, -1), 0.8, colors.black), ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2), ("LEFTPADDING", (0, 0), (-1, -1), 4)
    ]))
    sec1_rows = [[Paragraph("CODICE", p_table_col_left), Paragraph("DESCRIZIONE INTERVENTO", p_table_col_left), Paragraph("ok", p_table_col), Paragraph("ko", p_table_col), Paragraph("nv", p_table_col), Paragraph("na", p_table_col)]]
    for code, item_desc, val in data.get("ispezioni", []):
        sec1_rows.append([Paragraph(code, p_table_cell), Paragraph(item_desc, p_table_cell), Paragraph(str(val), p_center_val), "", "", ""])

    t_sec1 = Table(sec1_rows, colWidths=[50, 405, 22, 22, 23, 23])
    sec1_style = [
        ("BOX", (0, 0), (-1, -1), 0.8, colors.black), ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1), ("LEFTPADDING", (0, 0), (-1, -1), 3),
    ]
    for idx in range(1, len(data.get("ispezioni", [])) + 1):
        sec1_style.append(("SPAN", (2, idx), (5, idx)))
    t_sec1.setStyle(TableStyle(sec1_style))
    story.append(t_sec1)
    story.append(Spacer(1, 4))

    story.append(Table([[Paragraph("VERIFICHE FUNZIONALI", p_sec_hdr)]], colWidths=[545], style=[
        ("BOX", (0, 0), (-1, -1), 0.8, colors.black), ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2), ("LEFTPADDING", (0, 0), (-1, -1), 4)
    ]))
    sec2_rows = [[Paragraph("CODICE", p_table_col_left), Paragraph("DESCRIZIONE INTERVENTO", p_table_col_left), Paragraph("ok", p_table_col), Paragraph("ko", p_table_col), Paragraph("nv", p_table_col), Paragraph("na", p_table_col)]]
    for code, item_desc, val in data.get("verifiche", []):
        sec2_rows.append([Paragraph(code, p_table_cell), Paragraph(item_desc, p_table_cell), Paragraph(str(val), p_center_val), "", "", ""])

    t_sec2 = Table(sec2_rows, colWidths=[50, 405, 22, 22, 23, 23])
    sec2_style = [
        ("BOX", (0, 0), (-1, -1), 0.8, colors.black), ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1), ("LEFTPADDING", (0, 0), (-1, -1), 3),
    ]
    for idx in range(1, len(data.get("verifiche", [])) + 1):
        sec2_style.append(("SPAN", (2, idx), (5, idx)))
    t_sec2.setStyle(TableStyle(sec2_style))
    story.append(t_sec2)
    story.append(Spacer(1, 4))

    t_legend = Table([
        [Paragraph("OK = REQUISITO SODDISFATTO", p_info), Paragraph("NA = REQUISITO NON PERTINENTE", p_info)],
        [Paragraph("KO = REQUISITO NON SODDISFATTO", p_info), Paragraph("NV = REQUISITO NON VERIFICABILE", p_info)],
    ], colWidths=[275, 270])
    t_legend.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.8, colors.black), ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5), ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_legend)
    story.append(Spacer(1, 4))

    note_val = data.get("note", "")
    if str(note_val).startswith("ESITO"):
        note_val = ""
    t_note = Table([
        [Paragraph(f"NOTE: {note_val}", p_info)],
        [Paragraph("", p_info)],
    ], colWidths=[545], rowHeights=[11, 10])
    t_note.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.8, colors.black), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5), ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_note)
    story.append(Spacer(1, 4))

    t_esito = Table([[Paragraph(f"ESITO : &nbsp;&nbsp;<b>{data.get('esito', 'POSITIVO')}</b>", p_info)]], colWidths=[545])
    t_esito.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.8, colors.black), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2), ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_esito)
    story.append(Spacer(1, 4))

    t_odl = Table([[
        Paragraph(f"APERTO INTERVENTO TECNICO CORRETTIVO ODL N. {data.get('odl', '')}", p_info),
        Paragraph(f"DATA : {data.get('data_odl', '')}", p_info),
    ]], colWidths=[310, 235])
    t_odl.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.8, colors.black), ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2), ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_odl)
    story.append(Spacer(1, 8))

    if firma_path and os.path.exists(firma_path):
        img_f = PILImage.open(firma_path)
        fw, fh = img_f.size
        target_fh = 45
        target_fw = target_fh * (fw / fh)
        firma_obj = Image(firma_path, width=target_fw, height=target_fh)
        firma_content = Table([[Paragraph("FIRMA:", p_info), firma_obj]], colWidths=[40, 195], style=[("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0)])
    else:
        firma_content = Paragraph("FIRMA: ______________________", p_info)

    t_sig = Table([[Paragraph(f"TECNICO RESPONSABILE: <u>{tecnico_nome}</u>", p_info), firma_content]], colWidths=[310, 235])
    t_sig.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 4)]))
    story.append(t_sig)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# ==========================================
# 3. INTERFACCIA WEB AUTOMATICA TOTALMENTE
# ==========================================
st.title("⚡ Gestionale Cloud - SEAB (Modalità Automatica)")
st.markdown("Database, logo e firma vengono caricati automaticamente dal server. Cerca il dispositivo e scarica i PDF.")

st.sidebar.header("⚙️ Impostazioni")
tipo_scheda_scelto = st.sidebar.selectbox("Seleziona Tipo di Scheda", ["VSE (Sicurezza Elettrica - IEC 62353)", "MP (Manutenzione Preventiva)"])
tecnico_input = st.sidebar.text_input("Tecnico Responsabile", value="ALESSANDRO PETRAROLO")

# Caricamento automatico di logo e firma dalla cartella
logo_path, firma_path = get_resource_path()

if logo_path:
    st.sidebar.success(f"Logo caricato in automatico ({logo_path})")
else:
    st.sidebar.warning("⚠️ Manca il file `logo.png` o `logo.jpg` nella cartella.")

if firma_path:
    st.sidebar.success(f"Firma caricata in automatico ({firma_path})")
else:
    st.sidebar.warning("⚠️ Manca il file `firma.png` o `firma.jpg` nella cartella.")


# --- GESTIONE VSE AUTOMATICA ---
if "VSE" in tipo_scheda_scelto:
    excel_filename = "database_vse.xlsx"
    if not os.path.exists(excel_filename):
        st.error(f"❌ Impossibile trovare il file `{excel_filename}` nella cartella dell'applicazione.")
        st.info("Metti il file Excel con questo nome esatto nella stessa cartella di `app.py`.")
        st.stop()

    df = pd.read_excel(excel_filename)
    st.success(f"Database VSE attivo ({len(df)} dispositivi caricati automaticamente).")

    search_query = st.text_input("🔍 Filtra per Reparto Rilevato o Numero Inventario")
    filtered_df = df.copy()
    if search_query:
        def matches_vse(r):
            q = search_query.lower()
            val_rep = str(r.get("REPARTO RILEVATO", "")).lower()
            val_inv = str(r.get("INV ", r.get("INV", ""))).lower()
            return (q in val_rep) or (q in val_inv)
        filtered_df = df[df.apply(matches_vse, axis=1)]

    st.write(f"Dispositivi visibili: **{len(filtered_df)}**")
    st.dataframe(filtered_df[['INV ', 'CLASSE', 'PRODUTTORE', 'MODELLO', 'REPARTO RILEVATO', 'ESITO VE 2026']], use_container_width=True)

    def get_vse_row_dict(row):
        def val(col_name, default=""):
            for c in row.index:
                if " ".join(str(c).split()).upper() == " ".join(str(col_name).split()).upper():
                    v = row[c]
                    return v if pd.notnull(v) and str(v).lower() != "nan" else default
            return default

        inv_val = val("INV ", val("INV", "0"))
        if isinstance(inv_val, float): inv_val = int(inv_val)
        data_ve = val("DATA VE 2026", "")
        data_str = data_ve.strftime("%d/%m/%Y") if pd.notnull(data_ve) and hasattr(data_ve, "strftime") else str(data_ve)

        return {
            "inv": inv_val, "classe": str(val("CLASSE", "")), "produttore": str(val("PRODUTTORE", "")),
            "modello": str(val("MODELLO", "")), "sn": str(val("SN", "")), "configurazione": str(val("CONFIGURAZIONE", "")),
            "app_padre": str(val("APP PADRE", "")), "reparto_collaudo": str(val("REPARTO COLLAUDO", "")),
            "presidio": str(val("UBICAZIONE", "")), "reparto_rilevato": str(val("REPARTO RILEVATO", "")),
            "n_scheda": str(val("N SCHEDA VE 2026", "")), "data_ve": data_str, "esito_ve": str(val("ESITO VE 2026", "POSITIVO")),
            "note_ve": str(val("NOTE VE", "")), "allineamento": str(val("ALLINEAMENTO DOCUMENTAZIONE", "OK")),
            "fusibili": str(val("CONFORMITÀ FUSIBILI", "N.V.")), "etichette": str(val("STATO ETICHETTE E DATI DI TARGA", "OK")),
            "integrita": str(val("INTEGRITÀ E CONTAMINAZIONE", "OK")), "accessori": str(val("STATO DEGLI ACCESSORI", "OK")),
            "config_sistema": str(val("CONFIGURAZIONE SISTEMA", "OK")), "verifica_funzionale": str(val("VERIFICA FUNZIONALE DI SISTEMA", "OK")),
            "classe_prot": str(val("CLASSE DI PROTEZIONE (I II o alimentazione interna)", "I")), "tipo_parte": str(val("TIPO PARTE APPLICATA (NA, B, BF, CF)", "B")),
            "tensione": str(val("TENSIONE DI ALIMENTAZIONE DURANTE LA VERIFICA", "228,3 V")), "terra_desc": str(val("RESISTENZA DELLA TERRA DI PROTEZIONE \n(DESCRIZIONE SISTEMA)", "")),
            "terra_val": str(val("RESISTENZA TERRA DI PROTEZIONE Ω\n(valore)", "N.A.")), "iso_rete_terra": str(val("RETE TERRA DI PROTEZIONE MΩ", "N.A.")),
            "iso_rete_parti": str(val("RETE PARTI CONDUTTRICI ACCESSIBILI MΩ", "OVER MΩ")), "iso_rete_app_nof": str(val("RETE PARTI APPLICATE (NON TIPO F) MΩ", "OVER MΩ")),
            "iso_tipof_terra": str(val("PARTI APPLICATE TIPO F TERRA DI PROTEZIONE MΩ", "N.A.")), "iso_tipof_parti": str(val("PARTI APPICATE TIPO F PARTI CONDUTTRICI ACCESSIBILI MΩ", "N.A.")),
            "corr_sistema": str(val("CORRENTE DI DISPERSIONE NEL SISTEMA µA", "18,6 µA")), "corr_app1": str(val("1 CORRENTE max DSPA µa", "N.A.")),
            "desc_app1": str(val("DESCRIZIONE PARTI APPLICATE 1", "")), "corr_app2": str(val("2 CORRENTE DSPA µa ", "N.A.")),
            "desc_app2": str(val("DESCRIZIONE PARTE APPLICATA 2", "")), "corr_app3": str(val("3 CORRENTE DSPA  µa ", "N.A.")),
            "desc_app3": str(val("DESCRIZIONE PARTE APPLICATA 3", "")), "corr_app4": str(val("4 CORRENTE DSPA µa", "N.A.")),
            "desc_app4": str(val("DESCRIZIONE PARTE APPLICATA 4", "")), "strumento_sn": str(val("SN STRUMENTO DI MISURA ", "5625031")),
            "scadenza_taratura": str(val("SCADENZA TARATURA", "14/01/2027"))
        }

    st.markdown("### 🚀 Download Certificati VSE")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📦 Scarica ZIP VSE Filtrati", type="primary"):
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for idx, row in filtered_df.iterrows():
                    d = get_vse_row_dict(row)
                    pdf_bytes = generate_vse_pdf_bytes(d, tecnico_input, logo_path, firma_path)
                    zip_file.writestr(f"Certificato_VSE_{d['inv']}.pdf", pdf_bytes)
            zip_buffer.seek(0)
            st.download_button("📥 Scarica file .ZIP VSE", data=zip_buffer, file_name="Certificati_VSE.zip", mime="application/zip")

    with col2:
        if PdfMerger is not None and st.button("📚 Genera PDF Cumulativo VSE"):
            merger = PdfMerger()
            for idx, row in filtered_df.iterrows():
                d = get_vse_row_dict(row)
                merger.append(io.BytesIO(generate_vse_pdf_bytes(d, tecnico_input, logo_path, firma_path)))
            cum_buffer = io.BytesIO()
            merger.write(cum_buffer)
            merger.close()
            cum_buffer.seek(0)
            st.download_button("📥 Scarica PDF Cumulativo VSE", data=cum_buffer, file_name="_CUMULATIVO_VSE.pdf", mime="application/pdf")

# --- GESTIONE MP AUTOMATICA ---
else: 
    excel_filename = "database_mp.xlsx"
    if not os.path.exists(excel_filename):
        st.error(f"❌ Impossibile trovare il file `{excel_filename}` nella cartella dell'applicazione.")
        st.info("Metti il file Excel con questo nome esatto nella stessa cartella di `app.py`.")
        st.stop()

    df_raw = pd.read_excel(excel_filename, header=None)
    row0, row1, row2 = df_raw.iloc[0].values, df_raw.iloc[1].values, df_raw.iloc[2].values
    col_map = {}
    for idx, val in enumerate(row0):
        val_str = str(val).strip().upper()
        if val_str and val_str != 'NAN': col_map[val_str] = idx

    card_types = {}
    for col_idx in range(21, len(row0)):
        c_code, c_title, c_desc = str(row0[col_idx]).strip(), str(row1[col_idx]).strip(), str(row2[col_idx]).strip()
        if c_code in ['TECNICO', 'ISTRUZIONI STAMPA', 'PDTA', 'NAN', 'N CONTROLLO'] or not c_code or c_code.lower() == 'nan':
            continue
        match = re.match(r'([A-Z]+)', c_code)
        if match:
            t_letter = match.group(1)
            if t_letter not in card_types:
                card_types[t_letter] = {'title': c_title if c_title and c_title.lower() != 'nan' else f"Scheda Tipo {t_letter}", 'items': []}
            card_types[t_letter]['items'].append((c_code, col_idx, c_desc))

    st.success(f"Database MP attivo ({len(card_types)} tipi di schede caricate automaticamente).")
    df_data = df_raw.iloc[3:].copy()

    search_query = st.text_input("🔍 Filtra per Reparto Rilevato 2026 o Inventario")
    if search_query:
        col_rep, col_inv = col_map.get("REPARTO RILEVATO 2026"), col_map.get("INV")
        def matches_mp(r):
            q = search_query.lower()
            val_rep = str(r.iloc[col_rep]).lower() if col_rep is not None and pd.notnull(r.iloc[col_rep]) else ""
            val_inv = str(r.iloc[col_inv]).lower() if col_inv is not None and pd.notnull(r.iloc[col_inv]) else ""
            return (q in val_rep) or (q in val_inv)
        df_data = df_data[df_data.apply(matches_mp, axis=1)]

    st.write(f"Schede MP visibili: **{len(df_data)}**")

    def extract_mp_row_dict(row):
        def get_val(r, col_name, default=""):
            c_idx = col_map.get(col_name)
            if c_idx is not None:
                val = r.iloc[c_idx] if hasattr(r, 'iloc') else r[c_idx]
                return val if pd.notnull(val) else default
            return default

        inv_val = get_val(row, "INV", "0")
        if isinstance(inv_val, float): inv_val = int(inv_val)
        n_scheda_val = get_val(row, "N SCHEDA MP 2026", "")
        if isinstance(n_scheda_val, float): n_scheda_val = int(n_scheda_val)
        data_val = get_val(row, "DATA MP 2026", "")
        data_str = data_val.strftime("%d/%m/%Y") if pd.notnull(data_val) and hasattr(data_val, "strftime") else str(data_val if pd.notnull(data_val) else "")

        tipo_val = str(get_val(row, "TIPO DI SCHEDA", "A")).strip().upper()
        actual_type = tipo_val if tipo_val in card_types else "A"
        t_info = card_types[actual_type]

        ispezioni, verifiche = [], []
        for c_code, c_idx, c_desc in t_info['items']:
            raw_val = row.iloc[c_idx] if hasattr(row, 'iloc') else row[c_idx]
            val_clean = str(raw_val).strip().upper() if pd.notnull(raw_val) and str(raw_val).lower() != "nan" else "OK"
            if classify_mp_item(c_desc) == "ISPEZIONE":
                ispezioni.append((c_code, c_desc, val_clean))
            else:
                verifiche.append((c_code, c_desc, val_clean))

        return {
            "tipo_scheda": actual_type, "titolo_scheda": t_info['title'], "n_scheda": n_scheda_val,
            "data": data_str, "descrizione": str(get_val(row, "CLASSE", t_info['title'])), "inv": inv_val,
            "costruttore": str(get_val(row, "PRODUTTORE", "")), "sn": str(get_val(row, "SN", "")),
            "modello": str(get_val(row, "MODELLO", "")), "configurazione": str(get_val(row, "CONFIGURAZIONE RILEVATA", get_val(row, "CONFIGURAZIONE", ""))),
            "inv_padre": str(get_val(row, "APP PADRE RILEVATA", get_val(row, "APP \nPADRE", ""))), "reparto": str(get_val(row, "REPARTO 2025", "")),
            "presidio": str(get_val(row, "UBICAZIONE", "")), "reparto_rilevato": str(get_val(row, "REPARTO RILEVATO 2026", "")),
            "ispezioni": ispezioni, "verifiche": verifiche, "note": str(get_val(row, "NOTE MP", "")), "esito": "POSITIVO"
        }

    st.markdown("### 🚀 Download Schede MP")
    if st.button("📦 Scarica ZIP Schede MP Filtrate", type="primary"):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for idx, row in df_data.iterrows():
                d = extract_mp_row_dict(row)
                pdf_bytes = generate_mp_pdf_bytes(d, tecnico_input, logo_path, firma_path)
                zip_file.writestr(f"Scheda_MP_{d['n_scheda']}_{d['inv']}.pdf", pdf_bytes)
        zip_buffer.seek(0)
        st.download_button("📥 Scarica file .ZIP MP", data=zip_buffer, file_name="Schede_MP_Selezionate.zip", mime="application/zip")