# NeuralNotes

**AI-Powered Lecture Notes to Study Pack Generator** · Bennett University Prompt Engineering (SCSE4041) · C2 · Team PE-B13-18

Paste lecture notes or open a UTF-8 TXT file to build a summary, key terms and short-answer practice questions. The app includes source references, an answer toggle and Markdown export.

## Run locally

1. Install Python 3.10 or later with Tkinter. On Windows, use the standard Python installer with Tcl/Tk enabled.
2. Open a terminal in the extracted project folder and run `python app.py`.
3. Choose **Offline preview** and **Load example** to try the interface without any model.
4. For **AI · v3 chain**, create a Gemini API key in [Google AI Studio](https://aistudio.google.com/apikey), add it to `.env` as `GOOGLE_API_KEY=your_key`, and install dependencies with `python -m pip install -r requirements.txt`. The AI chain uses the Google `google-genai` SDK and Gemini Flash. **Offline preview** does not need a key or internet access.

## Browser dashboard

Run `python app_web.py` to open the professional browser interface at `http://127.0.0.1:5050`. It provides Gemini key status, source metrics, a three-stage pipeline, filtered study-pack views and Markdown export. The browser dashboard uses the same verified pipeline and offline/AI modes as the desktop app.

Notes must contain at least four words and be at most 12,000 characters after trimming. Use notes you have permission to process. Files are only written when you export or run the evaluator.

## Reproduce the evidence

```sh
python -m unittest discover -s evaluation -v
python evaluate.py --mode offline --output evaluation/offline-results.json
python evaluate.py --mode ai --output live-results.json
```

The offline evidence covers ten inputs. The unit tests exercise chain behavior with injected model responses. AI evaluation calls Gemini and requires a valid API key. Apply [the rubric](evaluation/rubric.md) to generated outputs and keep scores and raw responses with the submission evidence.

## GitHub upload

Extract the ZIP. Upload the contents of `NeuralNotes` to the repository root, including `.gitignore`, `requirements.txt` and `.env.example`. Keep the folder structure. This includes both Python entry points, the prompt templates, evaluation cases, tests, results and screenshots, and the two Markdown guides. Install the Python packages with `python -m pip install -r requirements.txt`. Keep `.env`, course PDFs and student IDs out of the public repository unless your team has permission to publish them.

The desktop app downloads from this repository. If a distinct prototype link is needed for the LMS, share a ZIP or release URL that faculty can access without requesting permission. Keep the `.env` file private and never commit API keys.

## References and development disclosure

- Bennett University, *Prompt Engineering Mini-Project Guidelines, Milestones & Assessment*, sections 10–15 and Appendix A (2026).
- OpenAI Codex assisted with prototype implementation, prompt templates, synthetic evaluation cases and report drafting. Team members should review and be able to explain all submitted materials.
