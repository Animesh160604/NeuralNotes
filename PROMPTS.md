# NeuralNotes prompts

The app uses three final prompts in V3 and includes two earlier prompts for comparison. The exact wording is in the linked text files. Run the evaluator with `--mode ai` to exercise all versions.

| Version | Prompt | Inputs | Outputs |
| --- | --- | --- | --- |
| V1 | [Baseline](prompts/v1.txt) | Numbered source lines | Free-form pack |
| V2 | [Structured single pass](prompts/v2.txt) | Numbered source lines and pack schema | Validated pack JSON |
| V3 | [P1 Evidence extraction](prompts/p1.txt) | Numbered source lines and extraction schema | Title and up to 12 quoted claims |
| V3 | [P2 Pack drafting](prompts/p2.txt) | Verified claims, corresponding numbered lines and pack schema | Draft pack |
| V3 | [P3 Grounding review](prompts/p3.txt) | Draft and allowed lines with pack schema | Corrected pack |

Each linked file is the system message. When a schema applies, the code appends a line beginning with `JSON schema: ` and the serialized schema. The user message is the JSON payload described above. There are no additional LLM prompts in the application. The offline mode uses text patterns and makes zero LLM calls.

The final prompt sequence is extraction → drafting → review. Python checks P1 quotes against their stated source lines and checks the final structure and reference IDs. It cannot check whether a cited line actually entails each generated claim. Run the human rubric before claiming factual accuracy or improvement.
