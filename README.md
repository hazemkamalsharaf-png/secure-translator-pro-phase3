# Secure Translator Pro

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)]()

> **AI-Powered Desktop Translation Application** with multi-agent architecture, glossary management, and document processing.

---

## العربية 🇪🇬

### نظرة عامة

Secure Translator Pro هو تطبيق سطح مكتب متقدم لترجمة النصوص والمستندات بالذكاء الاصطناعي. يستخدم التطبيق نظام وكلاء متعددين (Multi-Agent) لضمان أعلى جودة ترجمة، مع دعم لكل من التشغيل المحلي والسحابي.

### ✨ المميزات الرئيسية

| الميزة | الوصف |
|--------|-------|
| 🤖 **نظام الوكلاء المتعددين** |pipeline ثلاثي المراحل: الترجمة → المراجعة → الخبير الثقافي |
| 💻 **تشغيل محلي وسحابي** | دعم LM Studio محلياً وGoogle Gemini سحابياً |
| 📚 **إدارة القواميس** | مصطلحات مخصصة محفوظة في قاعدة بيانات SQLite |
| 📄 **معالجة المستندات** | دعم ملفات Word (.docx) وExcel (.xlsx) |
| 🌙 **الوضع الليلي / النهاري** | واجهة أنيقة مع دعم كامل لتبديل الثيمات |
| ⚡ **معالجة الدفعات** | تقسيم النصوص الطويلة إلى أجزاء ومعالجتها بالتوازي |
| 🔒 **خصوصية كاملة** | التشغيل المحلي يضمن بقاء بياناتك على جهازك |

### 🏗️ البنية التقنية

```
secure-translator-pro/
├── core/                  # محرك الترجمة والوكلاء
│   ├── agents.py          # نظام الوكلاء الثلاثة (مسودة، مراجعة، ثقافي)
│   ├── engine.py          # محرك الترجمة الرئيسي مع تقسيم النصوص
│   └── logging_helper.py  # نظام تسجيل متقدم مع تدوير الملفات
├── ui/                    # واجهة المستخدم
│   ├── main_window.py     # النافذة الرئيسية والتبويبات
│   ├── sidebar.py         # الشريط الجانبي للتنقل
│   ├── theme.py           # نظام الثيمات (داكن/فاتح)
│   ├── icon_factory.py    # إنشاء الأيقونات برمجياً
│   └── tabs/              # تبويبات التطبيق
│       ├── translation_tab.py
│       ├── glossary_tab.py
│       └── settings_tab.py
├── data/                  # إدارة البيانات
│   ├── config.py          # مدير الإعدادات مع دمج تلقائي
│   └── database.py        # مدير القواميس (SQLite)
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
- **إعدادات Google Gemini:** مفتاح API
- **لغات الترجمة:** اللغة المصدر واللغة الهدف

### 🔧 التشغيل المحلي مع LM Studio

1. حمّل [LM Studio](https://lmstudio.ai/) وثبته
2. حمّل نموذج دعم الترجمة (مثل Llama 3، Mistral، etc.)
3. شغّل خادم API المحلي
4. فعّل وضع "محلي" في إعدادات التطبيق

### 📖 نظام الوكلاء المتعددين

يعمل التطبيق بثلاثة وكلاء متخصصين بالتسلسل:

1. **وكيل المسودة** — يقوم بالترجمة الأولى مع الالتزام بالقاموس المخصص
2. **وكيل المراجعة** — يراجع الترجمة للتحقق من الدقة والسلاسة والأسلوب الأدبي
3. **الخبير الثقافي** — يضمن أن النص المترجم يحافظ على التأثير العاطفي والثقافي الأصلي

### 📄 معالجة الملفات

- **الإدخال:** ملفات نصية (.txt)
- **الإخراج:** مستندات Word (.docx) مع الحفاظ على التنسيق
- **الأرشيف:** يتم نقل الملفات الأصلية تلقائياً بعد الترجمة لمنع المعالجة المكررة

---

## English 🇬🇧

### Overview

**Secure Translator Pro** is an advanced desktop application for AI-powered text and document translation. It employs a multi-agent architecture to ensure the highest quality translations, supporting both local and cloud-based LLM inference.

### ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🤖 **Multi-Agent Pipeline** | Three-stage workflow: Drafting → Critiquing → Cultural Expert |
| 💻 **Local & Cloud Support** | Works with LM Studio locally or Google Gemini in the cloud |
| 📚 **Glossary Management** | Custom terminology stored in a persistent SQLite database |
| 📄 **Document Processing** | Full Word (.docx) and Excel (.xlsx) output support |
| 🌙 **Dark / Light Theme** | Elegant UI with seamless theme switching |
| ⚡ **Batch Processing** | Splits long texts into chunks for efficient translation |
| 🔒 **Full Privacy** | Local mode ensures your data never leaves your machine |

### 🏗️ Architecture

```
secure-translator-pro/
├── core/                  # Translation engine & agents
│   ├── agents.py          # Three-agent system (Draft, Critic, Cultural)
│   ├── engine.py          # Main translation engine with text chunking
│   └── logging_helper.py  # Advanced logger with file rotation
├── ui/                    # User interface
│   ├── main_window.py     # Main window and tab management
│   ├── sidebar.py         # Navigation sidebar
│   ├── theme.py           # Dark/Light theming system
│   ├── icon_factory.py    # Programmatic icon generation
│   └── tabs/              # Application tabs
│       ├── translation_tab.py
│       ├── glossary_tab.py
│       └── settings_tab.py
├── data/                  # Data management
│   ├── config.py          # Configuration manager with auto-merge
│   └── database.py        # Glossary manager (SQLite)
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
- **Google Gemini Settings:** API key
- **Translation Languages:** Source and target languages

### 🔧 Local Setup with LM Studio

1. Download and install [LM Studio](https://lmstudio.ai/)
2. Load a translation-capable model (e.g., Llama 3, Mistral)
3. Start the local API server
4. Set mode to "Local" in the app settings

### 📖 Multi-Agent System

The application processes text through three specialized agents sequentially:

1. **Drafting Agent** — Produces the initial translation following glossary constraints
2. **Critic Agent** — Reviews for accuracy, flow, elegance, and natural English prose
3. **Cultural Expert Agent** — Ensures emotional and cultural resonance matches the original

### 📄 File Processing

- **Input:** Text files (.txt)
- **Output:** Word documents (.docx) with formatting preserved
- **Archive:** Original files are automatically moved to prevent re-processing

---

## 🛠️ Development

### Project Structure

| Directory | Purpose |
|-----------|---------|
| `core/` | Core translation logic, agent orchestration, logging |
| `ui/` | CustomTkinter-based GUI components and tabs |
| `data/` | Configuration management, SQLite database operations |
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