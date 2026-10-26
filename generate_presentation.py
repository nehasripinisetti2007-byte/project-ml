import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

PROJECT_DIR = r"C:\Users\nehas\OneDrive\Desktop\Fake-News-Detection"
TITLE_LOGO = os.path.join(PROJECT_DIR, "aditya_title_logo.png")
CORNER_LOGO = os.path.join(PROJECT_DIR, "aditya_corner_logo.png")
OUTPUT_PPTX = os.path.join(PROJECT_DIR, "Fake_News_Detection_Presentation.pptx")

# Color palette - Clean, high contrast, easy to read
ORANGE = RGBColor(234, 88, 12)        # #ea580c - Aditya Vibrant Orange
NAVY = RGBColor(15, 59, 104)          # #0f3b68 - Aditya Navy Blue
DARK_SLATE = RGBColor(30, 41, 59)     # #1e293b - Clear dark text
MUTED_SLATE = RGBColor(100, 116, 139) # #64748b - Subtitle / meta text
CARD_BG = RGBColor(248, 250, 252)     # #f8fafc - Soft light card background
CARD_BORDER = RGBColor(226, 232, 240) # #e2e8f0 - Clean border
PEACH_BG = RGBColor(255, 241, 230)    # #fff1e6 - Soft warm peach
PEACH_BORDER = RGBColor(254, 215, 170)
WHITE = RGBColor(255, 255, 255)
GREEN = RGBColor(16, 185, 129)
BLUE_ACCENT = RGBColor(2, 132, 199)

def build_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    def set_white_bg(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = WHITE
        bg.line.fill.background()
        return bg

    def add_header(slide, title_text):
        set_white_bg(slide)
        if os.path.exists(CORNER_LOGO):
            slide.shapes.add_picture(CORNER_LOGO, Inches(11.0), Inches(0.4), width=Inches(1.85))

        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.42), Inches(9.8), Inches(0.8))
        tf = title_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = title_text
        p.font.name = "Calibri"
        p.font.size = Pt(26)
        p.font.bold = True
        p.font.color.rgb = ORANGE

    def add_card(slide, left, top, width, height, bg_color=CARD_BG, border_color=CARD_BORDER):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        if border_color:
            card.line.color.rgb = border_color
            card.line.width = Pt(1.2)
        else:
            card.line.fill.background()
        return card

    # =========================================================================
    # SLIDE 1: TITLE SLIDE (5 Actual Team Members & Guide from User Screenshot)
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_white_bg(s1)

    # Center Logo
    if os.path.exists(TITLE_LOGO):
        s1.shapes.add_picture(TITLE_LOGO, Inches(4.35), Inches(0.6), width=Inches(4.63))

    # Project Title
    t_box = s1.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(11.333), Inches(1.3))
    tf1 = t_box.text_frame
    tf1.word_wrap = True
    p1 = tf1.paragraphs[0]
    p1.text = "Fake News Detection System"
    p1.alignment = PP_ALIGN.CENTER
    p1.font.name = "Calibri"
    p1.font.size = Pt(32)
    p1.font.bold = True
    p1.font.color.rgb = ORANGE

    p1_sub = tf1.add_paragraph()
    p1_sub.text = "Using Multi-Model Machine Learning and NLP"
    p1_sub.alignment = PP_ALIGN.CENTER
    p1_sub.font.name = "Calibri"
    p1_sub.font.size = Pt(24)
    p1_sub.font.bold = True
    p1_sub.font.color.rgb = ORANGE

    # Course & Department Line
    sub_box = s1.shapes.add_textbox(Inches(1.5), Inches(3.2), Inches(10.333), Inches(0.45))
    p_sub = sub_box.text_frame.paragraphs[0]
    p_sub.text = "Machine Learning (241AI024)  |  Department of AIML  |  Final Review"
    p_sub.alignment = PP_ALIGN.CENTER
    p_sub.font.name = "Calibri"
    p_sub.font.size = Pt(14)
    p_sub.font.bold = True
    p_sub.font.color.rgb = NAVY

    # Team Members Header
    tm_hdr = s1.shapes.add_textbox(Inches(1.0), Inches(3.78), Inches(11.333), Inches(0.35))
    p_tm = tm_hdr.text_frame.paragraphs[0]
    p_tm.text = "Team Members"
    p_tm.alignment = PP_ALIGN.CENTER
    p_tm.font.name = "Calibri"
    p_tm.font.size = Pt(13)
    p_tm.font.bold = True
    p_tm.font.color.rgb = DARK_SLATE

    # 5 Actual Team Members (From user's uploaded slide photo)
    team_members = [
        ("P. Nehasri", "24B11AI346"),
        ("M. Nithin", "24B11AI226"),
        ("K. Vikas", "24B11AI190"),
        ("R. Pranathi", "24B11AI365"),
        ("Y. Chakradhar", "24B11AI462"),
    ]
    card_w = Inches(2.15)
    card_h = Inches(1.1)
    gap_x = Inches(0.2)
    start_x = Inches(0.89)
    top_y = Inches(4.2)

    for i, (name, roll) in enumerate(team_members):
        x = start_x + i * (card_w + gap_x)
        add_card(s1, x, top_y, card_w, card_h, bg_color=CARD_BG, border_color=CARD_BORDER)
        box = s1.shapes.add_textbox(x, top_y + Inches(0.12), card_w, card_h - Inches(0.24))
        tf = box.text_frame
        tf.word_wrap = True
        p_n = tf.paragraphs[0]
        p_n.text = name
        p_n.alignment = PP_ALIGN.CENTER
        p_n.font.name = "Calibri"
        p_n.font.size = Pt(13.5)
        p_n.font.bold = True
        p_n.font.color.rgb = DARK_SLATE

        p_r = tf.add_paragraph()
        p_r.text = roll
        p_r.alignment = PP_ALIGN.CENTER
        p_r.font.name = "Calibri"
        p_r.font.size = Pt(11.5)
        p_r.font.color.rgb = MUTED_SLATE

    # Guide Box
    guide_w = Inches(8.0)
    guide_h = Inches(0.75)
    guide_x = (prs.slide_width - guide_w) / 2
    guide_y = Inches(5.7)
    add_card(s1, guide_x, guide_y, guide_w, guide_h, bg_color=PEACH_BG, border_color=PEACH_BORDER)

    g_box = s1.shapes.add_textbox(guide_x, guide_y + Inches(0.1), guide_w, guide_h - Inches(0.2))
    tf_g = g_box.text_frame
    p_g = tf_g.paragraphs[0]
    p_g.alignment = PP_ALIGN.CENTER
    r_lead = p_g.add_run()
    r_lead.text = "Guide: "
    r_lead.font.name = "Calibri"
    r_lead.font.size = Pt(13.5)
    r_lead.font.bold = True
    r_lead.font.color.rgb = DARK_SLATE

    r_guide = p_g.add_run()
    r_guide.text = "P. Venkata Bala Annapurna, M.Tech (Ph.D)\n"
    r_guide.font.name = "Calibri"
    r_guide.font.size = Pt(13)
    r_guide.font.bold = True
    r_guide.font.color.rgb = NAVY

    r_desig = p_g.add_run()
    r_desig.text = "Asst. Professor, Department of AIML"
    r_desig.font.name = "Calibri"
    r_desig.font.size = Pt(11.5)
    r_desig.font.color.rgb = DARK_SLATE

    # =========================================================================
    # SLIDE 2: ABSTRACT (Clear, Simple & Presentation-Ready)
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    add_header(s2, "Abstract")

    left_box2 = s2.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(7.4), Inches(5.3))
    tf2 = left_box2.text_frame
    tf2.word_wrap = True

    pts2 = [
        ("The Goal: ", "Automatically detect whether an online news article or headline is REAL or FAKE before it spreads."),
        ("Multi-Model Approach: ", "Combines 3 proven Machine Learning algorithms (Linear SVM, Logistic Regression, Random Forest) for reliable consensus."),
        ("Large-Scale Dataset: ", "Trained and tested on 44,898 benchmark articles from the ISOT dataset and modern viral scams."),
        ("High Accuracy: ", "Achieves 99.07% accuracy with sub-second response time (< 40 milliseconds)."),
        ("Easy Explainability: ", "Features a simple 0 to 100% Credibility Speedometer so ordinary users can easily understand the verdict.")
    ]
    for i, (b_lead, b_text) in enumerate(pts2):
        p = tf2.paragraphs[0] if i == 0 else tf2.add_paragraph()
        p.space_after = Pt(16)
        r1 = p.add_run()
        r1.text = "•  " + b_lead
        r1.font.bold = True
        r1.font.size = Pt(15)
        r1.font.color.rgb = DARK_SLATE
        r2 = p.add_run()
        r2.text = b_text
        r2.font.size = Pt(14)
        r2.font.color.rgb = DARK_SLATE

    # Right Side: 4 Highlight Cards
    highlights = [
        ("44,898", "Articles Evaluated", "Balanced Real & Fake news dataset"),
        ("99.07%", "Classification Accuracy", "Optimal Linear SVM performance"),
        ("3 Models", "Consensus Voting", "SVM + Logistic Reg. + Random Forest"),
        ("< 40ms", "Instant Real-Time Speed", "Fast prediction on any web article")
    ]
    rx2 = Inches(8.6)
    rw2 = Inches(3.9)
    for idx, (val, title, desc) in enumerate(highlights):
        y = Inches(1.5) + idx * Inches(1.3)
        add_card(s2, rx2, y, rw2, Inches(1.15), bg_color=CARD_BG, border_color=CARD_BORDER)
        c_box = s2.shapes.add_textbox(rx2 + Inches(0.2), y + Inches(0.1), rw2 - Inches(0.4), Inches(0.95))
        c_tf = c_box.text_frame
        c_tf.word_wrap = True
        p_val = c_tf.paragraphs[0]
        p_val.text = val
        p_val.font.size = Pt(20)
        p_val.font.bold = True
        p_val.font.color.rgb = ORANGE

        p_t = c_tf.add_paragraph()
        p_t.text = title
        p_t.font.size = Pt(12)
        p_t.font.bold = True
        p_t.font.color.rgb = NAVY

        p_d = c_tf.add_paragraph()
        p_d.text = desc
        p_d.font.size = Pt(10)
        p_d.font.color.rgb = MUTED_SLATE

    # =========================================================================
    # SLIDE 3: INTRODUCTION (Why is Fake News a Major Issue?)
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    add_header(s3, "Introduction")

    left_box3 = s3.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(7.4), Inches(5.3))
    tf3 = left_box3.text_frame
    tf3.word_wrap = True

    pts3 = [
        ("Social Media Growth: ", "Over 5 billion people read news daily on WhatsApp, Twitter, and Facebook without editorial fact-checking."),
        ("Types of Misinformation: ", "Includes sensational clickbait, false political claims, fake health cures, and online financial scams."),
        ("Human Checking Fails: ", "Manual fact-checking takes hours or days. By that time, false news has already reached millions of users."),
        ("The AI Solution: ", "Machine learning can analyze text patterns and linguistic cues in milliseconds to flag fake news automatically."),
        ("Project Objective: ", "Build an accurate, transparent, and easy-to-use tool that checks news credibility in real time.")
    ]
    for i, (b_lead, b_text) in enumerate(pts3):
        p = tf3.paragraphs[0] if i == 0 else tf3.add_paragraph()
        p.space_after = Pt(16)
        r1 = p.add_run()
        r1.text = "•  " + b_lead
        r1.font.bold = True
        r1.font.size = Pt(15)
        r1.font.color.rgb = DARK_SLATE
        r2 = p.add_run()
        r2.text = b_text
        r2.font.size = Pt(14)
        r2.font.color.rgb = DARK_SLATE

    # Right Card: Real-World Facts
    add_card(s3, Inches(8.6), Inches(1.5), Inches(3.9), Inches(5.3), bg_color=PEACH_BG, border_color=PEACH_BORDER)
    r3_box = s3.shapes.add_textbox(Inches(8.8), Inches(1.7), Inches(3.5), Inches(4.9))
    r3_tf = r3_box.text_frame
    r3_tf.word_wrap = True
    p3_h = r3_tf.paragraphs[0]
    p3_h.text = "Why Fake News Spreads"
    p3_h.font.size = Pt(17)
    p3_h.font.bold = True
    p3_h.font.color.rgb = ORANGE

    facts = [
        ("6x Faster Spread: ", "False news diffuses 6 times faster than authentic news online (MIT Science Study)."),
        ("70% More Retweets: ", "People retweet sensational and shocking stories far more than factual updates."),
        ("Emotional Triggers: ", "Uses urgent words like 'URGENT!!', 'SHOCKING!!', and 'ACT NOW!!' to trigger panic."),
        ("Need for Fast AI: ", "An automated tool gives users the truth before they share.")
    ]
    for b_lead, b_text in facts:
        p = r3_tf.add_paragraph()
        p.space_before = Pt(12)
        r1 = p.add_run()
        r1.text = "•  " + b_lead
        r1.font.bold = True
        r1.font.size = Pt(12.5)
        r1.font.color.rgb = DARK_SLATE
        r2 = p.add_run()
        r2.text = b_text
        r2.font.size = Pt(11.5)
        r2.font.color.rgb = DARK_SLATE

    # =========================================================================
    # SLIDE 4: PROBLEM STATEMENT (Matches User's Sample 2 Exactly)
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    add_header(s4, "Problem Statement")

    left_box4 = s4.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(7.0), Inches(5.3))
    tf4 = left_box4.text_frame
    tf4.word_wrap = True

    pts4 = [
        ("Reading news online manually is slow and impractical at modern internet scale."),
        ("Raw web text is noisy: full of URLs, mentions (@user), hashtags (#news), special characters, and grammar mistakes."),
        ("Content changes constantly, so the system must predict immediately on freshly submitted digital text."),
        ("Modern fake news mimics genuine news formats, hiding viral scams and cash-phishing traps inside convincing text."),
        ("An automated system is needed to clean text, extract keywords, and classify news accurately in seconds.")
    ]
    for i, text in enumerate(pts4):
        p = tf4.paragraphs[0] if i == 0 else tf4.add_paragraph()
        p.space_after = Pt(16)
        r = p.add_run()
        r.text = "•  " + text
        r.font.size = Pt(15)
        r.font.color.rgb = DARK_SLATE

    # Right Card: Illustrative Example (Exact Sample 2 Layout)
    ie_lbl = s4.shapes.add_textbox(Inches(8.2), Inches(1.3), Inches(4.3), Inches(0.35))
    ie_lbl.text_frame.paragraphs[0].text = "Illustrative example"
    ie_lbl.text_frame.paragraphs[0].font.size = Pt(13)
    ie_lbl.text_frame.paragraphs[0].font.bold = True
    ie_lbl.text_frame.paragraphs[0].font.color.rgb = MUTED_SLATE

    # Box 1: Raw Web Text
    add_card(s4, Inches(8.2), Inches(1.75), Inches(4.3), Inches(2.1), bg_color=CARD_BG, border_color=CARD_BORDER)
    b1_box = s4.shapes.add_textbox(Inches(8.4), Inches(1.85), Inches(3.9), Inches(1.9))
    b1_tf = b1_box.text_frame
    b1_tf.word_wrap = True
    p1_h = b1_tf.paragraphs[0]
    p1_h.text = "Raw web text"
    p1_h.font.bold = True
    p1_h.font.size = Pt(13)
    p1_h.font.color.rgb = NAVY

    p1_c = b1_tf.add_paragraph()
    p1_c.space_before = Pt(6)
    p1_c.text = "BREAKING!! Markets fall again @bbc https://t.co/xyz #news\n\nForward This Text To 20 People To Receive Fifty Thousand Dollars In Your Bank Account Today By Midnight!!"
    p1_c.font.name = "Consolas"
    p1_c.font.size = Pt(10.5)
    p1_c.font.color.rgb = DARK_SLATE

    # Downward Arrow
    arrow = s4.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, Inches(10.1), Inches(4.0), Inches(0.5), Inches(0.55))
    arrow.fill.solid()
    arrow.fill.fore_color.rgb = ORANGE
    arrow.line.fill.background()

    # Box 2: Key Challenges
    add_card(s4, Inches(8.2), Inches(4.7), Inches(4.3), Inches(2.1), bg_color=PEACH_BG, border_color=PEACH_BORDER)
    b2_box = s4.shapes.add_textbox(Inches(8.4), Inches(4.8), Inches(3.9), Inches(1.9))
    b2_tf = b2_box.text_frame
    b2_tf.word_wrap = True
    p2_h = b2_tf.paragraphs[0]
    p2_h.text = "Key NLP Challenges"
    p2_h.font.bold = True
    p2_h.font.size = Pt(13)
    p2_h.font.color.rgb = ORANGE

    challenges = [
        "Noise removal: strip links, @mentions, and hashtags.",
        "Emotional hyperbole and exaggerated punctuation (!!).",
        "Clever cash scams disguised as business news.",
        "Need multi-model consensus to avoid false alarms."
    ]
    for c in challenges:
        p = b2_tf.add_paragraph()
        p.space_before = Pt(4)
        p.text = "•  " + c
        p.font.size = Pt(10.5)
        p.font.color.rgb = DARK_SLATE

    # =========================================================================
    # SLIDE 5: OBJECTIVES AND SCOPE (Two Simple Parallel Cards)
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    add_header(s5, "Objectives and Scope of the Project")

    # Card 1: Objectives
    add_card(s5, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.3), bg_color=CARD_BG, border_color=CARD_BORDER)
    ob_box = s5.shapes.add_textbox(Inches(1.1), Inches(1.7), Inches(5.0), Inches(4.9))
    ob_tf = ob_box.text_frame
    ob_tf.word_wrap = True
    p_ob_h = ob_tf.paragraphs[0]
    p_ob_h.text = "Project Objectives"
    p_ob_h.font.size = Pt(18)
    p_ob_h.font.bold = True
    p_ob_h.font.color.rgb = NAVY

    objs = [
        ("Automate Text Preprocessing: ", "Clean URLs, stopwords, and symbols using standard NLP techniques."),
        ("Train 3 Machine Learning Models: ", "Compare Linear SVM, Logistic Regression, and Random Forest."),
        ("Multi-Model Consensus: ", "All 3 models vote on the final prediction for maximum reliability."),
        ("Credibility Speedometer: ", "Provide a clear 0-100% credibility score with visual signals."),
        ("Deploy Web Application: ", "Build a responsive Flask website where anyone can test news in real time.")
    ]
    for b_lead, b_text in objs:
        p = ob_tf.add_paragraph()
        p.space_before = Pt(12)
        r1 = p.add_run()
        r1.text = "•  " + b_lead
        r1.font.bold = True
        r1.font.size = Pt(13)
        r1.font.color.rgb = DARK_SLATE
        r2 = p.add_run()
        r2.text = b_text
        r2.font.size = Pt(12)
        r2.font.color.rgb = DARK_SLATE

    # Card 2: Scope
    add_card(s5, Inches(6.9), Inches(1.5), Inches(5.6), Inches(5.3), bg_color=PEACH_BG, border_color=PEACH_BORDER)
    sc_box = s5.shapes.add_textbox(Inches(7.2), Inches(1.7), Inches(5.0), Inches(4.9))
    sc_tf = sc_box.text_frame
    sc_tf.word_wrap = True
    p_sc_h = sc_tf.paragraphs[0]
    p_sc_h.text = "Project Scope"
    p_sc_h.font.size = Pt(18)
    p_sc_h.font.bold = True
    p_sc_h.font.color.rgb = ORANGE

    scopes = [
        ("In Scope - News Articles: ", "Works for both short news headlines and full-length articles."),
        ("In Scope - Real-Time Predictions: ", "Instant classification with probability percentages in under 40ms."),
        ("In Scope - User Feedback: ", "Users can mark ground truth to continuously evaluate models."),
        ("Boundary - Modality: ", "Currently checks text only (video/image deepfakes are future scope)."),
        ("Boundary - Language: ", "Designed for English news (multilingual expansion planned).")
    ]
    for b_lead, b_text in scopes:
        p = sc_tf.add_paragraph()
        p.space_before = Pt(12)
        r1 = p.add_run()
        r1.text = "•  " + b_lead
        r1.font.bold = True
        r1.font.size = Pt(13)
        r1.font.color.rgb = DARK_SLATE
        r2 = p.add_run()
        r2.text = b_text
        r2.font.size = Pt(12)
        r2.font.color.rgb = DARK_SLATE

    # =========================================================================
    # SLIDE 6: DATASET DESCRIPTION (Simple & Visual)
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    add_header(s6, "Dataset Description")

    left_box6 = s6.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(5.8), Inches(5.4))
    tf6 = left_box6.text_frame
    tf6.word_wrap = True

    pts6 = [
        ("ISOT Dataset Benchmark: ", "Created by the Information Security & Object Technology (ISOT) research lab."),
        ("Real News (21,417 articles): ", "Authentic articles scraped from verified Reuters wire service reporting."),
        ("Fake News (23,481 articles): ", "Fabricated articles collected from flagged untrustworthy websites and blogs."),
        ("Total Size: ", "44,898 total news articles covering global politics and world events."),
        ("Balanced Distribution: ", "47.7% Real vs 52.3% Fake — balanced data ensures unbiased training."),
        ("Modern Scam Addition: ", "Enhanced with modern verified scams (phishing & WhatsApp chains) for contemporary accuracy.")
    ]
    for i, (b_lead, b_text) in enumerate(pts6):
        p = tf6.paragraphs[0] if i == 0 else tf6.add_paragraph()
        p.space_after = Pt(14)
        r1 = p.add_run()
        r1.text = "•  " + b_lead
        r1.font.bold = True
        r1.font.size = Pt(14)
        r1.font.color.rgb = DARK_SLATE
        r2 = p.add_run()
        r2.text = b_text
        r2.font.size = Pt(13.5)
        r2.font.color.rgb = DARK_SLATE

    # Right Side: EDA Distribution Chart
    chart_eda_p = os.path.join(PROJECT_DIR, "chart_eda_features.png")
    if os.path.exists(chart_eda_p):
        s6.shapes.add_picture(chart_eda_p, Inches(6.8), Inches(1.6), width=Inches(5.7))

    # =========================================================================
    # SLIDE 7: DATA PREPROCESSING (6 Clean Simple Steps + Clean Diagram)
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    add_header(s7, "Data Preprocessing")

    left_box7 = s7.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(5.8), Inches(5.4))
    tf7 = left_box7.text_frame
    tf7.word_wrap = True

    pts7 = [
        ("1. Cleaning: ", "Remove URLs (http://...), @mentions, HTML tags, and punctuation noise."),
        ("2. Lowercasing: ", "Convert all words to lowercase so 'BREAKING' matches 'breaking'."),
        ("3. Tokenization: ", "Break continuous sentences into individual word tokens."),
        ("4. Stopword Removal: ", "Filter out non-meaningful words like 'the', 'is', 'at'."),
        ("5. Lemmatization: ", "Convert words to their dictionary root form ('cured' -> 'cure')."),
        ("6. TF-IDF Vectorizer: ", "Transform words into numerical scores (top 5,000 unigrams & bigrams).")
    ]
    for i, (b_lead, b_text) in enumerate(pts7):
        p = tf7.paragraphs[0] if i == 0 else tf7.add_paragraph()
        p.space_after = Pt(14)
        r1 = p.add_run()
        r1.text = "•  " + b_lead
        r1.font.bold = True
        r1.font.size = Pt(14)
        r1.font.color.rgb = DARK_SLATE
        r2 = p.add_run()
        r2.text = b_text
        r2.font.size = Pt(13.5)
        r2.font.color.rgb = DARK_SLATE

    # Right Side: Workflow Diagram
    wf_img = os.path.join(PROJECT_DIR, "workflow_diagram.png")
    if os.path.exists(wf_img):
        s7.shapes.add_picture(wf_img, Inches(6.8), Inches(1.6), width=Inches(5.7))

    # =========================================================================
    # SLIDE 8: EXPLORATORY DATA ANALYSIS (EDA)
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    add_header(s8, "Exploratory Data Analysis (EDA)")

    left_box8 = s8.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(6.8), Inches(5.4))
    tf8 = left_box8.text_frame
    tf8.word_wrap = True

    pts8 = [
        ("Article Length Disparity: ", "Real news has a steady average length (~412 words). Fake news is either very short clickbait (<50 words) or long rambling blogs."),
        ("Vocabulary Patterns: ", "Real news frequently uses formal attribution words ('reuters', 'washington', 'spokesman'). Fake news heavily overuses emotional words ('shocking', 'exposed', 'secret', 'miracle')."),
        ("Headline Capitalization: ", "Fake headlines use 3.8x more capital letters ('ALL CAPS') to shout and attract attention."),
        ("Exclamation Marks (!!!): ", "Fake news uses exclamation marks 4 times more often than genuine wire news."),
        ("Key Insight: ", "Combining word frequency (TF-IDF) with punctuation and capitalization markers produces the highest detection accuracy.")
    ]
    for i, (b_lead, b_text) in enumerate(pts8):
        p = tf8.paragraphs[0] if i == 0 else tf8.add_paragraph()
        p.space_after = Pt(15)
        r1 = p.add_run()
        r1.text = "•  " + b_lead
        r1.font.bold = True
        r1.font.size = Pt(14)
        r1.font.color.rgb = DARK_SLATE
        r2 = p.add_run()
        r2.text = b_text
        r2.font.size = Pt(13.5)
        r2.font.color.rgb = DARK_SLATE

    # Right Side: Quick Comparison Card
    add_card(s8, Inches(8.0), Inches(1.5), Inches(4.5), Inches(5.3), bg_color=CARD_BG, border_color=CARD_BORDER)
    r8_box = s8.shapes.add_textbox(Inches(8.2), Inches(1.7), Inches(4.1), Inches(4.9))
    r8_tf = r8_box.text_frame
    r8_tf.word_wrap = True
    p8_h = r8_tf.paragraphs[0]
    p8_h.text = "Real vs Fake Text Patterns"
    p8_h.font.size = Pt(16)
    p8_h.font.bold = True
    p8_h.font.color.rgb = NAVY

    eda_stats = [
        ("Average Article Length", "Real: ~412 words", "Fake: ~289 words (High variance)"),
        ("Headline Uppercase (ALL CAPS)", "Real: 6.2% of chars", "Fake: 23.8% (3.8x higher)"),
        ("Exclamation Mark Pct (!)", "Real: 0.8% of sentences", "Fake: 14.2% of sentences"),
        ("Source Attribution", "Real: 88% cite sources", "Fake: 12% cite sources"),
        ("Top Characteristic Words", "Real: 'reuters', 'confirmed'", "Fake: 'shocking', 'exposed'")
    ]
    for metric, r_stat, f_stat in eda_stats:
        p = r8_tf.add_paragraph()
        p.space_before = Pt(8)
        r_m = p.add_run()
        r_m.text = "• " + metric + "\n"
        r_m.font.bold = True
        r_m.font.size = Pt(11.5)
        r_m.font.color.rgb = ORANGE

        r_v = p.add_run()
        r_v.text = f"   • {r_stat}\n   • {f_stat}"
        r_v.font.size = Pt(10.5)
        r_v.font.color.rgb = DARK_SLATE

    # =========================================================================
    # SLIDE 9: PROPOSED METHODOLOGY (6 Simple Steps + Architecture)
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    add_header(s9, "Proposed Methodology")

    left_box9 = s9.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(5.8), Inches(5.4))
    tf9 = left_box9.text_frame
    tf9.word_wrap = True

    pts9 = [
        ("Step 1 - User Input: ", "User submits news text or a headline through the web interface."),
        ("Step 2 - Text Preprocessing: ", "Removes noise, lowercases text, and lemmatizes root words."),
        ("Step 3 - TF-IDF Vectorization: ", "Extracts the 5,000 most informative unigram and bigram word features."),
        ("Step 4 - 3 ML Models Predict: ", "Linear SVM, Logistic Regression, and Random Forest evaluate text simultaneously."),
        ("Step 5 - Credibility Speedometer: ", "Combines model probabilities with linguistic indicators into a 0-100% score."),
        ("Step 6 - Instant Output: ", "Displays REAL or FAKE verdict with clear consensus across all 3 models.")
    ]
    for i, (b_lead, b_text) in enumerate(pts9):
        p = tf9.paragraphs[0] if i == 0 else tf9.add_paragraph()
        p.space_after = Pt(13)
        r1 = p.add_run()
        r1.text = "•  " + b_lead
        r1.font.bold = True
        r1.font.size = Pt(14)
        r1.font.color.rgb = DARK_SLATE
        r2 = p.add_run()
        r2.text = b_text
        r2.font.size = Pt(13)
        r2.font.color.rgb = DARK_SLATE

    # Right Side: Architecture Diagram
    arch_img = os.path.join(PROJECT_DIR, "system_architecture.png")
    if os.path.exists(arch_img):
        s9.shapes.add_picture(arch_img, Inches(6.8), Inches(1.6), width=Inches(5.7))

    # =========================================================================
    # SLIDE 10: MACHINE LEARNING ALGORITHMS USED (3 Clean Side-by-Side Cards)
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    add_header(s10, "Machine Learning Algorithms Used")

    card_w10 = Inches(3.7)
    card_h10 = Inches(5.2)
    start_x10 = Inches(0.8)
    gap_x10 = Inches(0.35)
    top_y10 = Inches(1.5)

    algo_cards = [
        ("Linear SVM", "Primary Active Model", ORANGE, [
            ("How it works: ", "Finds the optimal straight-line boundary separating Real from Fake news in high-dimensional text space."),
            ("Why we chose it: ", "Performs best for sparse text with 5,000 word features. Does not suffer from overfitting."),
            ("Role in System: ", "Serves as the primary active classifier for live predictions."),
            ("Accuracy: ", "99.07% accuracy (highest overall score in our project).")
        ]),
        ("Logistic Regression", "Probabilistic Baseline", NAVY, [
            ("How it works: ", "Uses the Sigmoid curve function to calculate probability percentages between 0% and 100%."),
            ("Why we chose it: ", "Provides smooth, calibrated probability scores that power our Credibility Speedometer."),
            ("Role in System: ", "Gives calibrated probabilistic confidence."),
            ("Accuracy: ", "98.71% accuracy with fast sub-millisecond speed.")
        ]),
        ("Random Forest", "Non-Linear Ensemble", DARK_SLATE, [
            ("How it works: ", "Builds a forest of 100 decision trees that all vote together on the result."),
            ("Why we chose it: ", "Captures complex word combinations and resists noisy outlier text."),
            ("Role in System: ", "Provides independent ensemble validation for linear models."),
            ("Accuracy: ", "98.98% accuracy and 98.93% F1-score.")
        ])
    ]

    for idx, (title, tag, tag_color, bullets) in enumerate(algo_cards):
        x = start_x10 + idx * (card_w10 + gap_x10)
        add_card(s10, x, top_y10, card_w10, card_h10, bg_color=CARD_BG, border_color=CARD_BORDER)
        box = s10.shapes.add_textbox(x + Inches(0.2), top_y10 + Inches(0.2), card_w10 - Inches(0.4), card_h10 - Inches(0.4))
        tf = box.text_frame
        tf.word_wrap = True

        p_t = tf.paragraphs[0]
        p_t.text = title
        p_t.font.size = Pt(17)
        p_t.font.bold = True
        p_t.font.color.rgb = tag_color

        p_tag = tf.add_paragraph()
        p_tag.text = f"[{tag}]"
        p_tag.font.size = Pt(11)
        p_tag.font.bold = True
        p_tag.font.color.rgb = MUTED_SLATE

        for b_lead, b_text in bullets:
            p = tf.add_paragraph()
            p.space_before = Pt(10)
            r1 = p.add_run()
            r1.text = "• " + b_lead
            r1.font.bold = True
            r1.font.size = Pt(12)
            r1.font.color.rgb = DARK_SLATE
            r2 = p.add_run()
            r2.text = b_text
            r2.font.size = Pt(11.5)
            r2.font.color.rgb = DARK_SLATE

    # =========================================================================
    # SLIDE 11: MODEL TRAINING AND TESTING (Clean & Simple Numbers)
    # =========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    add_header(s11, "Model Training and Testing")

    left_box11 = s11.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(6.8), Inches(5.4))
    tf11 = left_box11.text_frame
    tf11.word_wrap = True

    pts11 = [
        ("80/20 Train-Test Split: ", "35,918 articles used for training. 8,980 unseen articles kept aside strictly for testing."),
        ("Stratified Sampling: ", "Ensures an exact 50/50 balance of Real and Fake articles in both training and test sets."),
        ("Modern Scam Weighting: ", "Applied 150x weight on contemporary scams so the AI easily catches new WhatsApp cash & lottery phishing."),
        ("Hyperparameter Tuning: ", "• Linear SVM: Regularization C=1.0, Linear kernel.\n• Logistic Regression: L2 penalty, C=2.0.\n• Random Forest: 100 trees, max_features='sqrt'."),
        ("Tested on Both Types: ", "Achieves 99% accuracy on full articles and 95% accuracy on short isolated headlines.")
    ]
    for i, (b_lead, b_text) in enumerate(pts11):
        p = tf11.paragraphs[0] if i == 0 else tf11.add_paragraph()
        p.space_after = Pt(14)
        r1 = p.add_run()
        r1.text = "•  " + b_lead
        r1.font.bold = True
        r1.font.size = Pt(14)
        r1.font.color.rgb = DARK_SLATE
        r2 = p.add_run()
        r2.text = b_text
        r2.font.size = Pt(13.5)
        r2.font.color.rgb = DARK_SLATE

    # Right Card: Training Highlights
    add_card(s11, Inches(8.0), Inches(1.5), Inches(4.5), Inches(5.3), bg_color=PEACH_BG, border_color=PEACH_BORDER)
    r11_box = s11.shapes.add_textbox(Inches(8.2), Inches(1.7), Inches(4.1), Inches(4.9))
    r11_tf = r11_box.text_frame
    r11_tf.word_wrap = True
    p11_h = r11_tf.paragraphs[0]
    p11_h.text = "Training Specifications"
    p11_h.font.size = Pt(16)
    p11_h.font.bold = True
    p11_h.font.color.rgb = ORANGE

    specs = [
        ("Total Training Data: ", "35,918 articles"),
        ("Total Test Data: ", "8,980 articles"),
        ("Vocabulary Size: ", "5,000 Unigram & Bigram Features"),
        ("Sublinear TF Scaling: ", "Dampens repeated spam keywords"),
        ("Prediction Speed: ", "SVM: ~0.6ms | LR: ~1.2ms | RF: ~40ms"),
        ("Consensus Voting: ", "Majority rule across all 3 models")
    ]
    for s_lead, s_val in specs:
        p = r11_tf.add_paragraph()
        p.space_before = Pt(11)
        r1 = p.add_run()
        r1.text = "•  " + s_lead
        r1.font.bold = True
        r1.font.size = Pt(12.5)
        r1.font.color.rgb = DARK_SLATE
        r2 = p.add_run()
        r2.text = s_val
        r2.font.size = Pt(11.5)
        r2.font.color.rgb = DARK_SLATE

    # =========================================================================
    # SLIDE 12: MODEL EVALUATION (Clean Table + Charts)
    # =========================================================================
    s12 = prs.slides.add_slide(blank_layout)
    add_header(s12, "Model Evaluation")

    # Clean Table
    table_shape = s12.shapes.add_table(5, 7, Inches(0.8), Inches(1.35), Inches(11.7), Inches(1.8))
    table = table_shape.table

    col_widths = [Inches(2.5), Inches(1.5), Inches(1.5), Inches(1.5), Inches(1.5), Inches(1.7), Inches(1.5)]
    for idx, w in enumerate(col_widths):
        table.columns[idx].width = w

    headers = ["Model", "Accuracy", "Precision", "Recall", "F1-Score", "Headline Acc.", "Status"]
    for idx, h in enumerate(headers):
        cell = table.cell(0, idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        cell.text = h
        p = cell.text_frame.paragraphs[0]
        p.font.name = "Calibri"
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = WHITE
        p.alignment = PP_ALIGN.CENTER if idx > 0 else PP_ALIGN.LEFT

    rows_data = [
        ("Linear SVM", "99.07%", "98.60%", "99.46%", "99.03%", "94.94%", "Active Primary"),
        ("Random Forest", "98.98%", "98.84%", "99.02%", "98.93%", "94.20%", "Evaluated"),
        ("Logistic Regression", "98.71%", "98.42%", "98.88%", "98.65%", "93.80%", "Evaluated"),
        ("Consensus Ensemble", "99.12%", "98.90%", "99.35%", "99.12%", "95.10%", "Consensus Meta"),
    ]
    for r_idx, r_vals in enumerate(rows_data):
        for c_idx, val in enumerate(r_vals):
            cell = table.cell(r_idx + 1, c_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = PEACH_BG if r_idx == 0 else (CARD_BG if r_idx % 2 == 1 else WHITE)
            cell.text = val
            p = cell.text_frame.paragraphs[0]
            p.font.name = "Calibri"
            p.font.size = Pt(11)
            p.font.bold = (c_idx == 0 or r_idx == 0 or c_idx == 4)
            p.font.color.rgb = ORANGE if (r_idx == 0 and c_idx == 0) else DARK_SLATE
            p.alignment = PP_ALIGN.CENTER if c_idx > 0 else PP_ALIGN.LEFT

    # Bottom Charts
    comp_chart_p = os.path.join(PROJECT_DIR, "chart_model_comparison.png")
    cm_chart_p = os.path.join(PROJECT_DIR, "chart_confusion_matrix.png")

    if os.path.exists(comp_chart_p):
        s12.shapes.add_picture(comp_chart_p, Inches(0.8), Inches(3.45), width=Inches(6.6))
    if os.path.exists(cm_chart_p):
        s12.shapes.add_picture(cm_chart_p, Inches(7.7), Inches(3.45), width=Inches(4.8))

    # =========================================================================
    # SLIDE 13: RESULTS AND OUTPUT SCREENSHOTS (2 Clear UI Figures)
    # =========================================================================
    s13 = prs.slides.add_slide(blank_layout)
    add_header(s13, "Results and Output Screenshots")

    scr1_p = os.path.join(PROJECT_DIR, "ui_screenshot_detection.png")
    if os.path.exists(scr1_p):
        s13.shapes.add_picture(scr1_p, Inches(0.8), Inches(1.4), width=Inches(5.6))
        c1_box = s13.shapes.add_textbox(Inches(0.8), Inches(6.05), Inches(5.6), Inches(0.9))
        c1_tf = c1_box.text_frame
        c1_tf.word_wrap = True
        p1 = c1_tf.paragraphs[0]
        p1.text = "Figure 1: Live News Analyzer - 0-100% Credibility Speedometer, Multi-Model Consensus, and Linguistic Signals."
        p1.font.size = Pt(11)
        p1.font.bold = True
        p1.font.color.rgb = DARK_SLATE

    scr2_p = os.path.join(PROJECT_DIR, "ui_screenshot_performance.png")
    if os.path.exists(scr2_p):
        s13.shapes.add_picture(scr2_p, Inches(6.9), Inches(1.4), width=Inches(5.6))
        c2_box = s13.shapes.add_textbox(Inches(6.9), Inches(6.05), Inches(5.6), Inches(0.9))
        c2_tf = c2_box.text_frame
        c2_tf.word_wrap = True
        p2 = c2_tf.paragraphs[0]
        p2.text = "Figure 2: Performance Dashboard - Live Evaluator, Dynamic Confusion Matrix, and Real-Time Evaluation Table."
        p2.font.size = Pt(11)
        p2.font.bold = True
        p2.font.color.rgb = DARK_SLATE

    # =========================================================================
    # SLIDE 14: CONCLUSION AND FUTURE SCOPE (Two Simple Cards)
    # =========================================================================
    s14 = prs.slides.add_slide(blank_layout)
    add_header(s14, "Conclusion and Future Scope")

    # Conclusion Card
    add_card(s14, Inches(0.8), Inches(1.5), Inches(5.6), Inches(5.3), bg_color=CARD_BG, border_color=CARD_BORDER)
    c_box14 = s14.shapes.add_textbox(Inches(1.1), Inches(1.7), Inches(5.0), Inches(4.9))
    c_tf14 = c_box14.text_frame
    c_tf14.word_wrap = True
    p_c_h = c_tf14.paragraphs[0]
    p_c_h.text = "Conclusion"
    p_c_h.font.size = Pt(18)
    p_c_h.font.bold = True
    p_c_h.font.color.rgb = NAVY

    conclusions = [
        ("High Detection Accuracy: ", "Achieved 99.07% accuracy using Linear SVM on 44,898 benchmark articles."),
        ("Multi-Model Redundancy: ", "Combining 3 distinct algorithms eliminates bias and prevents false alarms."),
        ("Explainable Output: ", "The 0-100% Credibility Speedometer makes verdicts easy for everyone to understand."),
        ("Dynamic Evaluation: ", "Live performance dashboard recalculates metrics dynamically as new news is tested."),
        ("Fast Web Platform: ", "Delivered a working web app with sub-second response times (<40ms).")
    ]
    for b_lead, b_text in conclusions:
        p = c_tf14.add_paragraph()
        p.space_before = Pt(12)
        r1 = p.add_run()
        r1.text = "•  " + b_lead
        r1.font.bold = True
        r1.font.size = Pt(13)
        r1.font.color.rgb = DARK_SLATE
        r2 = p.add_run()
        r2.text = b_text
        r2.font.size = Pt(12)
        r2.font.color.rgb = DARK_SLATE

    # Future Scope Card
    add_card(s14, Inches(6.9), Inches(1.5), Inches(5.6), Inches(5.3), bg_color=PEACH_BG, border_color=PEACH_BORDER)
    f_box14 = s14.shapes.add_textbox(Inches(7.2), Inches(1.7), Inches(5.0), Inches(4.9))
    f_tf14 = f_box14.text_frame
    f_tf14.word_wrap = True
    p_f_h = f_tf14.paragraphs[0]
    p_f_h.text = "Future Scope"
    p_f_h.font.size = Pt(18)
    p_f_h.font.bold = True
    p_f_h.font.color.rgb = ORANGE

    futures = [
        ("Regional Indian Languages: ", "Extend pipeline to Telugu, Hindi, and Tamil using IndicBERT models."),
        ("Deepfake Image/Video Detection: ", "Incorporate Computer Vision models to flag manipulated viral videos."),
        ("Browser Extension: ", "Build a one-click Chrome extension to check news directly on Twitter and Facebook."),
        ("WhatsApp Fact-Check Bot: ", "Allow users to forward suspicious messages to a bot for instant verification."),
        ("Knowledge Graph Verification: ", "Cross-check extracted news facts against Google Fact Check API in real time.")
    ]
    for b_lead, b_text in futures:
        p = f_tf14.add_paragraph()
        p.space_before = Pt(12)
        r1 = p.add_run()
        r1.text = "•  " + b_lead
        r1.font.bold = True
        r1.font.size = Pt(13)
        r1.font.color.rgb = DARK_SLATE
        r2 = p.add_run()
        r2.text = b_text
        r2.font.size = Pt(12)
        r2.font.color.rgb = DARK_SLATE

    # =========================================================================
    # SLIDE 15: REFERENCES
    # =========================================================================
    s15 = prs.slides.add_slide(blank_layout)
    add_header(s15, "References")

    ref_box = s15.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(11.7), Inches(5.4))
    tf15 = ref_box.text_frame
    tf15.word_wrap = True

    references = [
        ("1. ", "H. Ahmed, I. Traore, and S. Saad, ", "\"Detection of Online Fake News Using N-Gram Analysis and Machine Learning Techniques,\" ", "Intelligent, Secure, and Dependable Systems, Springer, 2017."),
        ("2. ", "S. Vosoughi, D. Roy, and S. Aral, ", "\"The spread of true and false news online,\" ", "Science, vol. 359, no. 6380, pp. 1146-1151, Mar. 2018."),
        ("3. ", "F. Pedregosa et al., ", "\"Scikit-learn: Machine Learning in Python,\" ", "Journal of Machine Learning Research, vol. 12, pp. 2825-2830, 2011."),
        ("4. ", "V. Perez-Rosas et al., ", "\"Automatic Detection of Fake News,\" ", "Proceedings of the 27th International Conference on Computational Linguistics (COLING), pp. 3391-3401, 2018."),
        ("5. ", "C. Castillo, M. Mendoza, and B. Poblete, ", "\"Information Credibility on Twitter,\" ", "Proceedings of the 20th International Conference on World Wide Web (WWW), pp. 675-684, 2011.")
    ]
    for idx, (num, authors, title, venue) in enumerate(references):
        p = tf15.paragraphs[0] if idx == 0 else tf15.add_paragraph()
        p.space_after = Pt(16)

        r_num = p.add_run()
        r_num.text = num
        r_num.font.bold = True
        r_num.font.size = Pt(14)
        r_num.font.color.rgb = ORANGE

        r_auth = p.add_run()
        r_auth.text = authors
        r_auth.font.bold = True
        r_auth.font.size = Pt(13)
        r_auth.font.color.rgb = DARK_SLATE

        r_tit = p.add_run()
        r_tit.text = title
        r_tit.font.italic = True
        r_tit.font.size = Pt(13)
        r_tit.font.color.rgb = NAVY

        r_ven = p.add_run()
        r_ven.text = venue
        r_ven.font.size = Pt(12)
        r_ven.font.color.rgb = MUTED_SLATE

    # =========================================================================
    # SLIDE 16: THANK YOU (Clean & Balanced Closing)
    # =========================================================================
    s16 = prs.slides.add_slide(blank_layout)
    set_white_bg(s16)

    # Center Logo
    if os.path.exists(TITLE_LOGO):
        s16.shapes.add_picture(TITLE_LOGO, Inches(4.35), Inches(0.9), width=Inches(4.63))

    # Thank You Heading
    ty_box = s16.shapes.add_textbox(Inches(1.0), Inches(2.2), Inches(11.333), Inches(1.1))
    tf16 = ty_box.text_frame
    p16 = tf16.paragraphs[0]
    p16.text = "Thank You!"
    p16.alignment = PP_ALIGN.CENTER
    p16.font.name = "Calibri"
    p16.font.size = Pt(44)
    p16.font.bold = True
    p16.font.color.rgb = ORANGE

    # Q&A Subtitle
    qa_box = s16.shapes.add_textbox(Inches(1.0), Inches(3.45), Inches(11.333), Inches(0.5))
    p_qa = qa_box.text_frame.paragraphs[0]
    p_qa.text = "Questions & Answers  |  Open for Discussion"
    p_qa.alignment = PP_ALIGN.CENTER
    p_qa.font.name = "Calibri"
    p_qa.font.size = Pt(17)
    p_qa.font.bold = True
    p_qa.font.color.rgb = NAVY

    # Project Info Card
    card_ty_w = Inches(8.5)
    card_ty_h = Inches(2.5)
    card_ty_x = (prs.slide_width - card_ty_w) / 2
    card_ty_y = Inches(4.2)
    add_card(s16, card_ty_x, card_ty_y, card_ty_w, card_ty_h, bg_color=CARD_BG, border_color=CARD_BORDER)

    info_box = s16.shapes.add_textbox(card_ty_x, card_ty_y + Inches(0.2), card_ty_w, card_ty_h - Inches(0.4))
    info_tf = info_box.text_frame
    info_tf.word_wrap = True

    p_proj = info_tf.paragraphs[0]
    p_proj.text = "Fake News Detection System Using Machine Learning and NLP"
    p_proj.alignment = PP_ALIGN.CENTER
    p_proj.font.bold = True
    p_proj.font.size = Pt(15)
    p_proj.font.color.rgb = DARK_SLATE

    p_dept = info_tf.add_paragraph()
    p_dept.space_before = Pt(6)
    p_dept.text = "Department of Artificial Intelligence & Machine Learning (AIML)"
    p_dept.alignment = PP_ALIGN.CENTER
    p_dept.font.bold = True
    p_dept.font.size = Pt(13.5)
    p_dept.font.color.rgb = ORANGE

    p_univ = info_tf.add_paragraph()
    p_univ.text = "Aditya University, Surampalem, Andhra Pradesh"
    p_univ.alignment = PP_ALIGN.CENTER
    p_univ.font.size = Pt(12.5)
    p_univ.font.color.rgb = MUTED_SLATE

    p_team = info_tf.add_paragraph()
    p_team.space_before = Pt(8)
    p_team.text = "Team: P. Nehasri | M. Nithin | K. Vikas | R. Pranathi | Y. Chakradhar"
    p_team.alignment = PP_ALIGN.CENTER
    p_team.font.bold = True
    p_team.font.size = Pt(12)
    p_team.font.color.rgb = NAVY

    p_guide = info_tf.add_paragraph()
    p_guide.text = "Guide: P. Venkata Bala Annapurna, M.Tech (Ph.D), Asst. Prof, AIML Dept"
    p_guide.alignment = PP_ALIGN.CENTER
    p_guide.font.size = Pt(11.5)
    p_guide.font.color.rgb = DARK_SLATE

    prs.save(OUTPUT_PPTX)
    print("New simplified presentation successfully saved to:", OUTPUT_PPTX)

if __name__ == "__main__":
    build_presentation()
