# Personal Archive UI Design

Date: 2026-06-17  
Status: Draft  
Scope: Home, Profile, Report

## 1. Problem Statement

The product is being narrowed into a `personal archive-style fortune-telling tool`.

The current UI must stop feeling like a multi-entry workbench and become a single, clear delivery flow:

`basic input -> personal data card -> analysis report -> PDF / PNG delivery -> manual annotation`

This spec defines the front-end information architecture and page layout for that flow.

## 2. Goals

1. Make the homepage only responsible for input and preview.
2. Make the profile page the only standard archive editor.
3. Make the report page look and behave like a formal deliverable.
4. Use one visual language across all three pages.
5. Ensure report previews and PDF exports share the same chapter structure.
6. Preserve the existing computation logic and existing route structure.

## 3. Non-Goals

This phase does not do:

- Chat-style interaction
- Community or social features
- Entertainment-style landing pages
- A full rewrite of the domain calculation engines
- Dense dashboard or workbench patterns

## 4. Design Principles

1. Summary first.
2. Structure second.
3. Explanation last.
4. Keep one primary action per page.
5. Show only archive-relevant data in the archive flow.
6. Keep report content readable as a printed document.
7. Keep page previews and exported files visually aligned.

## 5. Page System

### 5.1 Home

#### Purpose

The home page is the entry point. It must help the user complete initial input and generate the archive card.

#### Layout

- Top hero area
- Left input column
- Right preview column
- Bottom action area

#### Left Column

- Basic information
- Time settings
- Birthplace and current location
- Current concern and history notes

#### Right Column

- Personal data card
- Time confidence
- Archive completeness
- Recent save state
- Real-world tags

#### Actions

- Primary: `Generate archive and enter report`
- Secondary: `Save draft`
- Secondary: `Go to archive`

#### Removed from Home

- Full Bazi analysis
- Full Ziwei analysis
- Full name analysis
- Workbench-style extra entry points

### 5.2 Profile

#### Purpose

The profile page is the single source of truth for structured personal archive data.

#### Layout

- Top explanation block
- Main editor area
- Sticky summary card on the right
- Bottom save / reset / go-to-report actions

#### Editor Sections

- Basic information
- Time and location
- Current residence
- Analysis preferences
- Historical events

#### Summary Card

- Archive completeness
- Time confidence
- Current focus
- Key tags
- Missing fields

#### Actions

- Save
- Reset
- Go to report

#### Removed from Profile

- Detailed analysis bodies
- Export controls
- Duplicate report content
- Workbench-like tools

### 5.3 Report

#### Purpose

The report page is the formal deliverable and PDF preview.

#### Layout

- Left chapter navigation
- Center report body
- Right summary / warning / annotation rail

#### Report Chapters

1. Cover
2. Table of contents
3. Personal archive
4. Timeline
5. Bazi overview
6. Ziwei overview
7. Name analysis
8. Integrated summary
9. Manual annotation area
10. Appendix and disclaimer

#### Right Rail

- Proactive warnings
- Current chapter summary
- Annotation space
- Export status

#### Actions

- Export PDF
- Export PNG
- Share

#### Removed from Report

- Input forms
- Workbench panels
- Debug output
- Temporary tool cards that do not belong in the final report

## 6. Content Grammar

All three pages and all report chapters must follow the same structure:

1. Summary
2. Structure
3. Explanation

This applies to:

- Home preview cards
- Profile summary cards
- Report sections

## 7. Visual System

### Color Direction

- Warm off-white
- Sand gold
- Deep ink
- Muted teal

### Semantic Color Use

- Gold: primary state
- Teal: normal state
- Red: risk or warning only

### Tone

- Archive-like
- Report-like
- Paper-like
- Calm
- Trustworthy

### Avoid

- Neon purple
- Fantasy glow
- Entertainment illustration
- Dense portal-style layouts

## 8. Component Boundaries

### Home Components

- Hero block
- Form panel
- Preview card
- Action bar

### Profile Components

- Hero block
- Editor panel
- Summary card
- Actions panel

### Report Components

- Layout shell
- Top bar
- Cover
- Summary block
- Chapter renderer
- Chapter navigation
- Annotation rail

## 9. Responsive Behavior

### Desktop

- Home uses a two-column layout with the preview kept visible.
- Profile uses a two-column layout with the summary sticky.
- Report uses a three-column layout for navigation, body, and side rail.

### Mobile

- Home becomes stacked: input first, preview second.
- Profile becomes stacked: editor first, summary second.
- Report becomes stacked with chapter navigation collapsed into a compact control.

## 10. Acceptance Criteria

1. Home shows input and preview only.
2. Profile is the only archive editing center.
3. Report looks like a formal deliverable.
4. All pages use one visual language.
5. Report preview and PDF follow the same chapter order.
6. Time axis and proactive warnings are visible in the report.
7. Manual annotation space is preserved.
8. Existing computation logic is not rewritten.
9. Existing core routes remain usable.

## 11. Implementation Boundary

This design is limited to the front-end page architecture and presentation layer.

It intentionally does not prescribe:

- New calculation algorithms
- New backend domain models
- Social or community features
- Subscription or account systems

## 12. Recommended Next Step

If this design is approved, the next step is to turn it into a concrete implementation plan for:

1. Home layout rewrite
2. Profile layout rewrite
3. Report layout rewrite
4. Preview and PDF alignment
