Chat App

A real-time group chat application built with Flask, Socket.IO, and Bootstrap — enhanced with a dark theme, smooth animations, and some extra UI polish.

Features

User Authentication – Register, log in, and update profile details (display name + avatar URL).

Group Chat – Create chat groups, view all available groups, and join instantly.

Real-Time Messaging – Powered by Socket.IO for instant message delivery.

Dark Theme – A custom dark UI theme applied globally via styles.css.

Animations & Transitions – Smooth hover effects, button animations, and chat message transitions.

Typing Indicator – Shows when someone is typing in the chat (pure front-end enhancement).

Responsive Design – Works across desktop, tablet, and mobile screens using Bootstrap.

Tech Stack

Backend: Flask (Python)

Frontend: Jinja2 templates + Bootstrap 5

Real-Time Engine: Flask-SocketIO (Socket.IO)

Styling: Custom styles.css with animations and dark theme

Project Structure
.
├── app.py               # Flask app entry point
├── templates/           # HTML templates (Jinja2)
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── groups.html
│   ├── chat.html
│   └── profile.html
├── static/
│   └── styles.css       # Custom styles and animations
└── README.md            # Project documentation