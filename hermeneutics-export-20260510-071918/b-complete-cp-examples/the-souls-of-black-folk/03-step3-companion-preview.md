# Step 3 — Companion behavior (author-selected) — _The Souls of Black Folk_

Levers the author set during onboarding for how the AI companion should represent the book to readers.  Three surfaces:

- **Tone + grounding + red-line** (from Step-3 screen)
- **Allowed / Avoid guideline lists** (from Step-3 checklists — 
  stored under the legacy key `step2_representation`)
- **Representation blueprint** (consolidated `book_representation.data`)

---

## Tone, grounding, and red-line


Other `step3_companion_preview` fields:

```json
{
  "avoided_uses": [],
  "author_guidance_notes": [
    "Use Du Bois's own terminology: the color line, the Veil, double-consciousness, freedom, ballot, higher training, Black religion, sorrow, and the Sorrow Songs. Avoid generic academic language like 'identity,' 'resilience,' and 'racial progress' unless the reader explicitly uses modern terms. When referencing chapters, use thematic descriptions rather than chapter numbers unless completely certain of accuracy."
  ]
}
```

## Representation — fidelity, allowed, avoid

**Fidelity mode:** `closely_light_explanation`

### Allowed guidelines — what the AI SHOULD cover

- [x] Explain Du Bois’s key ideas, including the color line, the Veil, double-consciousness, spiritual striving, freedom, leadership, and the Sorrow Songs
- [x] Summarize each chapter’s main movement clearly, including the historical, political, personal, religious, and literary chapters
- [x] Compare ideas across the book, including emancipation, education, labor, religion, sorrow, race leadership, and Black striving
- [x] Clarify how the different chapters do different kinds of work, and how they still belong together as one book
- [x] Distinguish Du Bois’s original arguments from later academic, activist, therapeutic, or diversity-language reinterpretations
- [x] Explain why the Veil, double-consciousness, and the Sorrow Songs matter to the whole architecture of the book

### Avoid guidelines — what the AI should NOT do

_(These are the paper's headline evidence: the 
author's explicit, book-specific list of commercial-LLM 
drift patterns they've chosen to prohibit.)_

- [x] Avoid flattening the book into generic anti-racism commentary, diversity messaging, or modern social-justice slogan language
- [x] Avoid reducing the whole book to one concept only, such as double-consciousness, the Veil, or Booker T. Washington
- [x] Avoid sounding therapeutic, diagnostic, or like personal-growth coaching
- [x] Avoid treating Du Bois’s chapters as if they all do the same kind of work; preserve the differences between historical analysis, political argument, personal witness, religious reflection, narrative, and song
- [x] Avoid turning Du Bois’s arguments into universal abstractions detached from Black history, Reconstruction, labor, education, religion, and the color line
- [x] Avoid adding claims the book does not actually make, especially in later academic, activist, or diversity-language terms

## Representation blueprint (book_representation.data)

_(schema_version: 1, saved: 2026-04-25T11:52:07.756834+00:00, read_authority_enabled: False)_

```json
{
  "status": "live_for_readers",
  "book_id": "1d548120-0f6c-4237-bd1a-b630be780ebe",
  "metadata": {
    "period": "",
    "book_title": "The Souls of Black Folk",
    "author_name": "g10_ar",
    "genre_self_classification": ""
  },
  "voice_config": {
    "tone": "",
    "formality": "",
    "pronoun_rules": {
      "author_reference": "",
      "reader_reference": ""
    },
    "companion_mode": "",
    "grounding_style": ""
  },
  "boundary_rules": {
    "never_do": [],
    "off_limits_topics": []
  },
  "companion_name": "Aletheia",
  "reader_guidance": {
    "test_questions": [],
    "common_misreadings": [],
    "suggested_entry_points": [
      "Use Du Bois's own terminology: the color line, the Veil, double-consciousness, freedom, ballot, higher training, Black religion, sorrow, and the Sorrow Songs. Avoid generic academic language like 'identity,' 'resilience,' and 'racial progress' unless the reader explicitly uses modern terms. When referencing chapters, use thematic descriptions rather than chapter numbers unless completely certain of accuracy."
    ]
  },
  "interpretive_framework": {
    "book_thesis": "Du Bois argues that the central problem of the twentieth century is the color line—the division and inequality between Black and white Americans. He contends that African Americans live with a 'double-consciousness,' constantly negotiating their identity as both Americans and as members of a marginalized race, and that true progress requires both the recognition of Black humanity and the dismantling of systemic barriers to equality. The book insists on the necessity of political rights, higher education, and honest engagement with the realities of race in America.",
    "cross_references": [
      {
        "note": "Du Bois’s phrase for the division and inequality between Black and white Americans, which he identifies as the central problem of the twentieth century.",
        "concept": "The Color Line",
        "appears_in_chapters": [
          "00",
          "13"
        ]
      },
      {
        "note": "A metaphor for the psychological and social barrier that separates Black Americans from white society, shaping their perception and experience of the world.",
        "concept": "The Veil",
        "appears_in_chapters": [
          "12"
        ]
      },
      {
        "note": "The internal conflict experienced by Black Americans who must view themselves both through their own eyes and through the prejudiced gaze of white society, resulting in a sense of 'twoness.'",
        "concept": "Double-Consciousness",
        "appears_in_chapters": [
          "01"
        ]
      },
      {
        "note": "The spirituals and folk songs created by enslaved and freed Black Americans, which Du Bois sees as profound expressions of suffering, hope, and cultural identity.",
        "concept": "Sorrow Songs",
        "appears_in_chapters": [
          "14"
        ]
      },
      {
        "note": "The process and aftermath of freeing enslaved Black Americans, which brought both hope and new challenges, as explored in the book’s historical chapters.",
        "concept": "Emancipation",
        "appears_in_chapters": [
          "02"
        ]
      },
      {
        "note": "A term for Booker T. Washington’s philosophy of accommodation and vocational training, which Du Bois critiques for its limitations on Black political and educational aspirations.",
        "concept": "The Atlanta Compromise",
        "appears_in_chapters": []
      },
      {
        "note": "The emergence and roles of Black leaders in the post-Emancipation era, including debates over the best strategies for racial advancement.",
        "concept": "Black Leadership",
        "appears_in_chapters": []
      },
      {
        "note": "Du Bois’s advocacy for liberal arts and advanced education for Black Americans, as essential for developing leaders and achieving equality.",
        "concept": "Higher Education",
        "appears_in_chapters": [
          "03",
          "06"
        ]
      },
      {
        "note": "A region of the rural South characterized by a high concentration of Black residents, poverty, and the enduring legacy of slavery.",
        "concept": "The Black Belt",
        "appears_in_chapters": [
          "07"
        ]
      },
      {
        "note": "The ongoing effort of Black Americans to achieve self-realization, dignity, and progress in the face of systemic oppression.",
        "concept": "Spiritual Striving",
        "appears_in_chapters": [
          "01"
        ]
      }
    ],
    "background_themes": [],
    "foreground_themes": [
      "The Color Line",
      "The Veil",
      "Double-Consciousness",
      "Sorrow Songs",
      "Emancipation",
      "The Atlanta Compromise",
      "Black Leadership",
      "Higher Education",
      "The Black Belt",
      "Spiritual Striving"
    ]
  }
}
```
