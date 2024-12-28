# Revision-3: Made the second sweep part identical to the first sweep and fixed the final processing
# For the final version, I might put the final processing into a function because it's very long. It should work anyways though.
# Pay attention to the fact that allData array is global!
# I only send "start" for now. If it works, just add "init_start" as well to the Arduino.

import tkinter as tk
from tkinter import BOTH, Canvas, ttk
import RPi.GPIO as GPIO

import serial
import time
import csv
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter

# Serial communication setup
SERIAL_PORT = '/dev/ttyACM0'
SERIAL_RATE = 9600
ser = serial.Serial(SERIAL_PORT, SERIAL_RATE, timeout=1)
ser.reset_input_buffer()
allData = []

# Savitzky-Golay filter setup
window_length = 31
polyorder = 3

# GPIO setup
ARROW_DOWN_GPIO = 17
ARROW_LEFT_GPIO = 23
ARROW_RIGHT_GPIO = 27
OK_GPIO = 22
GPIO.setmode(GPIO.BCM)

GPIO.setup(ARROW_DOWN_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(ARROW_LEFT_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(ARROW_RIGHT_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(OK_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Create the main window
root = tk.Tk()
root.geometry("480x640")
DEFAULT_BUTTON_COLOR = "#f0f0f0"
current_screen = None
focused_button = None

# State tracking
first_click = True

# Helper functions
def remove_nan_ovf(array):
    i = 0
    while i < len(array):
        if array[i] == "ovf" or array[i] == "nan":
            del array[i]
        else:
            i += 1

    return array

def process_data(message):
    # Split the message into its parts
    x = np.array(message[0].split("&"))
    # Split datasets to values
    phaseData1 = x[0].split(",")
    phaseData2 = x[1].split(",")
    phaseData3 = x[2].split(",")
    tempData = x[3]
    humData = x[4]
    # Remove nan and ovf values
    remove_nan_ovf(phaseData1)
    remove_nan_ovf(phaseData2)
    remove_nan_ovf(phaseData3)
    # Convert values to float
    phaseData1 = np.asfarray(phaseData1, float)
    phaseData2 = np.asfarray(phaseData2, float)
    phaseData3 = np.asfarray(phaseData3, float)
    tempData = float(tempData)
    humData = float(humData)

    return phaseData1, phaseData2, phaseData3, tempData, humData


# UI functions

def update_focus(button):
    global focused_button
    if focused_button:
        try:
            focused_button.config(bg=DEFAULT_BUTTON_COLOR)
        except tk.TclError:
            pass
    button.config(bg="green")
    focused_button = button

# Page 1 - booting screen
def show_circle_with_text():
    global current_screen
    current_screen = "circle"
    canvas = tk.Canvas(root, width=480, height=640)
    canvas.pack(fill=BOTH, expand=True)
    canvas.create_oval(80, 160, 400, 480, outline="black", width=2, tags="circle")
    canvas.create_text(240, 320, text="AmiNIC", font=("Arial", 48), fill="black", tags="circle_text")
    root.after(5000, home_screen)

# Page 2 - home screen
def home_screen():
    global current_screen
    current_screen = "home"
    
    GPIO.remove_event_detect(ARROW_DOWN_GPIO)
    GPIO.remove_event_detect(OK_GPIO)

    for widget in root.winfo_children():
        widget.destroy()

    button1 = tk.Button(root, text="New Measurement", font=("Arial", 28))
    button1.place(x=60, y=200, width=360, height=80)
    button2 = tk.Button(root, text="TURN OFF", font=("Arial", 28))
    button2.place(x=140, y=320, width=200, height=80)

    update_focus(button1)

    def focus_down():
        if focused_button == button1:
            update_focus(button2)
        else:
            update_focus(button1)

    def ok_action():
        if focused_button == button1:
            ser.write(b"init_start") #send "init_start" to Arduino to start initial sweep. No binding needed. //NOW ONLY "start"
            show_loading_screen()
        elif focused_button == button2:
            blank_screen()

    GPIO.add_event_detect(ARROW_DOWN_GPIO, GPIO.FALLING, callback=lambda x: focus_down(), bouncetime=500)
    GPIO.add_event_detect(OK_GPIO, GPIO.FALLING, callback=lambda x: ok_action(), bouncetime=500)

# Page 0 - if quit button pressed
def blank_screen():
    global current_screen
    current_screen = "blank"

    for widget in root.winfo_children():
        widget.destroy()

    root.after(2000, home_screen)

# Page 3 - initial sweep
def show_loading_screen():
    global current_screen
    current_screen = "loading"

    for widget in root.winfo_children():
        widget.destroy()

    frame = tk.Frame(root, width=480, height=640)
    frame.pack_propagate(False)
    frame.pack(expand=True)

    canvas = tk.Canvas(frame, width=480, height=640)
    canvas.pack(expand=True)

    loading_label = tk.Label(canvas, text="Loading...", font=("Arial", 36))
    canvas.create_window(240, 200, window=loading_label)

    progress = ttk.Progressbar(canvas, orient="horizontal", length=400, mode="determinate")
    canvas.create_window(240, 300, window=progress)

    progress["maximum"] = 100
    increment = 20

    def update_progress(value):
        if value <= 100:
            progress["value"] = value
            root.after(1000, update_progress, value + increment)
        else:
            while(ser.in_waiting == 0):
                pass
            if(ser.in_waiting > 0):
                # Read Arduino message
                init_reading = ser.readline().decode('utf-8').rstrip()
                allData = []
                allData.append(init_reading)
                # Declare sensor data variables
                global init_phaseData1, init_phaseData2, init_phaseData3
                global tempData1, humData1
                # Process and save data
                init_phaseData1, init_phaseData2, init_phaseData3, tempData1, humData1 = process_data(allData)

                np.savetxt("/home/raspi/programming/init_phaseData1.csv", np.transpose(init_phaseData1),delimiter=",")
                np.savetxt("/home/raspi/programming/init_phaseData2.csv", np.transpose(init_phaseData2), delimiter=",")
                np.savetxt("/home/raspi/programming/init_phaseData3.csv", np.transpose(init_phaseData3), delimiter=",")

            show_examination_screen()

    update_progress(0)

def show_examination_screen():
    global current_screen, focused_button
    current_screen = "examination"

    for widget in root.winfo_children():
        widget.destroy()

    title = tk.Label(root, text="EXAMINATION", font=("Arial", 36, "bold"))
    title.pack(pady=40)

    instruction = tk.Label(
        root,
        text="Please put and hold the device as close to the meat as possible",
        font=("Arial", 24, "italic"),
        wraplength=440,
        justify="center"
    )
    instruction.pack(pady=40)

    start_button = tk.Button(root, text="START", font=("Arial", 28), bg=DEFAULT_BUTTON_COLOR)
    start_button.pack(side="bottom", pady=40)

    focused_button = start_button
    update_focus(focused_button)

    def focus_right():
        update_focus(start_button)

    def ok_action():
        if focused_button == start_button:
            ser.write(b"start") #send "start" to arduino - second sweep, 15s delay needed for binding to happen
            show_countdown_screen()

    GPIO.remove_event_detect(ARROW_RIGHT_GPIO)
    GPIO.remove_event_detect(OK_GPIO)
     
    #GPIO.cleanup(OK_GPIO)
     
    #GPIO.add_event_detect(ARROW_RIGHT_GPIO, GPIO.RISING, callback=lambda x: focus_right(), bouncetime=300)
    GPIO.add_event_detect(OK_GPIO, GPIO.FALLING, callback=lambda x: ok_action(), bouncetime=500)

def show_countdown_screen():
    global current_screen
    current_screen = "countdown"

    for widget in root.winfo_children():
        widget.destroy()

    label = tk.Label(root, text="Hold it for:", font=("Arial", 32, "bold"))
    label.pack(pady=80)

    countdown_label = tk.Label(root, text="5", font=("Arial", 96))
    countdown_label.pack(pady=40)

    def countdown_timer(count):
        if count >= 0:
            countdown_label.config(text=str(count))
            root.after(1000, countdown_timer, count - 1)
        else:
            while(ser.in_waiting == 0):
                pass
            if(ser.in_waiting > 0):
                #Read Arduino message    
                normal_reading = ser.readline().decode('utf-8').rstrip()
                allData = []
                allData.append(normal_reading)
                # Declare sensor data variables
                global normal_phaseData1, normal_phaseData2, normal_phaseData3
                global tempData2, humData2
                # Process and save data
                normal_phaseData1, normal_phaseData2, normal_phaseData3, tempData2, humData2 = process_data(allData)

                np.savetxt("/home/raspi/programming/normal_phaseData1.csv", np.transpose(normal_phaseData1), delimiter=",")
                np.savetxt("/home/raspi/programming/normal_phaseData2.csv", np.transpose(normal_phaseData2), delimiter=",")
                np.savetxt("/home/raspi/programming/normal_phaseData3.csv", np.transpose(normal_phaseData3), delimiter=",")

            show_new_buttons()

    countdown_timer(5)

def show_new_buttons():
    global current_screen, btn_back, focused_button
    current_screen = "measurement_results_screen"
    
    GPIO.remove_event_detect(OK_GPIO)
    GPIO.remove_event_detect(ARROW_LEFT_GPIO)
    
    for widget in root.winfo_children():
        widget.destroy()

    frame = tk.Frame(root)
    frame.pack_propagate(False)
    frame.pack(side="left", fill="both", expand=True)

    frame.grid_rowconfigure(0, weight=1)
    frame.grid_rowconfigure(1, weight=0)
    frame.grid_rowconfigure(2, weight=0)
    frame.grid_rowconfigure(3, weight=0)
    frame.grid_rowconfigure(4, weight=1)
    frame.grid_columnconfigure(0, weight=1)
    
    # Filter & get peak value indexes from initial sweep
    init_phaseData1_filtered = savgol_filter(init_phaseData1, window_length, polyorder)
    init_phaseData2_filtered = savgol_filter(init_phaseData2, window_length, polyorder)
    init_phaseData3_filtered = savgol_filter(init_phaseData3, window_length, polyorder)

    init_phaseData1_peak_index = np.argmax(init_phaseData1_filtered)
    init_phaseData2_peak_index = np.argmax(init_phaseData2_filtered)
    init_phaseData3_peak_index = np.argmax(init_phaseData3_filtered)
    
    
    # Filter & get peak value indexes from normal sweep
    normal_phaseData1_filtered = savgol_filter(normal_phaseData1, window_length, polyorder)
    normal_phaseData2_filtered = savgol_filter(normal_phaseData2, window_length, polyorder)
    normal_phaseData3_filtered = savgol_filter(normal_phaseData3, window_length, polyorder)

    normal_phaseData1_peak_index = np.argmax(normal_phaseData1_filtered)
    normal_phaseData2_peak_index = np.argmax(normal_phaseData2_filtered)
    normal_phaseData3_peak_index = np.argmax(normal_phaseData3_filtered)
    
    index_diff1 = abs(init_phaseData1_peak_index-normal_phaseData1_peak_index)
    index_diff2 = abs(init_phaseData2_peak_index-normal_phaseData2_peak_index)
    index_diff3 = abs(init_phaseData3_peak_index-normal_phaseData3_peak_index)
    
    avg_index_diff = (index_diff1+index_diff2+index_diff3)/3

    if avg_index_diff <= 10:
        quality_value = "Good"
        
    elif (10 < avg_index_diff <= 30):
        quality_value = "Fair"
        
    else:
        quality_value = "Bad"

    # Insert readings from Arduino
    temp_value = tempData1
    humidity_value = humData1

    labels_text = [f"Temperature: {temp_value}C", f"Humidity: {humidity_value}%", f"Quality: {quality_value}"]
    
    for i, text in enumerate(labels_text):
        label = tk.Label(frame, text=text, font=("Arial", 28), anchor="w")
        label.grid(row=i + 1, column=0, sticky="w", padx=40, pady=10)

    btn_back = tk.Button(frame, text="BACK", font=("Arial", 28), command=home_screen)
    btn_back.grid(row=5, column=0, sticky="se", padx=16, pady=16)
    update_focus(btn_back)

    def focus_left():
        update_focus(btn_back)

    def ok_action():
        if focused_button == btn_back:
            home_screen()

    #GPIO.add_event_detect(ARROW_LEFT_GPIO, GPIO.FALLING, callback=lambda x: focus_left(), bouncetime=300)
    GPIO.add_event_detect(OK_GPIO, GPIO.FALLING, callback=lambda x: ok_action(), bouncetime=500)

# Start the application
show_circle_with_text()

try:
    root.mainloop()
finally:
    GPIO.cleanup()
