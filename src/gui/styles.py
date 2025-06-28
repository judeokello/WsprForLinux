#!/usr/bin/env python3
"""
Centralized styles for W4L GUI components.

Contains all CSS styles used across the application for consistency.
"""

# Title bar styles
TITLE_BAR_STYLE = """
QFrame {
    background-color: #3498db; 
    border-top-left-radius: 10px; 
    border-top-right-radius: 10px;
}
"""

TITLE_LABEL_STYLE = """
color: #2c3e50;
"""

SETTINGS_BUTTON_STYLE = """
QPushButton {
    background-color: transparent;
    border: none;
    color: #2c3e50;
    border-radius: 15px;
}
QPushButton:hover {
    background-color: rgba(255, 255, 255, 0.3);
}
"""

# Content area styles
CONTENT_FRAME_STYLE = """
QFrame {
    background-color: white;
    border: 1px solid #bdc3c7;
    border-radius: 8px;
}
"""

# Status bar styles
STATUS_FRAME_STYLE = """
QFrame {
    background-color: #f8f9fa;
    border-bottom-left-radius: 10px;
    border-bottom-right-radius: 10px;
}
"""

# Button styles
RECORD_BUTTON_READY_STYLE = """
QPushButton {
    background-color: #27ae60;
    color: white;
    border: none;
    border-radius: 17px;
    padding: 8px 16px;
}
QPushButton:hover {
    background-color: #229954;
}
"""

RECORD_BUTTON_RECORDING_STYLE = """
QPushButton {
    background-color: #e74c3c;
    color: white;
    border: none;
    border-radius: 17px;
    padding: 8px 16px;
}
QPushButton:hover {
    background-color: #c0392b;
}
"""

CLOSE_BUTTON_STYLE = """
QPushButton {
    background-color: #e74c3c;
    color: white;
    border: none;
    border-radius: 17px;
}
QPushButton:hover {
    background-color: #c0392b;
}
"""

# Status label styles
STATUS_READY_STYLE = "color: #27ae60; font-weight: bold;"
STATUS_LOADING_STYLE = "color: #f39c12; font-weight: bold;"
STATUS_RECORDING_STYLE = "color: #e74c3c; font-weight: bold;"
STATUS_STOPPING_STYLE = "color: #f39c12; font-weight: bold;"
STATUS_FINISHED_STYLE = "color: #27ae60; font-weight: bold;"
STATUS_ABORTED_STYLE = "color: #95a5a6; font-weight: bold;"
STATUS_ERROR_STYLE = "color: #e74c3c; font-weight: bold;"
STATUS_RECOVERING_STYLE = "color: #f39c12; font-weight: bold;"

# Instruction label style
INSTRUCTION_LABEL_STYLE = "color: #2c3e50;"

# Model combo style
MODEL_COMBO_STYLE = """
QComboBox {
    border: 1px solid #bdc3c7;
    border-radius: 5px;
    padding: 5px;
    background-color: white;
}
QComboBox:hover {
    border-color: #3498db;
}
QComboBox:disabled {
    background-color: #ecf0f1;
    color: #95a5a6;
}
""" 