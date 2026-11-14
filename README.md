# Secure Translator Pro

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)]()

> **AI-Powered Desktop Translation Application** with 4-agent architecture, glossary management, document processing, and configurable cloud/local models.

---

## العربية 🇪🇬

### نظرة عامة

Secure Translator Pro هو تطبيق سطح مكتب متقدم لترجمة النصوص والمستندات بالذكاء الاصطناعي. يستخدم التطبيق نظام **4 وكلاء متخصصين** (Multi-Agent) لضمان أعلى جودة ترجمة، مع دعم لكل من التشغيل المحلي والسحابي ونماذج قابلة للتخصيص.

### ✨ المميزات الرئيسية

| الميزة | الوصف |
|--------|-------|
| 🤖 **نظام 4 وكلاء متقدم** | pipeline رباعي المراحل: تحليل الأسلوب → الترجمة → المراجعة → الخبير الثقافي |
| ☁️💻 **تشغيل محلي وسحابي** | دعم LM Studio محلياً وGoogle Gemini سحابياً مع اختيار النموذج |
| 🧠 **تحليل أسلوب المستند** | وكيل مخصص يحلل نبرة النص وأسلوبه مرة واحدة قبل البدء في الترجمة |
| 📚 **إدارة القواميس الذكية** | فلترة تلقائية للمصطلحات — بس اللي في القطعة الحالية بتدخل للـ prompt |
| 🌐 **دعم 5 لغات** | English, Arabic, French, German, Spanish |
| 📄 **معالجة المستندات** | دعم ملفات Word (.docx) مع تنسيق RTL للعربية |
| 🌙 **الوضع الليلي / النهاري** | واجهة أنيقة مع دعم كامل لتبديل الثيمات |
| ⚡ **استرداد ذكي** | لو وكيل واحد فشل، التطبيق بيحاول يستخدم نتيجة الوكيل اللي قبله |
| 🔒 **خصوصية كاملة** | التشغيل المحلي يضمن بقاء بياناتك على جهازك |

### 🏗️ البنية التقنية

```
secure-translator-pro/
├── core/                  # محرك الترجمة والوكلاء
│   ├── agents.py          # نظام الوكلاء الأربعة (Style Profiler, Drafting, Critic, Cultural)
│   ├── engine.py          # محرك الترجمة مع تقسيم ذكي للنصوص و RTL support
│   └── logging_helper.py  # نظام تسجيل متقدم مع تدوير الملفات
├── ui/                    # واجهة المستخدم
│   ├── main_window.py     # النافذة الرئيسية والتبويبات
│   ├── sidebar.py         # الشريط الجانبي للتنقل
│   ├── theme.py           # نظام الثيمات (داكن/فاتح)
│   ├── icon_factory.py    # إنشاء الأيقونات برمجياً
│   └── tabs/              # تبويبات التطبيق
│       ├── translation_tab.py
│       ├── glossary_tab.py
│       ├── settings_tab.py
│       └── about_tab.py
├── data/                  # إدارة البيانات
│   ├── config.py          # مدير الإعدادات مع دمج تلقائي
│   └── database.py        # مدير القواميس (SQLite)
├── docs/                  # التوثيق
│   └── DESIGN_SYSTEM.md   # دليل نظام التصميم الكامل
└── main.py                # نقطة الدخول الرئيسية
```

### 📋 المتطلبات

- **Python 3.10** أو أحدث
- مكتبات Python المذكورة في `requirements.txt`

### 🚀 التثبيت

1. **استنساخ المستودع:**
   ```bash
   git clone <repository-url>
   cd secure-translator-pro-phase3
   ```

2. **إنشاء بيئة افتراضية (موصى به):**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate        # Windows
   source .venv/bin/activate     # macOS / Linux
   ```

3. **تثبيت المكتبات:**
   ```bash
   pip install -r requirements.txt
   ```

4. **تشغيل التطبيق:**
   ```bash
   python main.py
   ```

### ⚙️ الإعدادات

بعد التشغيل الأول، يمكنك تكوين التطبيق من تبويب الإعدادات:

- **وضع المحرك:** محلي (LM Studio) أو سحابي (Google Gemini)
- **إعدادات LM Studio:** عنوان الخادم، اسم النموذج، مهلة الاتصال، عدد إعادة المحاولة
- **إعدادات Google Gemini:** مفتاح API، اختيار النموذج (2.5 Flash, 2.5 Pro, 2.0 Flash)
- **لغات الترجمة:** اللغة المصدر واللغة الهدف (5 لغات مدعومة)
- **مجلد الإخراج:** مسار مخصص للملفات المترجمة
- **مجلد الأرشيف:** مسار مخصص للملفات الأصلية بعد المعالجة

### 🔧 التشغيل المحلي مع LM Studio

1. حمّل [LM Studio](https://lmstudio.ai/) وثبته
2. حمّل نموذج دعم الترجمة (مثل Llama 3، Mistral، etc.)
3. شغّل خادم API المحلي
4. فعّل وضع "محلي" في إعدادات التطبيق

### 📖 نظام الوكلاء الأربعة

يعمل التطبيق بأربعة وكلاء متخصصين بالتسلسل:

1. **وكيل تحليل الأسلوب (Style Profiler)** — يُشغَّل مرة واحدة في البداية لتحليل نبرة النص وأسلوبه وسرديته، ويُنشئ "دليل أسلوب" يُطبق على جميع القطع
2. **وكيل المسودة** — يقوم بالترجمة الأولى مع الالتزام بالقاموس المخصص والسياق
3. **وكيل المراجعة** — يراجع الترجمة للتحقق من الدقة والسلاسة والأسلوب الأدبي ومقارنتها بالنص الأصلي
4. **الخبير الثقافي** — يضمن أن النص المترجم يحافظ على التأثير العاطفي والثقافي الأصلي مع تمييز أصوات الشخصيات

### 📄 معالجة الملفات

- **الإدخال:** ملفات نصية (.txt) مع دعم تلقائي لـ UTF-8-sig, UTF-8, CP1256
- **الإخراج:** مستندات Word (.docx) مع تنسيق RTL للعربية والحفاظ على الفقرات
- **الأرشيف:** يتم نقل الملفات الأصلية تلقائياً بعد الترجمة لمنع المعالجة المكررة
- **الاسترداد الذكي:** لو الوكيل الرابع فشل في التحقق، التطبيق بيستخدم نتيجة الوكيل الثالث أو الثاني لو كانت مقبولة

---

## English 🇬🇧

### Overview

**Secure Translator Pro** is an advanced desktop application for AI-powered text and document translation. It employs a **4-agent architecture** to ensure the highest quality translations, supporting both local and cloud-based LLM inference with configurable models.

### ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🤖 **4-Agent Pipeline** | Four-stage workflow: Style Profiling → Drafting → Critiquing → Cultural Expert |
| ☁️💻 **Local & Cloud Support** | Works with LM Studio locally or Google Gemini in the cloud with model selection |
| 🧠 **Document Style Analysis** | Dedicated agent analyzes text tone and style once before translation begins |
| 📚 **Smart Glossary Filtering** | Only glossary terms present in each chunk are injected into prompts |
| 🌐 **5 Languages Supported** | English, Arabic, French, German, Spanish |
| 📄 **Document Processing** | Full Word (.docx) output with RTL formatting for Arabic text |
| 🌙 **Dark / Light Theme** | Elegant UI with seamless theme switching |
| ⚡ **Smart Recovery** | If the final agent fails validation, falls back to earlier valid stages |
| 🔒 **Full Privacy** | Local mode ensures your data never leaves your machine |

### 🏗️ Architecture

```
secure-translator-pro/
├── core/                  # Translation engine & agents
│   ├── agents.py          # Four-agent system (Style Profiler, Drafting, Critic, Cultural)
│   ├── engine.py          # Main translation engine with smart chunking & RTL support
│   └── logging_helper.py  # Advanced logger with file rotation
├── ui/                    # User interface
│   ├── main_window.py     # Main window and tab management
│   ├── sidebar.py         # Navigation sidebar
│   ├── theme.py           # Dark/Light theming system
│   ├── icon_factory.py    # Programmatic icon generation
│   └── tabs/              # Application tabs
│       ├── translation_tab.py
│       ├── glossary_tab.py
│       ├── settings_tab.py
│       └── about_tab.py
├── data/                  # Data management
│   ├── config.py          # Configuration manager with auto-merge
│   └── database.py        # Glossary manager (SQLite)
├── docs/                  # Documentation
│   └── DESIGN_SYSTEM.md   # Complete Design System guide
└── main.py                # Application entry point
```

### 📋 Requirements

- **Python 3.10** or later
- Python dependencies listed in `requirements.txt`

### 🚀 Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd secure-translator-pro-phase3
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate        # Windows
   source .venv/bin/activate     # macOS / Linux
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```

### ⚙️ Configuration

After the first run, configure the app from the Settings tab:

- **Engine Mode:** Local (LM Studio) or Cloud (Google Gemini)
- **LM Studio Settings:** Server URL, Model name, Timeout, Max retries
- **Google Gemini Settings:** API key, Model selection (2.5 Flash, 2.5 Pro, 2.0 Flash)
- **Translation Languages:** Source and target languages (5 supported)
- **Output Directory:** Custom path for translated files
- **Archive Directory:** Custom path for original files after processing

### 🔧 Local Setup with LM Studio

1. Download and install [LM Studio](https://lmstudio.ai/)
2. Load a translation-capable model (e.g., Llama 3, Mistral)
3. Start the local API server
4. Set mode to "Local" in the app settings

### 📖 Four-Agent System

The application processes text through four specialized agents sequentially:

1. **Style Profiler Agent** — Runs ONCE at the start to analyze document tone, narrative voice, and style; produces a blueprint applied across all chunks
2. **Drafting Agent** — Produces the initial translation following glossary constraints and context
3. **Critic Agent** — Reviews against the original source text for accuracy, flow, elegance, and natural prose
4. **Cultural Expert Agent** — Ensures emotional and cultural resonance with character voice distinction (polyphony)

### 📄 File Processing

- **Input:** Text files (.txt) with automatic encoding detection (UTF-8-sig → UTF-8 → CP1256)
- **Output:** Word documents (.docx) with RTL formatting for Arabic and paragraph preservation
- **Archive:** Original files are automatically moved to prevent re-processing
- **Smart Recovery:** If the final agent fails validation, falls back to earlier valid stages

---

## 🛠️ Development

### Project Structure

| Directory | Purpose |
|-----------|---------|
| `core/` | Core translation logic, 4-agent orchestration, logging |
| `ui/` | CustomTkinter-based GUI components and tabs |
| `data/` | Configuration management, SQLite database operations |
| `docs/` | Design System documentation and guides |
| `build/` | Build artifacts (executable generation) |

### Building Executable

```bash
python build_app.py
```

This uses PyInstaller via the `SecureTranslatorPro.spec` spec file to create a standalone executable.

---

## 📝 License

This project is for internal use. All rights reserved.

---

## 👨‍💻 Author

**Hazem Kamal Sharaf**

- GitHub: [@hazemkamalsharaf-png](https://github.com/hazemkamalsharaf-png)
