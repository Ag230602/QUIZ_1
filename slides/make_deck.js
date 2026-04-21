const pptxgen = require('pptxgenjs');
const {
  imageSizingContain,
  imageSizingCrop,
  warnIfSlideHasOverlaps,
  warnIfSlideElementsOutOfBounds,
  safeOuterShadow,
} = require('/home/oai/skills/slides/pptxgenjs_helpers');

const path = require('path');

const pptx = new pptxgen();
pptx.layout = 'LAYOUT_WIDE';
pptx.author = 'OpenAI';
pptx.company = 'OpenAI';
pptx.subject = 'Stable Diffusion e-commerce starter kit';
pptx.title = 'Controlled Stable Diffusion for E-Commerce Product Image Generation';
pptx.lang = 'en-US';
pptx.theme = {
  headFontFace: 'Aptos Display',
  bodyFontFace: 'Aptos',
  lang: 'en-US',
};
pptx.defineSlideMaster({
  title: 'MASTER',
  background: { color: 'F7F8FC' },
  objects: [
    { rect: { x: 0, y: 0, w: 13.333, h: 7.5, line: { color: 'F7F8FC', transparency: 100 }, fill: { color: 'F7F8FC' } } },
    { rect: { x: 0, y: 0, w: 13.333, h: 0.18, line: { color: '1F4E79', transparency: 100 }, fill: { color: '1F4E79' } } },
  ],
  slideNumber: { x: 12.6, y: 7.08, w: 0.45, h: 0.2, color: '5E6A7E', fontSize: 10, align: 'right' },
});

const C = {
  navy: '18324A',
  blue: '2F6BFF',
  teal: '10A7A3',
  green: '2F9E44',
  amber: 'F59F00',
  red: 'E03131',
  text: '1E293B',
  muted: '5B6473',
  line: 'D9E0EA',
  fill: 'FFFFFF',
  soft: 'EEF3FF',
  soft2: 'F2FBFA',
};

function addTitle(slide, title, subtitle) {
  slide.addText(title, {
    x: 0.6, y: 0.45, w: 7.8, h: 0.45,
    fontFace: 'Aptos Display', fontSize: 28, color: C.navy, bold: true,
    margin: 0,
  });
  if (subtitle) {
    slide.addText(subtitle, {
      x: 0.62, y: 0.95, w: 10.8, h: 0.3,
      fontSize: 13, color: C.muted, margin: 0,
    });
  }
}

function addNotes(slide, lines=[]) {
  slide.addNotes(`\n[Sources]\n- No external sources used; content derived from the user's assignment prompt and package-generated assets.\n[/Sources]\n${lines.join('\n')}`);
}

function addPill(slide, text, x, y, w, fill, color='FFFFFF') {
  slide.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h: 0.35,
    rectRadius: 0.08,
    line: { color: fill, transparency: 100 },
    fill: { color: fill },
  });
  slide.addText(text, {
    x, y: y + 0.035, w, h: 0.22,
    fontSize: 12, bold: true, align: 'center', color,
    margin: 0,
  });
}

function addBulletList(slide, items, x, y, w, h, fontSize=17, color=C.text) {
  const runs = [];
  items.forEach((t) => {
    runs.push({ text: t, options: { bullet: { indent: 12 }, breakLine: true } });
  });
  slide.addText(runs, {
    x, y, w, h, fontSize, color,
    breakLine: false,
    paraSpaceAfterPt: 7,
    margin: 2,
    valign: 'top',
  });
}

function addCard(slide, x, y, w, h, title, body, accent=C.blue) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h,
    rectRadius: 0.08,
    line: { color: C.line, width: 1 },
    fill: { color: C.fill },
    shadow: safeOuterShadow('000000', 0.12, 45, 1.5, 0.5),
  });
  slide.addShape(pptx.ShapeType.rect, {
    x, y, w: 0.12, h,
    line: { color: accent, transparency: 100 },
    fill: { color: accent },
  });
  slide.addText(title, {
    x: x + 0.28, y: y + 0.18, w: w - 0.38, h: 0.26,
    fontSize: 18, bold: true, color: C.navy, margin: 0,
  });
  slide.addText(body, {
    x: x + 0.28, y: y + 0.5, w: w - 0.42, h: h - 0.64,
    fontSize: 13, color: C.text, margin: 0,
    valign: 'top',
  });
}

// Slide 1
{
  const s = pptx.addSlide('MASTER');
  s.addShape(pptx.ShapeType.roundRect, {
    x: 0.7, y: 0.75, w: 11.9, h: 5.9,
    rectRadius: 0.1,
    fill: { color: 'FFFFFF' },
    line: { color: C.line, width: 1 },
    shadow: safeOuterShadow('000000', 0.12, 45, 1.5, 0.5),
  });
  s.addShape(pptx.ShapeType.rect, {
    x: 8.95, y: 0.75, w: 3.65, h: 5.9,
    fill: { color: C.soft },
    line: { color: C.soft, transparency: 100 },
  });
  s.addText('Controlled Stable Diffusion for\nE-Commerce Product Image Generation', {
    x: 1.1, y: 1.25, w: 7.2, h: 1.15,
    fontFace: 'Aptos Display', fontSize: 26, bold: true, color: C.navy,
    margin: 0,
  });
  s.addText('Submission-ready starter kit for the challenge scenario: data-driven product images with prompt control, evaluation, and reporting.', {
    x: 1.12, y: 2.55, w: 6.75, h: 0.8,
    fontSize: 18, color: C.text, margin: 0,
  });
  addPill(s, 'Option 1', 1.1, 3.75, 1.15, C.blue);
  addPill(s, 'Baseline vs Improved', 2.4, 3.75, 2.15, C.teal);
  addPill(s, '10+ Slide PPT Included', 4.7, 3.75, 2.35, C.green);
  addCard(s, 1.05, 4.35, 6.9, 1.6, 'What is inside the ZIP?', 'Code skeleton, sample dataset, prompt templates, evaluation scripts, README, AI disclosure, demo video script, and a PowerPoint deck with placeholders for your final outputs.', C.blue);
  addCard(s, 9.25, 1.18, 3.0, 1.1, 'Pipeline', 'Metadata → prompts → Stable Diffusion → evaluation', C.blue);
  addCard(s, 9.25, 2.45, 3.0, 1.1, 'Control', 'Structured prompts + negative prompts + optional ControlNet', C.teal);
  addCard(s, 9.25, 3.72, 3.0, 1.1, 'Metrics', 'Alignment, consistency, diversity, quality', C.green);
  addCard(s, 9.25, 4.99, 3.0, 1.1, 'Deliverables', 'Slides, repo docs, sample outputs, and demo script', C.amber);
  addNotes(s);
}

// Slide 2
{
  const s = pptx.addSlide('MASTER');
  addTitle(s, 'Challenge scenario and system goal', 'Choose one real-world setting and build a controlled, evaluated Stable Diffusion pipeline.');
  addCard(s, 0.7, 1.45, 4.0, 4.95, 'Selected scenario: E-commerce product imagery', 'Goal: generate catalog-ready product images from structured metadata such as title, category, material, color, style, functional attributes, and target camera view.\n\nBusiness value:\n• faster listing creation\n• lower photography cost\n• scalable style consistency across SKUs', C.blue);
  addCard(s, 4.9, 1.45, 3.7, 4.95, 'Core research question', 'Does stronger prompt control improve alignment and consistency without collapsing diversity?\n\nThis project compares:\n1) naive prompts\n2) structured prompts + negative prompts\n3) optional structured prompts + ControlNet', C.teal);
  s.addShape(pptx.ShapeType.roundRect, {
    x: 8.85, y: 1.45, w: 3.8, h: 4.95,
    rectRadius: 0.08,
    fill: { color: 'FFFFFF' }, line: { color: C.line, width: 1 },
    shadow: safeOuterShadow('000000', 0.12, 45, 1.5, 0.5),
  });
  s.addText('Required in your final submission', { x: 9.12, y: 1.72, w: 3.1, h: 0.3, fontSize: 19, bold: true, color: C.navy, margin: 0 });
  addBulletList(s, [
    'Working Stable Diffusion pipeline',
    'At least one control mechanism',
    'Data-to-prompt mapping strategy',
    'Baseline vs improved evaluation',
    'Failure cases and analysis',
    'PPT, video, GitHub repo, and AI disclosure',
  ], 9.05, 2.15, 3.2, 3.85, 16);
  addNotes(s);
}

// Slide 3
{
  const s = pptx.addSlide('MASTER');
  addTitle(s, 'Dataset and data schema', 'A compact CSV schema is included so you can start with a repeatable metadata-to-prompt process.');
  s.addShape(pptx.ShapeType.roundRect, {
    x: 0.72, y: 1.4, w: 7.95, h: 5.35,
    rectRadius: 0.08, fill: { color: 'FFFFFF' }, line: { color: C.line, width: 1 },
  });
  s.addText('Sample CSV columns', { x: 0.98, y: 1.68, w: 2.3, h: 0.25, fontSize: 18, bold: true, color: C.navy, margin: 0 });
  const cols = [
    ['product_id', 'Stable key for grouping outputs'],
    ['title', 'Product name used in prompt'],
    ['category', 'Domain cue such as drinkware or electronics'],
    ['color / material / style', 'Visual constraints'],
    ['attributes', 'Functional details to preserve'],
    ['target_view', 'Front, side, 3/4 angle, etc.'],
    ['environment', 'Background or scene'],
    ['baseline_prompt', 'Naive comparison prompt'],
  ];
  let y = 2.1;
  cols.forEach((row, i) => {
    s.addShape(pptx.ShapeType.rect, { x: 0.98, y, w: 2.25, h: 0.42, fill: { color: i % 2 === 0 ? 'F8FAFC' : 'EEF3FF' }, line: { color: C.line, width: 0.5 } });
    s.addShape(pptx.ShapeType.rect, { x: 3.23, y, w: 5.12, h: 0.42, fill: { color: i % 2 === 0 ? 'F8FAFC' : 'EEF3FF' }, line: { color: C.line, width: 0.5 } });
    s.addText(row[0], { x: 1.1, y: y + 0.08, w: 1.9, h: 0.16, fontSize: 13, bold: true, color: C.text, margin: 0 });
    s.addText(row[1], { x: 3.38, y: y + 0.08, w: 4.8, h: 0.18, fontSize: 12, color: C.text, margin: 0 });
    y += 0.45;
  });
  addCard(s, 8.95, 1.45, 3.75, 2.15, 'Included sample products', 'The starter CSV includes example rows for:\n• insulated water bottle\n• ceramic coffee mug\n• wireless over-ear headphones\n\nEach appears in multiple views.', C.blue);
  addCard(s, 8.95, 3.9, 3.75, 2.35, 'Why structured data matters', 'It makes the generation process auditable. You can trace each attribute in the input row to a specific phrase in the prompt and measure whether the output preserves it.', C.teal);
  addNotes(s);
}

// Slide 4
{
  const s = pptx.addSlide('MASTER');
  addTitle(s, 'Stable Diffusion pipeline', 'The repository includes a Python pipeline using Diffusers and a fallback placeholder path for environments without a model.');
  const boxes = [
    ['Metadata CSV', C.blue],
    ['Prompt Builder', C.teal],
    ['Stable Diffusion', C.green],
    ['Output Images', C.amber],
    ['Evaluation', C.red],
  ];
  let x = 0.8;
  boxes.forEach((b, idx) => {
    if (idx < boxes.length - 1) {
      s.addShape(pptx.ShapeType.chevron, { x: x + 1.9, y: 2.72, w: 0.5, h: 0.55, fill: { color: 'CFD8E6' }, line: { color: 'CFD8E6', transparency: 100 } });
    }
    s.addShape(pptx.ShapeType.roundRect, {
      x, y: 2.25, w: 1.9, h: 1.45,
      rectRadius: 0.08, fill: { color: 'FFFFFF' }, line: { color: b[1], width: 2 },
    });
    s.addText(b[0], { x: x + 0.15, y: 2.78, w: 1.6, h: 0.3, align: 'center', fontSize: 18, bold: true, color: C.navy, margin: 0 });
    x += 2.45;
  });
  addCard(s, 0.95, 4.45, 3.65, 1.55, 'Pipeline implementation', '`src/generate.py` loads metadata, creates baseline or structured prompts, calls the diffusion pipeline, and stores outputs per product and target view.', C.blue);
  addCard(s, 4.82, 4.45, 3.65, 1.55, 'Control hooks', 'Negative prompts are required in the improved configuration. Optional ControlNet support is exposed in the config for stronger geometric or layout conditioning.', C.teal);
  addCard(s, 8.69, 4.45, 3.65, 1.55, 'Fallback behavior', 'If a model is unavailable, the script writes visible placeholder images so the rest of the submission materials still render cleanly.', C.green);
  addNotes(s);
}

// Slide 5
{
  const s = pptx.addSlide('MASTER');
  addTitle(s, 'Prompt design: baseline vs structured', 'This is the main controlled comparison in the starter project.');
  addCard(s, 0.75, 1.45, 4.0, 4.85, 'Baseline prompt', 'Example\n\n“A black water bottle on a white background”\n\nPros\n• fast to write\n• easy baseline\n\nTypical issues\n• misses material and attributes\n• inconsistent composition\n• extra objects or clutter', C.red);
  addCard(s, 4.95, 1.45, 4.0, 4.85, 'Structured prompt template', 'Commercial e-commerce product photo of {title}, {color}, made of {material}, {style} style. Key attributes: {attributes}. View: {target_view}. Scene: {environment}. Professional product lighting. 85mm product photography. Single product only, photorealistic, catalog-ready.', C.blue);
  addCard(s, 9.15, 1.45, 3.45, 4.85, 'Expected effect', 'Structured prompts improve attribute coverage and reduce ambiguity. The trade-off is that stricter prompts can reduce output diversity if over-specified.', C.teal);
  addNotes(s);
}

// Slide 6
{
  const s = pptx.addSlide('MASTER');
  addTitle(s, 'Required control strategy', 'At least one control mechanism is mandatory; this starter kit uses two and leaves room for a third.');
  addCard(s, 0.75, 1.55, 3.8, 4.65, '1. Structured templates', 'Fields from the metadata row are injected into fixed prompt slots. This improves traceability and keeps experiments reproducible.', C.blue);
  addCard(s, 4.78, 1.55, 3.8, 4.65, '2. Negative prompts', 'Example negative prompt:\nlow quality, blurry, text, watermark, duplicate product, busy background, human hands, broken geometry\n\nThis suppresses common product-image artifacts.', C.teal);
  addCard(s, 8.81, 1.55, 3.8, 4.65, '3. Optional ControlNet', 'If you add edge maps, masks, or layout guides, you can enforce object boundaries or view structure more strongly for even better catalog consistency.', C.green);
  addPill(s, 'Required', 1.0, 6.45, 1.2, C.blue);
  addPill(s, 'Required', 5.03, 6.45, 1.2, C.teal);
  addPill(s, 'Optional Bonus', 9.02, 6.45, 1.5, C.green);
  addNotes(s);
}

// Slide 7
{
  const s = pptx.addSlide('MASTER');
  addTitle(s, 'Evaluation metrics and experiment plan', 'The assignment requires measurable evaluation, a baseline comparison, and failure analysis.');
  s.addShape(pptx.ShapeType.roundRect, { x: 0.72, y: 1.45, w: 6.15, h: 5.1, rectRadius: 0.08, fill: { color: 'FFFFFF' }, line: { color: C.line, width: 1 } });
  s.addText('Required metrics', { x: 1.0, y: 1.75, w: 2.0, h: 0.25, fontSize: 18, bold: true, color: C.navy, margin: 0 });
  addBulletList(s, [
    'Prompt alignment: does the image reflect metadata and prompt content?',
    'Consistency: are multiple views of the same product visually coherent?',
    'Diversity: are generated samples meaningfully distinct and non-duplicate?',
    'Quality: human rubric plus optional automated proxy metrics.',
  ], 0.95, 2.15, 5.5, 2.7, 16);
  addCard(s, 0.95, 4.95, 5.45, 1.2, 'Suggested comparison table', 'Baseline naive prompt | Structured + negative prompt | Optional structured + ControlNet', C.amber);
  addCard(s, 7.15, 1.45, 5.45, 2.15, 'Included scripts', '`src/evaluate.py` builds a summary CSV and a qualitative review sheet. `src/compare_baseline.py` creates a simple chart for your report or slides.', C.blue);
  addCard(s, 7.15, 3.95, 5.45, 2.15, 'Failure cases to document', 'Wrong number of objects, color drift, cluttered scenes, distorted geometry, incorrect view angle, and outputs that ignore key product attributes.', C.red);
  addNotes(s);
}

// Slide 8
{
  const s = pptx.addSlide('MASTER');
  addTitle(s, 'Results slide template', 'The ZIP includes placeholder images so the deck renders now; replace them with your real pipeline outputs before submission.');
  const img1 = path.resolve('/mnt/data/sd_ecommerce_submission/sample_outputs/P001_baseline_front.png');
  const img2 = path.resolve('/mnt/data/sd_ecommerce_submission/sample_outputs/P001_structured_front.png');
  const img3 = path.resolve('/mnt/data/sd_ecommerce_submission/sample_outputs/P001_structured_three_quarter.png');
  const chart = path.resolve('/mnt/data/sd_ecommerce_submission/results/baseline_vs_structured.png');
  s.addText('Baseline', { x: 0.95, y: 1.45, w: 2.0, h: 0.2, fontSize: 18, bold: true, color: C.navy, margin: 0 });
  s.addText('Structured', { x: 4.55, y: 1.45, w: 2.0, h: 0.2, fontSize: 18, bold: true, color: C.navy, margin: 0 });
  s.addText('Structured (alt view)', { x: 8.15, y: 1.45, w: 2.6, h: 0.2, fontSize: 18, bold: true, color: C.navy, margin: 0 });
  [img1, img2, img3].forEach((img, i) => {
    const x = 0.85 + i * 3.6;
    s.addShape(pptx.ShapeType.roundRect, { x, y: 1.8, w: 3.1, h: 3.1, rectRadius: 0.05, fill: { color: 'FFFFFF' }, line: { color: C.line, width: 1 } });
    s.addImage({ path: img, ...imageSizingContain(img, x + 0.1, 1.9, 2.9, 2.9) });
  });
  addCard(s, 11.55, 1.8, 1.1, 3.1, 'Tip', 'Replace these placeholders with real generated outputs and label success/failure cases directly on the slide.', C.amber);
  s.addShape(pptx.ShapeType.roundRect, { x: 0.85, y: 5.2, w: 6.1, h: 1.2, rectRadius: 0.05, fill: { color: 'FFFFFF' }, line: { color: C.line, width: 1 } });
  s.addText('Example narrative: structured prompts usually improve cleanliness, attribute retention, and view consistency, but may over-constrain diversity.', { x: 1.08, y: 5.56, w: 5.6, h: 0.35, fontSize: 14, color: C.text, margin: 0 });
  s.addShape(pptx.ShapeType.roundRect, { x: 7.2, y: 5.2, w: 5.4, h: 1.2, rectRadius: 0.05, fill: { color: 'FFFFFF' }, line: { color: C.line, width: 1 } });
  s.addImage({ path: chart, ...imageSizingContain(chart, 7.35, 5.28, 5.1, 1.0) });
  addNotes(s);
}

// Slide 9
{
  const s = pptx.addSlide('MASTER');
  addTitle(s, 'Findings, insights, and limitations', 'Use this slide to turn outputs into analysis — not just image dumps.');
  addCard(s, 0.75, 1.5, 3.8, 4.9, 'Findings to look for', '• which prompt fields mattered most?\n• did negative prompts reduce text/logo artifacts?\n• which categories were easiest or hardest?\n• where did control improve consistency the most?', C.blue);
  addCard(s, 4.77, 1.5, 3.8, 4.9, 'Typical limitations', '• hard fine-grained geometry\n• attribute conflicts in long prompts\n• style and realism trade-offs\n• stronger control can reduce diversity\n• diffusion outputs may still miss subtle product details', C.red);
  addCard(s, 8.79, 1.5, 3.8, 4.9, 'Bonus extension ideas', '• image-to-video product spin demo\n• narration with audio description\n• multimodal evaluation with text + image + audio\n• stronger conditioning via ControlNet or reference images', C.green);
  addNotes(s);
}

// Slide 10
{
  const s = pptx.addSlide('MASTER');
  addTitle(s, 'GitHub, demo video, and AI disclosure', 'The challenge explicitly requires transparency about tools and generated content.');
  addCard(s, 0.75, 1.55, 3.9, 2.1, 'GitHub repository', 'Replace with your final URL:\nhttps://github.com/your-username/your-repo\n\nREADME should include setup, dataset, outputs, and libraries used.', C.blue);
  addCard(s, 4.92, 1.55, 3.9, 2.1, 'Demo video', 'Replace with your final video URL:\nhttps://youtube.com/... or GitHub-hosted clip\n\nKeep it concise: system overview, input, output, results.', C.teal);
  addCard(s, 9.09, 1.55, 3.5, 2.1, 'AI tools used', 'A disclosure template is included in `docs/ai_tool_disclosure.md` and should be copied into your final submission.', C.green);
  addCard(s, 0.75, 4.05, 11.85, 2.2, 'Included in the ZIP', 'README, config, starter code, sample CSV, evaluation scripts, deck, demo script, AI disclosure, placeholder outputs, and results templates. This makes it easy to finish the project instead of starting from a blank folder.', C.amber);
  addNotes(s);
}

// Slide 11
{
  const s = pptx.addSlide('MASTER');
  addTitle(s, 'How to use this starter package', 'A practical completion checklist for your final submission.');
  addBulletList(s, [
    'Install the dependencies and run baseline generation from the sample CSV.',
    'Run structured prompt generation and compare outputs per product/view.',
    'Optionally add ControlNet or another conditioning method for stronger control.',
    'Run evaluation, fill the human quality rubric, and update the results chart.',
    'Replace placeholder images and URLs in the deck, then record the demo video.',
    'Push the final code and outputs to GitHub and submit the ZIP + links.',
  ], 0.9, 1.65, 7.3, 4.8, 18);
  addCard(s, 8.6, 1.65, 3.5, 1.35, 'Command 1', 'python src/generate.py --config configs/default.yaml --mode baseline', C.blue);
  addCard(s, 8.6, 3.2, 3.5, 1.35, 'Command 2', 'python src/generate.py --config configs/default.yaml --mode structured', C.teal);
  addCard(s, 8.6, 4.75, 3.5, 1.35, 'Command 3', 'python src/evaluate.py --metadata data/sample_products.csv --baseline_dir outputs/baseline --improved_dir outputs/structured --output_csv results/evaluation_summary.csv', C.green);
  addNotes(s);
}

for (const slide of pptx._slides) {
  warnIfSlideHasOverlaps(slide, pptx);
  warnIfSlideElementsOutOfBounds(slide, pptx);
}

pptx.writeFile({ fileName: '/mnt/data/sd_ecommerce_submission/slides/Stable_Diffusion_Ecommerce_Starter.pptx' });
