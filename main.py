import streamlit as st
import pandas as pd
import tempfile
import os
from fpdf import FPDF
from pdf2image import convert_from_path
from PIL import Image
import pywhatkit as pwk
import time
from dotenv import load_dotenv
import hashlib

# Load environment variables from .env file
load_dotenv()

# Function to hash passwords for secure comparison
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Function to validate admin credentials
def validate_admin(email, password):
    load_dotenv()
    stored_email = os.getenv('AdminEmail')
    stored_password = os.getenv('password')
    print('this is', email)
    print('this is', password)
    print(stored_email, stored_password)
    # Hash the provided password and compare with the stored hash
    return email.strip() == stored_email and password.strip() == stored_password

class PDF(FPDF):
    def header(self):
        self.image('123412.png', 10, 8, 190)
        self.ln(30)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, 'Page %s' % self.page_no(), 0, 0, 'C')

def send_whatsapp_message(phone_number, image_paths, student_name):
    message = f"Dear Sir/Madam, please find your Ward's First internal marks report attached."

    for image_path in image_paths:
        if not os.path.exists(image_path):
            print(f"Image file does not exist: {image_path}")
            continue

        try:
            img = Image.open(image_path)
            img.verify()
            print(f"Image {image_path} is valid.")
        except (IOError, SyntaxError) as e:
            print(f"Image {image_path} is invalid or corrupted: {e}")
            continue

        try:
            print(f"Sending image to {phone_number}.")
            pwk.sendwhats_image(phone_number, image_path, caption=message)
            print(f"WhatsApp message sent to {phone_number} with image {image_path}.")
        except Exception as e:
            print(f"Failed to send WhatsApp message to {phone_number} with image {image_path}: {e}")

        time.sleep(5)

def process_csv_to_pdf(df, year: str):
    pdf_directory = "pdf-file"
    if not os.path.exists(pdf_directory):
        os.makedirs(pdf_directory)

    for index, row in df.iterrows():
        pdf = PDF()
        pdf.add_page()
        pdf.ln(5)

        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, "Dear Sir/Madam,\n"
                               "The academic performance of your ward in the First Internal Assessment test "
                               "held during the period between 22.08.2024 and 30.08.2024 is given below.")
        pdf.ln(5)

        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(0, 10, f"Student Name: {row['Name']}", ln=True, align='C')
        pdf.cell(0, 10, f"College Registration Number: {row['College Registration Number']}", ln=True, align='C')
        pdf.ln(5)

        table_width = 190
        col_widths = [30, 80, 40, 30]  # Adjusted width for Marks Obtained

        pdf.set_font("Arial", style='B', size=12)
        pdf.set_x((210 - table_width) / 2)

        headers = ["Subject Code", "Subject Name", "Max Marks", "Marks Obtained"]
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 10, header, border=1, align='C')
        pdf.ln()

        pdf.set_font("Arial", size=12)
        pdf.set_x((210 - table_width) / 2)

        subjects = []
        if year == "2":
            subjects = [
                ("22GE302", "Universal Human Values II", row['22GE302']),
                ("22MA301", "Discrete Mathematics", row['22MA301']),
                ("22CS305", "Advanced Java Programming", row['22CS305']),
                ("22CS306", "Design and Analysis of Algorithms", row['22CS306']),
                ("22AI301", "Artificial Intelligence", row['22AI301']),
                ("22AI302", "Data Science using Python", row['22AI302'])
            ]
        elif year == "3":
            subjects = [
                ("22CS006", "Introduction to Computer Networks", row['22CS006']),
                ("22CS911", "Data Engineering in Cloud", row['22CS911']),
                ("22AI912", "Multi-core architecture and programming", row['22AI912']),
                ("22AI501", "Deep Learning", row['22AI501']),
                ("22AI502", "Data Exploration and Visualization", row['22AI502']),
            ]
        elif year == "4":
            subjects = [
                ("21AI701", "Deep Learning Techniques", row['21AI701']),
                ("21AI702", "Natural Language Processing", row['21AI702']),
                ("21CS905", "Computer Vision", row['21CS905']),
                ("21ME002", "Design Thinking", row['21ME002']),
                ("21AI923", "Distributed and Cloud Computing", row['21AI923'])
            ]

        for code, name, marks in subjects:
            marks = str(marks) if pd.notna(marks) else "N/A"  # Safely convert marks
            pdf.cell(col_widths[0], 10, code, border=1, align='C')
            pdf.cell(col_widths[1], 10, name, border=1, align='C')
            pdf.cell(col_widths[2], 10, "100", border=1, align='C')  # Max marks
            pdf.cell(col_widths[3], 10, marks, border=1, align='C')  # Marks obtained
            pdf.ln()

        pdf.ln(5)
        pdf.cell(0, 10, f"Percentage: {row['Percentage']}%", ln=True, align='C')
        pdf.ln(5)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 8, "Please note that a minimum of 80% attendance is necessary for a student to be permitted "
                               "to appear for the University Examination.\n\n"
                               "Date:                                                         PRINCIPAL")

        pdf_filename = os.path.join(pdf_directory, f"{row['College Registration Number']}.pdf")
        pdf.output(pdf_filename)

        images = convert_from_path(pdf_filename)
        image_paths = []
        for i, image in enumerate(images):
            image_path = os.path.join(pdf_directory, f"{row['College Registration Number']}_page_{i+1}.png")
            image.save(image_path, 'PNG')
            image_paths.append(image_path)

        phone_number = "+91" + str(row['Phone Number'])

        print(f"Waiting for WhatsApp to stabilize for the first message to {phone_number}")
        time.sleep(2)

        send_whatsapp_message(phone_number, image_paths, row['Name'])

        print(f"WhatsApp message sent to {row['Name']} at {phone_number}.")

def main():
    # Initialize session state for login
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    # Step 1: Admin Login (only show if not logged in)
    if not st.session_state.logged_in:
        st.title("Admin Login")

        email = st.text_input("Admin Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if validate_admin(email, password):
                st.success("Login successful!")
                st.session_state.logged_in = True  # Set login state to True
            else:
                st.error("Invalid email or password. Please try again.")

    # Step 2: Display main content only after login
    if st.session_state.logged_in:
        st.title("Student Report Generator and WhatsApp Messenger")

        # Year selection
        year = st.selectbox("Select Year", ["2", "3", "4"])

        # File upload
        uploaded_file = st.file_uploader("Upload CSV file", type="csv")

        if uploaded_file:
            # Process the uploaded CSV
            df = pd.read_csv(uploaded_file)

            # Display the CSV file contents in Streamlit for verification
            st.dataframe(df)

            if st.button("Generate PDF and Send WhatsApp"):
                with st.spinner("Processing..."):
                    process_csv_to_pdf(df, year)
                st.success("PDF generated and WhatsApp messages sent successfully!")

if __name__ == "__main__":
    main()
