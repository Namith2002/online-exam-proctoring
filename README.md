# 🎓 Online Exam Proctoring System

A secure and user-friendly online examination system with automated proctoring capabilities. Built with Python Flask, SQLite, and modern web technologies.

## 🌟 Features

### Student Features

- 📝 Take exams from any location with a webcam and microphone
- ⏱️ Real-time exam timer with auto-submit
- 💾 Auto-save answers as you progress
- 📊 View your exam history and scores
- 🔒 Secure login and exam access

### Administrator Features

- ✏️ Create and edit exams with multiple-choice questions
- ⚙️ Configure exam duration and settings
- 👥 Monitor student attempts in real-time
- 📸 Review proctoring data (webcam snapshots & audio)
- 📈 View detailed exam analytics and results

### Security Features

- 📷 Automated webcam snapshots every 15 seconds
- 🎤 Audio recording in 20-second intervals
- 🚫 Tab switch detection
- ⚠️ Window blur monitoring
- 🕒 Time tracking and enforcement

## 🚀 Setup Guide

### System Requirements

- Python 3.8 or higher
- Modern web browser with webcam and microphone support
- SQLite3

### Installation Steps

1. Clone the repository:

```bash
git clone https://github.com/Namith2002/online-exam-proctoring.git
cd online-exam-proctoring
```

1. Create a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

1. Install dependencies:

```bash
pip install -r requirements.txt
```

1. Initialize the database:

```bash
python db_init.py
```

1. Run the application:

```bash
python app.py
```

1. Access the application at `http://localhost:5000`

### Default Admin Access

- Username: admin123
- Password: admin_123@45

⚠️ **Important**: Change these credentials in production!

## 🏗️ Directory Structure

```plaintext
online-exam-proctoring/
├── app.py              # Main application file
├── db_init.py          # Database initialization
├── models.py           # Database models
├── requirements.txt    # Python dependencies
├── static/            
│   ├── css/           # Stylesheets
│   └── js/            # JavaScript files
├── templates/          # HTML templates
└── uploads/           # Proctoring data storage
    ├── proctor_audio/
    └── proctor_images/
```

## 🔒 Built-in Security

- Password hashing using secure algorithms
- Session management and authentication
- Input validation and sanitization
- Secure file upload handling
- Anti-tampering measures during exams

## 📱 Supported Browsers

Tested and working on:

- Google Chrome (recommended)
- Mozilla Firefox
- Microsoft Edge
- Safari

## 🛠️ Architecture Overview

### Server Components

- **Framework**: Flask (Python)
- **Database**: SQLite
- **Authentication**: Session-based
- **File Storage**: Local filesystem

### Client Components

- **UI Framework**: Custom CSS with responsive design
- **JavaScript**: Vanilla JS with modern APIs
- **Media Handling**: MediaRecorder API
- **Real-time Updates**: Fetch API

## 🤝 Development Guide

1. Fork the repository
1. Create your feature branch (`git checkout -b feature/AmazingFeature`)
1. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
1. Push to the branch (`git push origin feature/AmazingFeature`)
1. Open a Pull Request

## 📋 Roadmap

- [ ] Add support for essay-type questions
- [ ] Implement face detection in proctoring
- [ ] Add real-time chat support
- [ ] Enable PDF export of results
- [ ] Add email notifications

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Credits

- Flask documentation and community
- MediaRecorder API documentation
- SQLite documentation
- Open-source community

## 📞 Contact

For support, please create an issue in the GitHub repository or contact the maintainers.
- 📊 View your exam history and scores
- 🔒 Secure login and exam access

### For Administrators
- ✏️ Create and edit exams with multiple-choice questions
- ⚙️ Configure exam duration and settings
- 👥 Monitor student attempts in real-time
- 📸 Review proctoring data (webcam snapshots & audio)
- 📈 View detailed exam analytics and results

### Proctoring Features
- 📷 Automated webcam snapshots every 15 seconds
- 🎤 Audio recording in 20-second intervals
- 🚫 Tab switch detection
- ⚠️ Window blur monitoring
- 🕒 Time tracking and enforcement

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- Modern web browser with webcam and microphone support
- SQLite3

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Namith2002/online-exam-proctoring.git
cd online-exam-proctoring
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
python db_init.py
```

5. Run the application:
```bash
python app.py
```

6. Access the application at `http://localhost:5000`

### Default Admin Credentials
- Username: admin123
- Password: admin_123@45

⚠️ **Important**: Change these credentials in production!

## 🏗️ Project Structure

```
online-exam-proctoring/
├── app.py              # Main application file
├── db_init.py          # Database initialization
├── models.py           # Database models
├── requirements.txt    # Python dependencies
├── static/            
│   ├── css/           # Stylesheets
│   └── js/            # JavaScript files
├── templates/          # HTML templates
└── uploads/           # Proctoring data storage
    ├── proctor_audio/
    └── proctor_images/
```

## 🔒 Security Features

- Password hashing using secure algorithms
- Session management and authentication
- Input validation and sanitization
- Secure file upload handling
- Anti-tampering measures during exams

## 📱 Browser Compatibility

Tested and supported on:
- Google Chrome (recommended)
- Mozilla Firefox
- Microsoft Edge
- Safari

## 🛠️ Technical Implementation

### Backend
- **Framework**: Flask (Python)
- **Database**: SQLite
- **Authentication**: Session-based
- **File Storage**: Local filesystem

### Frontend
- **UI Framework**: Custom CSS with responsive design
- **JavaScript**: Vanilla JS with modern APIs
- **Media Handling**: MediaRecorder API
- **Real-time Updates**: Fetch API

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📋 Todo

- [ ] Add support for essay-type questions
- [ ] Implement face detection in proctoring
- [ ] Add real-time chat support
- [ ] Enable PDF export of results
- [ ] Add email notifications

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Flask documentation and community
- MediaRecorder API documentation
- SQLite documentation
- Open-source community

## 📞 Support

For support, please create an issue in the GitHub repository or contact the maintainers.
