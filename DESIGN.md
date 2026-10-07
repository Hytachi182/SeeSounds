# Design

## Sound Recognition Trainer desktop system

This is an operating interface for focused study rather than a consumer media player. The visual language is calm, compact and legible: a deep blue-green navigation rail anchors a soft warm-neutral workspace, while a restrained teal marks affirmative actions and progress. Error/destructive actions use a clear red.

- Navigation is persistent and text-led; page titles use a strong, direct hierarchy.
- Rounded 8px controls and 14px panels distinguish interaction from study content without turning the application into a grid of decorative cards.
- Large centred prompt panels create a quiet listening moment in Training and Exam modes.
- Secondary controls are low-emphasis pale teal; primary actions are solid teal; destructive actions are red.
- Tables are the primary dense-data surface for the library and per-sound statistics, with readable headers and a search-first workflow.
- Keyboard focus uses a visible teal outline through Qt's native focus handling; disabled and empty states use explicit text rather than color alone.

The app must stay usable at a normal desktop width: the sidebar remains fixed, while page content flexes and tables own their overflow rather than clipping rows.
