# PodAsk Backend Test Frontend

This is a simple static page to test the podcast session flow:
- create a session
- start a segment
- raise hand
- clarify
- provide answer
- resume

## How to use

1. Start the backend:
   ```bash
   python run.py
   ```

2. Open `test-frontend/index.html` in your browser.

If your browser blocks `file://` requests, run a local static server:

```bash
python -m http.server 5173
```

Then open:
```
http://localhost:5173/test-frontend/
```

The UI defaults to `http://localhost:8000` as the API base URL.
