# AI Test Verification Tool

Python tool for verifying AI model responses using keyword-based scoring.

## Quick Start

**GUI Version (Recommended):**
```bash
./launch_gui.sh
```

**Command Line Menu:**
```bash
./launch.sh
```

Interactive menu/GUI will appear. Select options to run tests.

## Configuration

Edit `src/config.py`:
- API keys: `OPENAI_API_KEY`, `DEEPSEEK_API_KEY`
- Settings: `MAX_TESTS`, `SCORE_THRESHOLD`

## Output

Results saved to `output/` directory:
- `airline_policy.xlsx`
- `visa_guidance.xlsx`

## Requirements

```bash
source venv/bin/activate
pip install -r requirements.txt
```

## Project Structure

```
src/
├── main.py          # Main script
├── menu.py          # Interactive CLI menu
├── gui.py           # GUI window
├── config.py        # Configuration
├── bots/            # LLM clients
├── judge/           # Scoring logic
└── utils/           # CSV/Excel utilities
```
