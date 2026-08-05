# ET617 Mathematics Learning App

This project is a standalone learner-focused Mathematics web application built with Flask. It provides:

- learner login and registration
- a modern student dashboard
- interactive Mathematics chapter study blocks
- embedded video lesson playback with play, pause, and fast-forward controls
- flashcard-style learning facts for each topic
- short quiz activity with multi-question support
- clickstream tracking stored in SQLite

## Run the app

1. Open a terminal in the project folder:

   ```powershell
   cd "C:\Users\Yugratna\Desktop\Sem5\ET617\Assignment1\et617_assignment1"
   ```

2. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Start the app:

   ```powershell
   python app.py
   ```

4. Open the app in your browser:

   ```text
   http://127.0.0.1:5000
   ```

## Default learner login

- Username: `learner`
- Password: `demo123`

## Local server

The app runs on the local development server:

```text
http://127.0.0.1:5000
```

## Mathematics study flow

The dashboard is designed as a student learning portal with:

- chapter progress circles
- lessons completed and remaining counters
- expandable chapter sections
- quick learning facts
- short quiz review cards
- dark/light mode

The database file is:

```text
learning_app.db
```
