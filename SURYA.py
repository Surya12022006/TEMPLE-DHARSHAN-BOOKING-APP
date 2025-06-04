import gradio as gr 
import sqlite3 
import datetime 
import pandas as pd
CHAPTER 5 
APPENDIX A SOURCE CODE
# ------------------ SQLite Setup ------------------
conn = sqlite3.connect("temple_darisan.db", check_same_thread=False) 
cursor = conn.cursor()
#.ı Drop tables if they already exist (for dev/testing) 
cursor.execute("DROP TABLE IF EXISTS users") 
cursor.execute("DROP TABLE IF EXISTS bookings")
# Create users table 
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
id INTEGER PRIMARY KEY AUTOINCREMENT,
email TEXT UNIQUE, 
password TEXT, 
full_name TEXT
) 
""")
# Create bookings table 
cursor.execute("""
CREATE TABLE IF NOT EXISTS bookings (
id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER, 
temple_name TEXT, 
darisan_date TEXT, 
time_slot TEXT, 
payment_status TEXT,
FOREIGN KEY(user_id) REFERENCES users(id)
)
""")
conn.commit()
# Track current user session info 
current_user_id = {"id": None} 
current_user_name = {"name": ""}
current_user_booking_id = {"id": None} # Store booking id for cancellation
# ------------------ Backend Functions ------------------
def register_user(name, email, password):
if not name or not email or not password:
return "'.All fields are required." 
try:
cursor.execute("INSERT INTO users (full_name, email, password) 
VALUES (?, ?, ?)",
(name, email, password)) 
conn.commit()
return f"⬛ Registered successfully! Please log in using: {email}" 
except sqlite3.IntegrityError:
return "+ Email already registered. Please log in instead." 
except Exception as e:return f"+ Error: {str(e)}"
def login_user(email, password):
cursor.execute("SELECT * FROM users WHERE email=? AND 
password=?", (email, password))
user = cursor.fetchone() 
if user:
current_user_id["id"] = user[0] 
current_user_name["name"] = user[3]
current_user_booking_id["id"] = None # Reset booking id on new login 
return f"⬛ Welcome, {user[3]}!", user[3]
else:
return "+ Invalid email or password.", ""
def book_darisan(temple, date, slot): 
if not current_user_id["id"]:
return "ı.Please log in first."
# Optional: validate date format and date not in past 
try:
booking_date = datetime.datetime.strptime(date, "%Y-%m-%d").date() 
if booking_date < datetime.date.today():
return "+ Darisan date cannot be in the past." 
except ValueError:
return "+ Date format must be YYYY-MM-DD."
cursor.execute(
"INSERT INTO bookings (user_id, temple_name, darisan_date, time_slot, 
payment_status) VALUES (?, ?, ?, ?, ?)",
(current_user_id["id"], temple, date, slot, "Pending"))conn.commit()
return f"⬛ Booking for {temple} on {date} at {slot} successful! Proceed to 
Payment tab."
def make_payment():
if not current_user_id["id"]: 
return "ı.Login first."
cursor.execute("SELECT * FROM bookings WHERE user_id=? AND
payment_status='Pending'", (current_user_id["id"],)) 
booking = cursor.fetchone()
if booking:
cursor.execute("UPDATE bookings SET payment_status='Paid' WHERE 
id=?", (booking[0],))
conn.commit()
return "⬛ Payment successful!" 
else:
return "+ No pending bookings found."
def get_paid_booking(user_id): 
cursor.execute("""
SELECT b.id, u.full_name, b.temple_name, b.darisan_date, b.time_slot 
FROM bookings b JOIN users u ON b.user_id = u.id
WHERE b.user_id=? AND b.payment_status='Paid'
ORDER BY b.darisan_date DESC LIMIT 1 
""", (user_id,))
booking = cursor.fetchone() 
if booking:
current_user_booking_id["id"] = booking[0] 
return (
"⬛ Booking found below.",booking[1], booking[2], booking[3] + " at " + booking[4], 
gr.update(visible=True)
)
else:
current_user_booking_id["id"] = None
return "+ No paid booking found.", "", "", "", gr.update(visible=False)
def cancel_booking(user_id):
booking_id = current_user_booking_id.get("id") 
if not booking_id:
return ".ı No booking to cancel."
cursor.execute("DELETE FROM bookings WHERE id=? AND user_id=?", 
(booking_id, user_id))
conn.commit()
current_user_booking_id["id"] = None # Reset booking id after cancellation 
return "⬛ Booking cancelled. 80% refund has been initiated."
def view_db():
users_df = pd.read_sql_query("SELECT id, full_name, email FROM users", 
conn)
bookings_df = pd.read_sql_query("""
SELECT b.id, u.full_name, b.temple_name, b.darisan_date, b.time_slot, 
b.payment_status
FROM bookings b JOIN users u ON b.user_id = u.id 
""", conn)
return users_df, bookings_df
# ------------------ Gradio UI ------------------
with gr.Blocks() as app:gr.Markdown("## '.;ç¡ Temple Darisan Booking Software", elem_id="title", 
elem_classes="text-3xl font-bold text-center")
with gr.Tab("w•⬛›Register"): 
gr.Markdown("### Create Your Account") 
reg_name = gr.Textbox(label="Full Name") 
reg_email = gr.Textbox(label="Email")
reg_pass = gr.Textbox(label="Password", type="password") 
reg_btn = gr.Button("Register")
reg_msg = gr.Markdown()
reg_btn.click(fn=register_user, inputs=[reg_name, reg_email, reg_pass], 
outputs=reg_msg)
with gr.Tab("t'çP Login"):
gr.Markdown("### Login to Your Account") 
email = gr.Textbox(label="Email")
password = gr.Textbox(label="Password", type="password") 
login_btn = gr.Button("Login")
login_msg = gr.Markdown()
full_name = gr.Textbox(label="Full Name", interactive=False) 
login_btn.click(fn=login_user, inputs=[email, password],
outputs=[login_msg, full_name])
with gr.Tab("ç†,Profile"): 
gr.Markdown("### Your Profile Info")
profile_name = gr.Textbox(label="Full Name", value=lambda: 
current_user_name["name"], interactive=True)
profile_id = gr.Textbox(label="User ID", value=lambda: 
str(current_user_id["id"]), interactive=True)
with gr.Tab("ç·ˆ.Book Darisan"):gr.Markdown("### Select Your Temple and Time Slot") 
temple = gr.Dropdown([
"Tirupati, Chittoor", 
"Palani, Dindigul",
"Rameswaram, Ramanathapuram", 
"Meenakshi Temple, Madurai", 
"Kedarnath Temple,Rudraprayag", 
"Badrinath Temple,Chamoli", 
"Somnath Temple,Gir Somnath",
"Dwarkadhish Temple,Devbhumi Dwarka", 
"Akshardham Temple,New Delhi", 
"Mahakaleshwar Temple,Ujjain", 
"Omkareshwar Temple,Khandwa",
"Kashi Vishwanath Temple,Varanasi", 
"Vaishno Devi Temple,Reasi",
"Shirdi Sai Baba Temple,Ahmednagar", 
"Siddhivinayak Temple,Mumbai", 
"Mahalaxmi Temple,Kolhapur", 
"Trimbakeshwar Temple,Nashik", 
"Bhimashankar Temple,Pune", 
"Grishneshwar Temple,Aurangabad", 
"Aundha Nagnath Temple,Hingoli", 
"Parli Vaijnath Temple,Beed",
"Ram Mandir,Ayodhya", 
"Lingaraja Temple,Bhubaneswar", 
"Jagannath Temple,Puri", 
"Konark Sun Temple,Puri", 
"Kamakhya Temple,Guwahati", 
"Kalighat Kali Temple,Kolkata","Dakshineswar Temple,Kolkata", 
"Belur Math,Howrah",
"Annamalaiyar Temple,Tiruvannamalai", 
"Sabarimala Temple,Pathanamthitta", 
"Guruvayur Temple,Thrissur",
"Padmanabhaswamy Temple,Thiruvananthapuram", 
"Chamundeshwari Temple,Mysuru",
"Hoysaleswara Temple,Hassan", 
"Chennakesava Temple,Hassan", 
"Virupaksha Temple,Ballari", 
"Murudeshwar Temple,Uttara Kannada", 
"Udupi Sri Krishna Temple,Udupi",
"Kukke Subramanya Temple,Dakshina Kannada", 
"Mookambika Temple,Udupi",
"Sringeri Sharada Peetham,Chikkamagaluru", 
"Dharmasthala Temple,Dakshina Kannada", 
"Banashankari Temple,Bagalkot",
"Shani Shingnapur,Ahmednagar", 
"Tulja Bhavani Temple,Osmanabad", 
"Jejuri Khandoba Temple,Pune", 
"Bhuleshwar Temple,Pune", 
"Babulnath Temple,Mumbai", 
"Rajarajeshwara Temple,Kannur", 
"Narasimha Swamy Temple,Nandyal",
"Yadagirigutta Temple,Yadadri Bhuvanagiri", 
"Keesaragutta Temple,Medchal",
"Basara Saraswathi Temple,Nirmal", 
"Chilkur Balaji Temple,Ranga Reddy", 
"Kanaka Durga Temple,Vijayawada","Simhachalam Temple,Visakhapatnam", 
"Annavaram Temple,Kakinada", 
"Srikalahasti Temple,Tirupati", 
"Vontimitta Temple,Kadapa", 
"Kotappakonda Temple,Guntur", 
"Mantralayam Temple,Kurnool",
"Alampur Jogulamba Temple,Jogulamba Gadwal", 
"Bhadrakali Temple,Warangal",
"Medaram Temple,Mulugu", 
"Mallikarjuna Temple,Srisailam", 
"Thanumalayan Temple,Kanyakumari",
"Sri Ranganathaswamy Temple,Tiruchirappalli", 
"Nataraja Temple,Chidambaram", 
"Brihadeeswarar Temple,Thanjavur", 
"Swamimalai Murugan Temple,Thanjavur", 
"Thiruthani Murugan Temple,Tiruvallur", 
"Thiruvarur Temple,Tiruvarur",
"Tenkasi Temple,Tenkasi", 
"Sarangapani Temple,Kumbakonam",
"Vaitheeswaran Temple,Ramanathapuram", 
"Kanchi Kamakshi Temple,Kanchipuram", 
"Kapaleeshwarar Temple,Chennai", 
"Vadapalani Murugan Temple,Chennai", 
"Santhome Basilica,Chennai",
"St. Thomas Mount,Chennai", 
"Velankanni Church,Nagapattinam",
"Our Lady of Good Health Church,Velankanni", 
"Little Flower Church,Trivandrum",
"St. George Forane Church,Angamaly"], label="Select Temple")
darisan_date = gr.Textbox(label="Darisan Date (YYYY-MM-DD)") 
time_slot = gr.Radio(choices=["Morning", "Afternoon", "Evening"],
label="Select Time Slot")
book_btn = gr.Button("Book Darisan") 
book_msg = gr.Markdown()
book_btn.click(fn=book_darisan, inputs=[temple, darisan_date, time_slot], 
outputs=book_msg)
with gr.Tab("-—.Payment"):
gr.Markdown("### Make Payment for Your Booking") 
pay_btn = gr.Button("Pay Now")
pay_msg = gr.Markdown()
pay_btn.click(fn=make_payment, inputs=[], outputs=pay_msg)
with gr.Tab("+ Cancel Booking"):
gr.Markdown("### Cancel Your Paid Booking and Get 80% Refund") 
view_msg = gr.Markdown()
name = gr.Textbox(label="Name", interactive=True) 
temple = gr.Textbox(label="Temple", interactive=True)
slot_time = gr.Textbox(label="Date & Time", interactive=True) 
cancel_btn = gr.Button("Cancel Booking", visible=True) 
cancel_status = gr.Markdown()
# Show current paid booking
view_btn = gr.Button("View My Paid Booking") 
view_btn.click(fn=get_paid_booking, inputs=[gr.State(lambda:
current_user_id["id"])],
outputs=[view_msg, name, temple, slot_time, cancel_btn])cancel_btn.click(fn=cancel_booking, inputs=[gr.State(lambda: 
current_user_id["id"])], outputs=cancel_status)
# Move the Database Info tab inside the gr.Blocks context 
with gr.Tab("¡#ç/ Database Info"):
gr.Markdown("### Admin Access Required to View Database Info")
# Input field and submit button for access code
admin_code = gr.Textbox(label="Enter Admin Access Code", 
type="password")
submit_code_btn = gr.Button("Submit Code") 
access_status = gr.Markdown()
# Secure components (initially hidden)
users_tbl = gr.Dataframe(headers=["ID", "Name", "Email"], visible=False) 
bookings_tbl = gr.Dataframe(headers=["Booking ID", "User Name",
"Temple", "Date", "Time Slot", "Payment Status"], visible=False) 
db_refresh = gr.Button("Refresh Database", visible=False)
code
# Access code check function 
def check_admin_access(code):
if code == "2303811714821044": # <- Change this to your desired secure
return ("⬛ Access granted.", 
gr.update(visible=True), 
gr.update(visible=True), 
gr.update(visible=True))
else:
return ("+ Invalid code. Access denied.",gr.update(visible=False), 
gr.update(visible=False), 
gr.update(visible=False))
# Button click connects the function 
submit_code_btn.click(
fn=check_admin_access, 
inputs=[admin_code],
outputs=[access_status, users_tbl, bookings_tbl, db_refresh]
)
# Refresh click (only works after access)
db_refresh.click(fn=view_db, inputs=[], outputs=[users_tbl, bookings_tbl])
if name == " main ": 
app.launch()
