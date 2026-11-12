# 🎨 SecureTranslator Design System

**A production-ready desktop UI design system built on CustomTkinter.**

This document captures the complete visual language, architecture patterns, and reusable component conventions used in **SecureTranslator Pro**. Apply it whenever you build another modern, organized, and polished desktop app.

---

## Table of Contents

1. [Philosophy & Principles](#philosophy--principles)
2. [Architecture Overview](#architecture-overview)
3. [Design Tokens](#design-tokens)
4. [Color System](#color-system)
5. [Typography System](#typography-system)
6. [Spacing & Radius Scale](#spacing--radius-scale)
7. [Layout Patterns](#layout-patterns)
8. [Component Library](#component-library)
9. [Tab/Page Patterns](#tabpage-patterns)
10. [Animation & Interaction](#animation--interaction)
11. [File Structure Convention](#file-structure-convention)
12. [How to Reuse This System](#how-to-reuse-this-system)

---

## Philosophy & Principles

### Core Design Values

| Principle | Description |
|-----------|-------------|
| **Token-Based Everything** | Zero hard-coded colors, sizes, or fonts in widgets. Every value goes through theme tokens. |
| **Card-Centric Layouts** | Content is always grouped into `Card` components with consistent elevation and padding. |
| **Dual Theme Native** | Light & Dark themes are first-class citizens — not an afterthought. Every token has a `(light, dark)` pair. |
| **Component Composition** | Complex UIs are built by composing small, single-responsibility components (`Card`, `Button`, `Badge`, `Toast`). |
| **No Global State Pollution** | Theme is a singleton manager. Tabs don't know about each other. Data layer is isolated from UI layer. |

### Design Language

- **Modern & Clean**: Minimal borders, generous whitespace, soft rounded corners (14px for cards).
- **Professional Palette**: Indigo primary (`#4f46e5` / `#6366f1`), muted secondary text, semantic colors for feedback.
- **Dark Sidebar Contrast**: A persistent dark sidebar (`#10172a` light mode / `#080d1a` dark mode) creates a strong visual anchor regardless of theme.
- **Consistent Elevation**: 3 surface layers — background → surface (cards) → elevated (overlays, toasts).

---

## Architecture Overview

```
main.py
├── main_window.py          ← App shell (grid layout, sidebar + content area)
├── ui/
│   ├── theme.py            ← Design tokens, ThemeManager singleton
│   ├── strings.py          ← UI text catalog (i18n-ready)
│   ├── asset_path.py       ← Dev & PyInstaller path resolution
│   ├── icon_factory.py     ← Programmatic SVG-style icons (Pillow)
│   ├── sidebar.py          ← Navigation sidebar component
│   └── components/         ← Reusable UI primitives
│       ├── card.py         ← Elevated content panel with title + body_frame
│       ├── button.py       ← Primary / Secondary / Danger / Ghost variants
│       ├── badge.py        ← Status indicator (idle, running, done, error...)
│       ├── toast.py        ← Non-blocking notification overlay
│       ├── section_header.py ← Section divider with decorative line
│       └── nav_item.py     ← Sidebar nav item (icon + label, hover/active states)
└── ui/tabs/                ← Each tab = one self-contained class
    ├── translation_tab.py  ← Main workspace (file upload → translate)
    ├── glossary_tab.py     ← Term management (add/search/delete table)
    └── settings_tab.py     ← Configuration (language, engine mode, API keys)
```

### Key Architectural Patterns

1. **Singleton ThemeManager**: `ThemeManager.get_instance()` — provides color tokens, fonts, spacing helpers. Cached CTkFont objects avoid recreation.

2. **Constructor Contract Pattern**: Every component declares its expected constructor signature in a docstring:
   ```python
   # Card(parent, title="Section", padding="md")
   # Button(parent, text="Label", command=cb)
   # TranslationTab(parent, config_manager)
   ```

3. **Transparent Parent Frames**: Container frames use `fg_color="transparent"` to inherit parent background — avoids color mismatch at boundaries.

4. **`token_pair()` Helper**: Returns `(light_color, dark_color)` tuple. CustomTkinter automatically swaps based on `appearance_mode`. This is the single most important pattern in the codebase.

5. **Callback-Based Communication**: Tabs communicate with core logic via callbacks (not direct imports):
   ```python
   progress_callback(current, total, status)
   error_callback(message)
   completion_callback(output_path)
   ```

---

## Design Tokens

### Color System

All colors are defined in `THEMES` dict inside `ui/theme.py`. Each token has a light and dark variant.

#### Surface Colors (Layering Hierarchy)

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `bg` | `#f3f5f9` | `#0b1020` | Main window background |
| `surface` | `#ffffff` | `#141a2e` | Card backgrounds, panels |
| `surface_hover` | `#eef1f7` | `#1c2540` | Hover states, alternating table rows |
| `elevated` | `#ffffff` | `#1a2238` | Overlays, dropdowns |
| `input` | `#f8fafc` | `#0f1528` | Text fields, textboxes |

#### Border Colors

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `border` | `#e2e6ef` | `#2a3554` | Card borders, input borders |
| `border_light` | `#eef1f6` | `#222c48` | Subtle dividers, row separators |

#### Primary / Accent

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `primary` | `#4f46e5` (Indigo 600) | `#6366f1` (Indigo 500) | Primary buttons, progress bars, active states |
| `primary_hover` | `#4338ca` (Indigo 700) | `#818cf8` (Indigo 400) | Button hover states |
| `primary_soft` | `#eef2ff` | `#1e1b4b` | Soft highlighted backgrounds |

#### Semantic Colors

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `success` | `#15803d` (Green 700) | `#4ade80` (Green 400) | Success toasts, confirmation states |
| `warning` | `#b45309` (Amber 700) | `#fbbf24` (Amber 400) | Warning messages, pending states |
| `danger` | `#dc2626` (Red 600) | `#f87171` (Red 400) | Error toasts, danger buttons |
| `danger_hover` | `#b91c1c` (Red 700) | `#fca5a5` (Red 300) | Danger button hover |
| `danger_soft` | `#fef2f2` | `#3f1d24` | Soft error backgrounds |

#### Text Colors

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `text` | `#0f172a` (Slate 900) | `#f8fafc` (Slate 50) | Primary text, headings |
| `text_muted` | `#64748b` (Slate 500) | `#94a3b8` (Slate 400) | Secondary info, hints |
| `text_secondary` | `#748096` | `#7b88a1` | Placeholder text |

#### Sidebar Colors (Dark in Both Themes — Creates Visual Anchor)

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `sidebar_bg` | `#10172a` | `#080d1a` | Sidebar background |
| `sidebar_active` | `#1c2744` | `#1c2744` | Active nav item background |
| `sidebar_hover` | `#172039` | `#121a30` | Nav item hover state |
| `sidebar_icon` | `#94a3b8` | `#94a3b8` | Inactive nav icon color |
| `sidebar_active_icon` | `#ffffff` | `#ffffff` | Active nav icon color |

### Usage Pattern — `token_pair()`

```python
from ui.theme import token_pair, ThemeManager

theme = ThemeManager.get_instance()

# For frames (CustomTkinter swaps based on appearance mode)
frame = ctk.CTkFrame(parent, fg_color=token_pair("surface"))

# For labels (pick one theme explicitly if needed)
label = ctk.CTkLabel(
    parent, 
    text_color=theme.color("text_muted")  # single-theme access
)
```

### Input Style Presets

The codebase ships with ready-made style dicts:

```python
from ui.theme import entry_style, combo_style, radio_style

# Text fields, textboxes
entry_style() → {fg_color, border_color, text_color, placeholder_text_color}

# Combo boxes / dropdowns (adds button colors)
combo_style() → entry_style + {button_color, button_hover_color, dropdown_fg_color, ...}

# Radio buttons
radio_style() → {fg_color, hover_color, border_color, text_color}
```

---

## Typography System

### Font Scale

All sizes are in pixels. Weights: `"normal"` or `"bold"`.

| Token | Size (px) | Weight | Usage Example |
|-------|-----------|--------|---------------|
| `mega` | 28 | bold | Hero / display text |
| `heading` | 24 | bold | Page-level titles |
| `subhead` | 16 | bold | Section headers, top bar title |
| `label` | 13 | normal | Form labels, field headings |
| `body` | 13 | normal | Body text, table content |
| `muted` | 12 | normal | Helper text, hints, placeholders |
| `small` | 11 | normal | Meta info, counters, breadcrumbs |

### Font Family Strategy

```python
# Priority order:
# 1. IBM Plex Sans Arabic (bundled font — works cross-platform)
# 2. Segoe UI (Windows fallback)
# 3. Helvetica Neue (macOS fallback)
# 4. Noto Sans (Linux fallback)
```

### Usage

```python
theme.ctk_font("body")                  # Returns CTkFont(body, 13px, normal)
theme.ctk_font("label", weight="bold")  # Override weight only
theme.ctk_font("subhead")               # Returns CTkFont(subhead, 16px, bold)
```

---

## Spacing & Radius Scale

### Spacing Tokens (used as `pad`, `pady`, `padding` values)

| Token | Value (px) | Usage |
|-------|------------|-------|
| `4` | 4 | Tight gaps between inline elements |
| `8` | 8 | Standard gap between sibling items |
| `12` | 12 | Card row padding, section margins |
| `16` | 16 | Medium spacing — default fallback |
| `20` | 20 | Between card groups |
| `24` | 24 | Side padding for content area |

### Padding Levels (used in Card component)

| Token | Value (px) | Usage |
|-------|------------|-------|
| `sm` | 8 | Compact card content |
| `md` | 14 | Standard card padding |
| `lg` | 20 | Spacious layouts |
| `xl` | 28 | Hero sections, full-width areas |

### Corner Radius Scale

| Token | Value (px) | Usage |
|-------|------------|-------|
| `sm` | 6 | Input fields, small elements |
| `md` | 10 | Medium panels, add forms |
| `lg` | 14 | **Cards — the signature modern radius** |
| `xl` | 20 | Large overlays, modals |

### Progress Bar Radius

Special case: progress bar uses half of its height for a pill shape:
```python
height=8, corner_radius=4  # Always pill-shaped
```

---

## Layout Patterns

### Window Shell (MainWindow)

```
┌─────────────────────────────────────────────────────┐
│ Sidebar (240px fixed) │ Top Bar (title + version)  │
│                       ├────────────────────────────┤
│  📖 Translation       │                            │
│  📚 Glossary          │    Scrollable Body         │
│  ⚙️ Settings          │                            │
│                       │    ┌─ Card (Source File) ─┐│
│  🌗 Theme Toggle      │    ├─ Card (Persona)     ─┤│
│  v2.0                 │    ├─ Card (Progress)    ─┤│
│                       │    └──────────────────────┘│
└─────────────────────────────────────────────────────┘

Min size: 1000×650 | Default: 1280×780
```

### Key Layout Rules

1. **Sidebar**: Fixed width of `240px`, always dark, spans full height. Uses `grid(row=0, column=0, sticky="nsew")`.

2. **Content Area**: Fills remaining space. Contains 3 rows: top bar (60px fixed), divider (1px), body (weight=1).

3. **Top Bar**: Always white surface with title left-aligned and version/app meta right-aligned.

4. **Body Tabs**: Each tab fills the entire body area (`sticky="nsew"`). Only one visible at a time via `grid()`/`grid_remove()`.

5. **Card Content**: Centered within body with max-width constraint (`860px` for settings). Side padding auto-adjusts:
   ```python
   side = max(24, (event.width - 860) // 2)
   ```

### Scroll Pattern

Every tab uses a `CTkScrollableFrame` that fills the body. Content is wrapped in a centered container:
```python
scroll_frame = ctk.CTkScrollableFrame(self, fg_color=token_pair("bg"))
scroll_frame.pack(fill="both", expand=True)

content = ctk.CTkFrame(scroll_frame, fg_color="transparent")
content.pack(fill="x", padx=24, pady=(20, 32))
```

### Form Row Pattern (Settings Tab)

Consistent label-control row layout:
```python
# Frame for the row (fg_color="transparent" to blend)
row = ctk.CTkFrame(card.body_frame, fg_color="transparent")
row.pack(fill="x", pady=(0, 12))  # 12px gap between rows

# Fixed-width label on left (160px)
ctk.CTkLabel(row, text=..., width=160).pack(side="left", padx=(0, 8), pady=4)

# Control fills remaining space
control.pack(side="left", fill="x", expand=True, pady=4)
```

---

## Component Library

### Card Component

**File**: `ui/components/card.py`

The foundational container. Every piece of content lives inside a card.

```python
from ui.components.card import Card

card = Card(
    parent,          # Master widget
    title="Section",  # Optional header text
    padding="md",     # Internal padding: "sm"|"md"|"lg"|"xl"
)
card.grid(row=0, column=0, sticky="ew", pady=(0, 12))

# Use body_frame for child widgets — never pack directly on card
card.body_frame.grid(...)
```

**Visual Design**:
- `corner_radius: 14px` (`theme.radius("lg")`)
- Border width: `1px`, color from `token_pair("border")`
- Background: `token_pair("surface")` (auto-swaps with theme)
- Internal padding via `theme.spacing(padding)`

### Button Variants

**File**: `ui/components/button.py`

```python
from ui.components.button import PrimaryButton, SecondaryButton, DangerButton, GhostButton, DangerGhostButton

# Filled primary button (white text on indigo)
btn = PrimaryButton(parent, text="Start", command=on_start)

# Outlined secondary button (indigo border, white fill)
btn = SecondaryButton(parent, text="Browse", command=browse)

# Filled danger button (red background)
btn = DangerButton(parent, text="Delete", command=delete)

# Ghost button (transparent bg, colored text — hover fills)
btn = GhostButton(parent, text="Reset")

# Danger ghost button (red text/border — hover fills red)
btn = DangerGhostButton(parent, text="Remove")
```

**Design Specs**:
- Height: `36px` standard, `38px` for action buttons in progress cards
- Font: Bold, 13px (`theme.ctk_font("label", weight="bold")`)
- Corner radius: matches theme `sm` (6px) via CTkButton default
- Hover states: defined per variant

### NavItem

**File**: `ui/components/nav_item.py`

Sidebar navigation items with icon + label, hover and active states.

```python
from ui.components.nav_item import NavItem

nav = NavItem(
    sidebar_frame,   # Parent (must be the Sidebar widget)
    icon_name="book",  # Registered icon name
    label="Translation",
    command=callback,
)
nav.pack(fill="x", padx=12, pady=2)
nav.activate()      # Sets active state
nav.deactivate()    # Resets to normal + hover
```

**Design Specs**:
- Height: `44px` per item
- Icon rendered at 40×40 (downsampled from supersampled for sharpness)
- Hover background: `token_pair("sidebar_hover")` — only applies when parent is dark
- Active state: indigo left border (`#6366f1`) + white icon
- Normal state: slate icon color (`#94a3b8`)

### Toast Notifications

**File**: `ui/components/toast.py`

Non-blocking, auto-dismissing notifications. Appears in top-right corner.

```python
from ui.components.toast import Toast

toast = Toast(parent)  # Create once per tab/container

toast.show("Title", "Message body", "success")    # Green
toast.show("Warning", "Something unusual...", "warning")   # Amber
toast.show("Error", "Failed to connect.", "error")     # Red
toast.show("Info", "Processing...", "info")           # Indigo

# Duration: 3 seconds for success/error, 5 seconds for warning/info
```

**Design Specs**:
- Overlay window anchored to top-right of master widget
- Stacks vertically when multiple appear simultaneously
- Icon prefix (✅ success, ⚠️ warning, ❌ error, ℹ️ info)
- Auto-dismiss after configured duration

### Badge / Status Indicator

**File**: `ui/components/badge.py`

Small colored label indicating state.

```python
from ui.components.badge import StatusBadge

badge = StatusBadge(parent, "running")   # or: idle, pending, done, success, error, needs_review
badge.pack(side="right")
```

**Color Mapping**:
| State | Text Color | Background |
|-------|-----------|------------|
| `idle` | muted text | surface_hover |
| `pending` | warning (amber) | surface_hover |
| `running` | primary (indigo) | surface_hover |
| `done` / `success` | success (green) | surface_hover |
| `error` | danger (red) | surface_hover |

### Section Header

**File**: `ui/components/section_header.py`

Decorative divider with title label and subtle bottom line.

```python
from ui.components.section_header import SectionHeader

header = SectionHeader(frame, "Local Model Settings")
header.pack(fill="x", pady=(16, 4))
```

### Icon Factory

**File**: `ui/icon_factory.py`

Programmatic icon generation using Pillow — no PNG assets needed.

- Rendered at 8× supersampling, then downsampled for smooth edges
- Transparent background (works on any surface color)
- Icons defined as SVG-like path functions (`_book`, `_glossary`, `_settings`)
- Output: `CTkImage` objects suitable for CTkLabel

---

## Tab/Page Patterns

### Translation Tab Pattern

```
┌─ Card: Source File ─────────────────────────────┐
│ [No file selected           ] [Browse File]     │
│ File info: 2.3 KB | document.txt                │
└─────────────────────────────────────────────────┘

┌─ Card: Translator Persona / Instructions ───────┐
│ [Reset]                                          │
│ ┌──────────────────────────────────────────────┐│
│ │ You are an elite translator...              ││
│ │ ...                                           ││
│ │                                              ││
│ └──────────────────────────────────────────────┘│
│ Define the translator's role, tone, and rules.  │
└─────────────────────────────────────────────────┘

┌─ Card: Progress ────────────────────────────────┐
│ ████████████░░░░░░░░░░░░░░░░░ (8px pill bar)    │
│ [0 / 12]                        [Cancel] [Start] │
└─────────────────────────────────────────────────┘
```

**Key Patterns**:
- File validation: type check (.txt only), size limit (10MB max)
- Async execution via `threading.Thread` — UI never blocks
- Progress updates dispatched to main thread via `self.after(0, callback)`
- State machine: idle → running → done/error/cancel

### Glossary Tab Pattern

```
┌─ Toolbar ───────────────────────────────────────┐
│ [Search terms...            ] [+ Add Term]      │
└─────────────────────────────────────────────────┘

┌─ Table (scrollable) ────────────────────────────┐
│ TERM              TRANSLATION          [Delete]  │ ← header
│ ├─ Source term ──┼─ Target translation ──────── │
│ │ Source term 2 │ Translation 2           [X]   │ ← alternating bg
│ └───────────────────────────────────────────────┘

┌─ Add Term Form (toggle visible) ────────────────┐
│ Term: [___________] | Translation: [_________] │ [Add]
└─────────────────────────────────────────────────┘
```

**Key Patterns**:
- Real-time search via `StringVar.trace_add("write", ...)`
- Add form toggles visibility (not recreated)
- Empty state message when no entries match
- SQLite database (`glossary.db`) for persistence

### Settings Tab Pattern

```
┌─ Card: Translation ─────────────────────────────┐
│ Source Language: [English ▼]                     │
│ Target Language: [Arabic ▼]                      │
└─────────────────────────────────────────────────┘

┌─ Card: Output & Archive Folders ────────────────┐
│ Output Directory: /path/to/translated  [Browse]  │
│ Archive Directory: /path/to/archived   [Browse]  │
└─────────────────────────────────────────────────┘

┌─ Card: Engine Mode ─────────────────────────────┐
│ ○ Local    ○ Cloud                               │
└─────────────────────────────────────────────────┘

┌─ Card: Local Model Settings (shown when "Local") │
│ Model name: [model-name ▼] [Fetch]              │
│ Server URL: [http://localhost...]               │
│ Timeout:     [120]                               │
│ Max retries: [2]                                 │
└─────────────────────────────────────────────────┘

┌─ Card: Cloud API Settings (shown when "Cloud")  │
│ Provider:    [gemini ▼]                          │
│ API Key:     [••••••••••]         [Show/Hide]   │
└─────────────────────────────────────────────────┘

                    [💾 Save Settings]              ← Save Bar
```

**Key Patterns**:
- Max-width constraint (`860px`) with responsive side padding
- Contextual visibility (local vs cloud cards swap based on engine mode)
- Async model fetching via background thread + `after()` polling
- API key masking with show/hide toggle
- Save status feedback (4-second auto-dismiss toast)

---

## Animation & Interaction

### Button States

Every button variant has 3 states:
1. **Normal**: Default appearance
2. **Hover**: Background fill or border color change
3. **Disabled**: Greyed out, non-interactive (`state="disabled"`)

### Toast Timing

| Type | Auto-dismiss |
|------|-------------|
| Success / Error | 3 seconds |
| Warning / Info | 5 seconds |

### Progress Bar

- Pill-shaped (`height: 8px`, `corner_radius: 4px`)
- Smooth animation via `set(progress)` calls (0.0 → 1.0)
- Color: `token_pair("primary")` — indigo in both themes

### Tab Transitions

Instant switch using `grid()` / `grid_remove()`. No fade or slide animation — clean and snappy.

---

## File Structure Convention

```
project-root/
├── main.py                      # Entry point (thin — sets up paths, loads config)
├── ui/
│   ├── __init__.py
│   ├── theme.py                 # ★ ALL design tokens live here
│   ├── strings.py               # All visible text catalog
│   ├── asset_path.py            # Path resolution (dev + frozen)
│   ├── icon_factory.py          # Programmatic icons
│   ├── main_window.py           # App shell layout
│   ├── sidebar.py               # Navigation panel
│   ├── components/              # Reusable primitives
│   │   ├── __init__.py
│   │   ├── card.py
│   │   ├── button.py
│   │   ├── badge.py
│   │   ├── toast.py
│   │   ├── section_header.py
│   │   └── nav_item.py
│   └── tabs/                    # Feature pages (one class each)
│       ├── __init__.py
│       ├── translation_tab.py
│       ├── glossary_tab.py
│       └── settings_tab.py
├── core/                        # Business logic (no UI imports)
│   ├── engine.py                # Translation orchestration
│   ├── agents.py                # AI agent definitions
│   └── logging_helper.py        # App logger
├── data/                        # Data layer
│   ├── config.py                # JSON config management
│   └── database.py              # SQLite operations
└── docs/
    ├── DESIGN_SYSTEM.md         # ← This file
    └── README.md                # User-facing documentation
```

### Naming Conventions

| Pattern | Example | Used For |
|---------|---------|----------|
| `snake_case` | `file_path_var`, `progress_bar` | Variables, methods |
| `PascalCase` | `ThemeManager`, `TranslationTab` | Classes |
| `_private_method` | `_create_source_card()` | Internal helpers |
| `token_pair("name")` | `fg_color=token_pair("surface")` | Any color value |
| `theme.ctk_font("body")` | — | Font reference |
| `t("key")` | `text=t("trans_start")` | UI strings |

---

## How to Reuse This System

When building a new application with the same style:

### Step 1: Copy the Foundation Files

```
Copy these files verbatim (rename as needed):
├── ui/theme.py              → Your design system entry point
├── ui/strings.py            → Your text catalog  
├── ui/asset_path.py         → Path resolution
├── ui/icon_factory.py       → Icon generation
└── ui/components/           → All component classes

Then customize:
  • THEMES dict in theme.py — change primary color, adjust palette
  • FONTS dict — adjust sizes for your content hierarchy
  • STRINGS in strings.py — replace all UI text
```

### Step 2: Adapt the Layout Shell

```python
# In main_window.py:
SIDEBAR_WIDTH = 240          # Keep or change
TOPBAR_HEIGHT = 60           # Keep or change
geometry("1280x780")         → Your preferred default size
minsize(1000, 650)           → Your minimum size

# Change navigation items in sidebar.py NAV_ITEMS list:
NAV_ITEMS = [
    ("dashboard", "home", "tab_dashboard"),     # New tab
    ("analytics", "chart", "tab_analytics"),    
    ("settings", "settings", "tab_settings"),   
]
```

### Step 3: Create Your Tabs

For each new feature page, follow the pattern:

```python
class MyTab(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=token_pair("bg"))
        
        # 1. Scrollable frame fills area
        scroll = ctk.CTkScrollableFrame(self, fg_color=token_pair("bg"))
        scroll.pack(fill="both", expand=True)
        
        # 2. Content wrapper (centered with side padding)
        content = ctk.CTkFrame(scroll, fg_color="transparent")
        content.pack(fill="x", padx=24, pady=(20, 32))
        
        # 3. Cards for grouping
        card = Card(content, title="Section Title", padding="md")
        card.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        
        # 4. Use token_pair() for ALL colors
        btn = PrimaryButton(card.body_frame, text="Action", command=self.do)

```

### Step 4: Change the Color Palette (Quick Guide)

To rebrand, only modify `THEMES` in `theme.py`:

```python
THEMES = {
    "light": {
        # Keep surface/border/sidebar structure
        # Only change these 2 colors to rebrand:
        "primary":       "#059669",      # Your brand color (green)
        "primary_hover": "#047857",      # Darker shade
        
        # Semantic colors stay the same pattern
        "success":       "#15803d",      
        "warning":       "#b45309",      
        "danger":        "#dc2626",      
    },
    "dark": {
        "primary":       "#34d399",      # Lighter shade for dark mode
        "primary_hover": "#6ee7b7",      
    },
}
```

### Design System Checklist ✅

When building a new screen, verify:

- [ ] Zero hard-coded hex colors — all via `token_pair()` or `theme.color()`
- [ ] All content inside `Card` components (or transparent frames)
- [ ] Buttons use component variants (`PrimaryButton`, etc.)
- [ ] Fonts come from `theme.ctk_font()` scale
- [ ] Spacing uses consistent values (`pady=(0, 12)` pattern)
- [ ] Corner radius follows scale (`sm` for inputs, `lg` for cards)
- [ ] Toast notifications for all user feedback
- [ ] Empty states shown when data is absent
- [ ] Sidebar nav items follow the same hover/active pattern

---

## Quick Reference Card

```
┌─ TOKEN QUICK REFERENCE ─────────────────────────┐
│                                                │
│  Colors:    token_pair("primary")              │
│              theme.color("text_muted")          │
│                                                │
│  Fonts:     theme.ctk_font("body")             │
│              theme.ctk_font("label", bold)      │
│                                                │
│  Spacing:   theme.spacing("8")   → 8px         │
│              theme.pad("md")     → 14px         │
│              theme.radius("lg")  → 14px         │
│                                                │
│  Styles:    entry_style()                      │
│              combo_style()                     │
│              radio_style()                     │
│                                                │
│  Components:Card(parent, title="...")          │
│              PrimaryButton(parent, text="...") │
│              Toast(parent).show(...)           │
│              StatusBadge(parent, "running")    │
│                                                │
└────────────────────────────────────────────────┘
```

---

*This design system was extracted from SecureTranslator Pro (v2.0) and is ready to be reused for any future desktop application that needs a modern, token-based, dual-theme UI.*
