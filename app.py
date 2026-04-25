import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from config import get_db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
import json

app = Flask(__name__)
app.secret_key = 'organlink_secret_2024'


if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


# ==================== HELPER FUNCTIONS ====================
def add_log(user_id, target_table, action):
    db = get_db()
    if db:
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO logs (user_id, target_table, action) VALUES (%s, %s, %s)",
            (user_id, target_table, action)
        )
        db.commit()
        cursor.close()
        db.close()

def get_compatible_organs(patient_bloodgroup, patient_organ_needed):
    """Find compatible organs based on blood group compatibility"""
    compatibility = {
        'O-': ['O-'],
        'O+': ['O+', 'O-'],
        'A-': ['A-', 'O-'],
        'A+': ['A+', 'A-', 'O+', 'O-'],
        'B-': ['B-', 'O-'],
        'B+': ['B+', 'B-', 'O+', 'O-'],
        'AB-': ['AB-', 'A-', 'B-', 'O-'],
        'AB+': ['AB+', 'AB-', 'A+', 'A-', 'B+', 'B-', 'O+', 'O-']
    }
    
    compatible_groups = compatibility.get(patient_bloodgroup, [])
    if not compatible_groups:
        return []
    
    db = get_db()
    if not db:
        return []
    
    cursor = db.cursor(dictionary=True)
    placeholders = ','.join(['%s'] * len(compatible_groups))
    
    query = f"""
        SELECT do.*, d.bloodgroup as donor_bloodgroup, d.health_status,
               u.name as donor_name
        FROM donor_organs do
        JOIN donors d ON do.donor_id = d.donor_id
        JOIN users u ON d.user_id = u.user_id
        WHERE do.organ_type = %s 
        AND do.status = 'available'
        AND d.health_status = 'healthy'
        AND d.bloodgroup IN ({placeholders})
        ORDER BY do.added_on ASC
    """
    
    params = [patient_organ_needed] + compatible_groups
    cursor.execute(query, params)
    organs = cursor.fetchall()
    cursor.close()
    db.close()
    
    return organs

# ==================== PUBLIC ROUTES ====================
@app.route('/')
def home():
    db = get_db()
    if not db:
        return render_template('home.html', waiting_patients=0, total_donors=0, successful_matches=0, available_organs=0)
    
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("SELECT COUNT(*) as count FROM patients WHERE status = 'waiting'")
    waiting_patients = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM donors")
    total_donors = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM matches WHERE status = 'approved'")
    successful_matches = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM donor_organs WHERE status = 'available'")
    available_organs = cursor.fetchone()['count']
    
    cursor.close()
    db.close()
    
    return render_template('home.html', 
                         waiting_patients=waiting_patients,
                         total_donors=total_donors,
                         successful_matches=successful_matches,
                         available_organs=available_organs)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        db = get_db()
        if not db:
            flash("Database connection error", "error")
            return render_template('login.html')
        
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        db.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['user_id']
            session['user_name'] = user['name']
            session['role'] = user['role']
            
            add_log(user['user_id'], 'users', f"User {user['name']} logged in")
            
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'hospital':
                return redirect(url_for('hospital_dashboard'))
            elif user['role'] == 'patient':
                return redirect(url_for('patient_dashboard'))
            elif user['role'] == 'donor':
                return redirect(url_for('donor_dashboard'))
        else:
            flash("Invalid email or password", "error")
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form['role']
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        
        db = get_db()
        if not db:
            flash("Database error", "error")
            return render_template('register.html')
        
        cursor = db.cursor(dictionary=True)
        
        try:
            # Check if email exists
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                flash("Email already registered", "error")
                return render_template('register.html')
            
            # Insert user
            cursor.execute(
                "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
                (name, email, password, role)
            )
            db.commit()
            user_id = cursor.lastrowid
            
            if role == 'donor':
                bloodgroup = request.form['bloodgroup']
                organ_donated = request.form['organ_donated']
                
                cursor.execute(
                    "INSERT INTO donors (user_id, bloodgroup, organ_donated, health_status, available) VALUES (%s, %s, %s, %s, %s)",
                    (user_id, bloodgroup, organ_donated, 'under_review', True)
                )
                db.commit()
                donor_id = cursor.lastrowid
                
                cursor.execute(
                    "INSERT INTO donor_organs (donor_id, organ_type, bloodgroup, status) VALUES (%s, %s, %s, %s)",
                    (donor_id, organ_donated, bloodgroup, 'available')
                )
                db.commit()
                
                flash("Donor registered! Waiting for hospital verification.", "success")
                
            elif role == 'hospital':
                hospital_name = request.form['hospital_name']
                address = request.form['address']
                contact = request.form['contact']
                
                cursor.execute(
                    "INSERT INTO hospitals (user_id, name, address, contact, approved) VALUES (%s, %s, %s, %s, %s)",
                    (user_id, hospital_name, address, contact, False)
                )
                db.commit()
                flash("Hospital registered! Waiting for admin approval.", "success")
                
            elif role == 'admin':
                admin_secret = request.form.get('admin_secret', '')
                if admin_secret == 'OrganLink2024':
                    flash("Admin registered successfully!", "success")
                else:
                    cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
                    db.commit()
                    flash("Invalid admin secret code!", "error")
                    return render_template('register.html')
            
            cursor.close()
            db.close()
            return redirect(url_for('login'))
            
        except Exception as e:
            db.rollback()
            flash(f"Registration error: {str(e)}", "error")
            cursor.close()
            db.close()
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    if 'user_id' in session:
        add_log(session['user_id'], 'users', "Logged out")
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for('home'))

# ==================== ADMIN ROUTES ====================
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        flash("Unauthorized access", "error")
        return redirect(url_for('login'))
    
    db = get_db()
    if not db:
        flash("Database error", "error")
        return render_template('admin/dashboard.html', 
                             pending_hospitals=[], 
                             all_hospitals=[],
                             all_patients=[],
                             all_donors=[],
                             total_patients=0, 
                             total_donors=0,
                             total_matches=0,
                             available_organs=0)
    
    cursor = db.cursor(dictionary=True)
    
    # Pending hospitals
    cursor.execute("SELECT * FROM hospitals WHERE approved = FALSE")
    pending_hospitals = cursor.fetchall()
    
    # ALL hospitals (for hospitals table)
    cursor.execute("SELECT * FROM hospitals ORDER BY approved DESC, name ASC")
    all_hospitals = cursor.fetchall()
    
    # ALL patients with details (for patients table)
    cursor.execute("""
        SELECT p.*, u.name, h.name as hospital_name 
        FROM patients p
        JOIN users u ON p.user_id = u.user_id
        JOIN hospitals h ON p.hospital_id = h.hospital_id
        ORDER BY p.waiting_since DESC
    """)
    all_patients = cursor.fetchall()
    
    # ALL donors with details (for donors table)
    cursor.execute("""
        SELECT d.*, u.name, h.name as hospital_name 
        FROM donors d
        JOIN users u ON d.user_id = u.user_id
        LEFT JOIN hospitals h ON d.hospital_id = h.hospital_id
        ORDER BY d.donor_id DESC
    """)
    all_donors = cursor.fetchall()
    
    # Statistics
    cursor.execute("SELECT COUNT(*) as count FROM patients")
    total_patients = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM donors")
    total_donors = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM matches WHERE status = 'approved'")
    total_matches = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM donor_organs WHERE status = 'available'")
    available_organs = cursor.fetchone()['count']
    
    cursor.close()
    db.close()
    
    return render_template('admin/dashboard.html', 
                         pending_hospitals=pending_hospitals,
                         all_hospitals=all_hospitals,
                         all_patients=all_patients,
                         all_donors=all_donors,
                         total_patients=total_patients,
                         total_donors=total_donors,
                         total_matches=total_matches,
                         available_organs=available_organs)

@app.route('/admin/approve_hospital/<int:hospital_id>')
def approve_hospital(hospital_id):
    if 'user_id' not in session or session['role'] != 'admin':
        flash("Unauthorized access", "error")
        return redirect(url_for('login'))
    
    db = get_db()
    if db:
        cursor = db.cursor()
        cursor.execute("UPDATE hospitals SET approved = TRUE WHERE hospital_id = %s", (hospital_id,))
        db.commit()
        add_log(session['user_id'], 'hospitals', f"Approved hospital {hospital_id}")
        cursor.close()
        db.close()
        flash("Hospital approved successfully!", "success")
    
    return redirect(url_for('admin_dashboard'))

# Keep these for backward compatibility (if needed)
@app.route('/admin/all_patients')
def admin_all_patients():
    if 'user_id' not in session or session['role'] != 'admin':
        flash("Unauthorized access", "error")
        return redirect(url_for('login'))
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/all_donors')
def admin_all_donors():
    if 'user_id' not in session or session['role'] != 'admin':
        flash("Unauthorized access", "error")
        return redirect(url_for('login'))
    return redirect(url_for('admin_dashboard'))

# ==================== HOSPITAL ROUTES ====================
@app.route('/hospital/dashboard')
def hospital_dashboard():
    if 'user_id' not in session or session['role'] != 'hospital':
        flash("Unauthorized access", "error")
        return redirect(url_for('login'))
    
    db = get_db()
    if not db:
        return render_template('hospital/dashboard.html', 
                             hospital=None, 
                             total_patients=0, 
                             total_donors=0,
                             urgent_patients=0,
                             all_patients=[],
                             all_donors=[],
                             waiting_patients=[])
    
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM hospitals WHERE user_id = %s", (session['user_id'],))
    hospital = cursor.fetchone()
    
    if not hospital or not hospital['approved']:
        flash("Hospital not approved yet", "error")
        return redirect(url_for('logout'))
    
    session['hospital_id'] = hospital['hospital_id']
    
    # Statistics
    cursor.execute("SELECT COUNT(*) as count FROM patients WHERE hospital_id = %s", (hospital['hospital_id'],))
    total_patients = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM donors WHERE hospital_id = %s", (hospital['hospital_id'],))
    total_donors = cursor.fetchone()['count']
    
    cursor.execute("""
        SELECT COUNT(*) as count FROM patients 
        WHERE hospital_id = %s AND urgency IN ('critical', 'high') AND status = 'waiting'
    """, (hospital['hospital_id'],))
    urgent_patients = cursor.fetchone()['count']
    
    # All patients for this hospital (for patients list table)
    cursor.execute("""
        SELECT p.*, u.name 
        FROM patients p
        JOIN users u ON p.user_id = u.user_id
        WHERE p.hospital_id = %s
        ORDER BY 
            CASE p.urgency
                WHEN 'critical' THEN 1
                WHEN 'high' THEN 2
                WHEN 'medium' THEN 3
                WHEN 'low' THEN 4
            END,
            p.waiting_since ASC
    """, (hospital['hospital_id'],))
    all_patients = cursor.fetchall()
    
    # All donors for this hospital (for donors list table)
    cursor.execute("""
        SELECT d.*, u.name 
        FROM donors d
        JOIN users u ON d.user_id = u.user_id
        WHERE d.hospital_id = %s
        ORDER BY d.donor_id DESC
    """, (hospital['hospital_id'],))
    all_donors = cursor.fetchall()
    
    # Waiting patients for matching section
    cursor.execute("""
        SELECT p.*, u.name 
        FROM patients p
        JOIN users u ON p.user_id = u.user_id
        WHERE p.hospital_id = %s AND p.status = 'waiting'
        ORDER BY 
            CASE p.urgency
                WHEN 'critical' THEN 1
                WHEN 'high' THEN 2
                WHEN 'medium' THEN 3
                WHEN 'low' THEN 4
            END,
            p.waiting_since ASC
    """, (hospital['hospital_id'],))
    waiting_patients = cursor.fetchall()
    
    cursor.close()
    db.close()
    
    return render_template('hospital/dashboard.html', 
                         hospital=hospital,
                         total_patients=total_patients,
                         total_donors=total_donors,
                         urgent_patients=urgent_patients,
                         all_patients=all_patients,
                         all_donors=all_donors,
                         waiting_patients=waiting_patients)

@app.route('/hospital/add_patient', methods=['GET', 'POST'])
def add_patient():
    if 'user_id' not in session or session['role'] != 'hospital':
        flash("Unauthorized access", "error")
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        bloodgroup = request.form['bloodgroup']
        organ_needed = request.form['organ_needed']
        urgency = request.form['urgency']
        
        db = get_db()
        if not db:
            flash("Database error", "error")
            return redirect(url_for('hospital_dashboard'))
        
        cursor = db.cursor(dictionary=True)
        
        try:
            # Check if email exists
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                flash("Email already registered!", "error")
                return redirect(url_for('hospital_dashboard'))
            
            cursor.execute(
                "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
                (name, email, password, 'patient')
            )
            db.commit()
            user_id = cursor.lastrowid
            
            cursor.execute("""
                INSERT INTO patients (user_id, hospital_id, bloodgroup, organ_needed, urgency, waiting_since, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (user_id, session['hospital_id'], bloodgroup, organ_needed, urgency, date.today(), 'waiting'))
            db.commit()
            
            add_log(session['user_id'], 'patients', f"Added patient {name}")
            flash(f"Patient {name} registered successfully!", "success")
            cursor.close()
            db.close()
            return redirect(url_for('hospital_dashboard'))
            
        except Exception as e:
            db.rollback()
            flash(f"Error: {str(e)}", "error")
            cursor.close()
            db.close()
    
    return redirect(url_for('hospital_dashboard'))

@app.route('/hospital/add_donor', methods=['POST'])
def add_donor():
    if 'user_id' not in session or session['role'] != 'hospital':
        flash("Unauthorized access", "error")
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        bloodgroup = request.form['bloodgroup']
        organs = request.form.getlist('organs[]')
        
        if not organs:
            flash("Please select at least one organ", "error")
            return redirect(url_for('hospital_dashboard'))
        
        db = get_db()
        if not db:
            flash("Database error", "error")
            return redirect(url_for('hospital_dashboard'))
        
        cursor = db.cursor(dictionary=True)
        
        try:
            # Check if email exists
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                flash("Email already registered!", "error")
                return redirect(url_for('hospital_dashboard'))
            
            cursor.execute(
                "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
                (name, email, password, 'donor')
            )
            db.commit()
            user_id = cursor.lastrowid
            
            cursor.execute("""
                INSERT INTO donors (user_id, bloodgroup, organ_donated, health_status, available, hospital_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, bloodgroup, organs[0] if organs else 'Unknown', 'healthy', True, session['hospital_id']))
            db.commit()
            donor_id = cursor.lastrowid
            
            for organ in organs:
                cursor.execute("""
                    INSERT INTO donor_organs (donor_id, organ_type, bloodgroup, status)
                    VALUES (%s, %s, %s, %s)
                """, (donor_id, organ, bloodgroup, 'available'))
            db.commit()
            
            add_log(session['user_id'], 'donors', f"Added donor {name}")
            flash(f"Donor {name} registered with {len(organs)} organ(s)!", "success")
            cursor.close()
            db.close()
            return redirect(url_for('hospital_dashboard'))
            
        except Exception as e:
            db.rollback()
            flash(f"Error: {str(e)}", "error")
            cursor.close()
            db.close()
    
    return redirect(url_for('hospital_dashboard'))

@app.route('/hospital/find_match/<int:patient_id>')
def find_match(patient_id):
    if 'user_id' not in session or session['role'] != 'hospital':
        flash("Unauthorized access", "error")
        return redirect(url_for('login'))
    
    db = get_db()
    if not db:
        flash("Database error", "error")
        return redirect(url_for('hospital_dashboard'))
    
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.*, u.name 
        FROM patients p
        JOIN users u ON p.user_id = u.user_id
        WHERE p.patient_id = %s AND p.hospital_id = %s
    """, (patient_id, session['hospital_id']))
    patient = cursor.fetchone()
    cursor.close()
    db.close()
    
    if not patient:
        flash("Patient not found", "error")
        return redirect(url_for('hospital_dashboard'))
    
    organs = get_compatible_organs(patient['bloodgroup'], patient['organ_needed'])
    
    return render_template('hospital/available_matches.html', patient=patient, organs=organs)

@app.route('/hospital/assign_organ', methods=['POST'])
def assign_organ():
    if 'user_id' not in session or session['role'] != 'hospital':
        flash("Unauthorized access", "error")
        return redirect(url_for('login'))
    
    organ_id = request.form['organ_id']
    patient_id = request.form['patient_id']
    
    db = get_db()
    if not db:
        flash("Database error", "error")
        return redirect(url_for('hospital_dashboard'))
    
    cursor = db.cursor(dictionary=True)
    
    try:
        db.start_transaction()
        
        # Lock the organ for update to prevent double booking
        cursor.execute("SELECT * FROM donor_organs WHERE organ_id = %s AND status = 'available' FOR UPDATE", (organ_id,))
        organ = cursor.fetchone()
        
        if not organ:
            flash("Organ no longer available!", "error")
            db.rollback()
            return redirect(url_for('hospital_dashboard'))
        
        # Update organ status
        cursor.execute("UPDATE donor_organs SET status = 'matched' WHERE organ_id = %s", (organ_id,))
        
        # Update patient status
        cursor.execute("UPDATE patients SET status = 'matched' WHERE patient_id = %s", (patient_id,))
        
        # Create match record
        cursor.execute("""
            INSERT INTO matches (patient_id, donor_id, organ_id, matched_by, status, match_date)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """, (patient_id, organ['donor_id'], organ_id, session['user_id'], 'approved'))
        
        db.commit()
        add_log(session['user_id'], 'matches', f"Assigned organ {organ_id} to patient {patient_id}")
        flash("Organ assigned successfully! Patient has been matched.", "success")
        
    except Exception as e:
        db.rollback()
        flash(f"Error assigning organ: {str(e)}", "error")
    
    cursor.close()
    db.close()
    
    return redirect(url_for('hospital_dashboard'))

# ==================== PATIENT ROUTES ====================
@app.route('/patient/dashboard')
def patient_dashboard():
    if 'user_id' not in session or session['role'] != 'patient':
        flash("Unauthorized access", "error")
        return redirect(url_for('login'))
    
    db = get_db()
    if not db:
        return render_template('patient/dashboard.html', patient=None)
    
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.*, h.name as hospital_name, u.name as patient_name
        FROM patients p
        JOIN hospitals h ON p.hospital_id = h.hospital_id
        JOIN users u ON p.user_id = u.user_id
        WHERE p.user_id = %s
    """, (session['user_id'],))
    patient = cursor.fetchone()
    
    if patient:
        # Calculate waitlist position
        if patient['status'] == 'waiting':
            cursor.execute("""
                SELECT COUNT(*) + 1 as position FROM patients 
                WHERE organ_needed = %s 
                AND status = 'waiting' 
                AND (
                    CASE urgency
                        WHEN 'critical' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'medium' THEN 3
                        WHEN 'low' THEN 4
                    END
                ) < (
                    CASE %s
                        WHEN 'critical' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'medium' THEN 3
                        WHEN 'low' THEN 4
                    END
                )
                OR (
                    urgency = %s AND waiting_since < %s
                )
            """, (patient['organ_needed'], patient['urgency'], patient['urgency'], patient['waiting_since']))
            position_result = cursor.fetchone()
            patient['waitlist_position'] = position_result['position'] if position_result else 1
        else:
            patient['waitlist_position'] = None
        
        # Get match info if matched
        if patient['status'] == 'matched':
            cursor.execute("""
                SELECT m.*, do.organ_type, u.name as donor_name
                FROM matches m
                JOIN donor_organs do ON m.organ_id = do.organ_id
                JOIN donors d ON m.donor_id = d.donor_id
                JOIN users u ON d.user_id = u.user_id
                WHERE m.patient_id = %s AND m.status = 'approved'
                ORDER BY m.match_date DESC LIMIT 1
            """, (patient['patient_id'],))
            patient['match_info'] = cursor.fetchone()
    
    cursor.close()
    db.close()
    
    return render_template('patient/dashboard.html', patient=patient)

# ==================== DONOR ROUTES ====================
@app.route('/donor/dashboard')
def donor_dashboard():
    if 'user_id' not in session or session['role'] != 'donor':
        flash("Unauthorized access", "error")
        return redirect(url_for('login'))
    
    db = get_db()
    if not db:
        return render_template('donor/dashboard.html', donor=None, organs=[], matches=[])
    
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT d.*, h.name as hospital_name
        FROM donors d
        LEFT JOIN hospitals h ON d.hospital_id = h.hospital_id
        WHERE d.user_id = %s
    """, (session['user_id'],))
    donor = cursor.fetchone()
    
    if donor:
        cursor.execute("SELECT * FROM donor_organs WHERE donor_id = %s ORDER BY added_on DESC", (donor['donor_id'],))
        organs = cursor.fetchall()
        
        cursor.execute("""
            SELECT m.*, do.organ_type, p.organ_needed, u.name as patient_name
            FROM matches m
            JOIN donor_organs do ON m.organ_id = do.organ_id
            JOIN patients p ON m.patient_id = p.patient_id
            JOIN users u ON p.user_id = u.user_id
            WHERE m.donor_id = %s AND m.status = 'approved'
        """, (donor['donor_id'],))
        matches = cursor.fetchall()
    else:
        organs = []
        matches = []
    
    cursor.close()
    db.close()
    
    return render_template('donor/dashboard.html', donor=donor, organs=organs, matches=matches)

# if __name__ == '__main__':
#     app.run(debug=True)