-- DROP DATABASE IF EXISTS organlink;
-- CREATE DATABASE organlink;
-- USE organlink;

-- Users table
CREATE TABLE users(
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    email VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(30) NOT NULL,
    contact_phone VARCHAR(20),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_role CHECK (role IN ('admin','hospital','patient','donor'))
);

-- Hospitals table
CREATE TABLE hospitals(
    hospital_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(100),
    contact VARCHAR(30),
    approved BOOLEAN DEFAULT FALSE,
    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Patients table
CREATE TABLE patients(
    patient_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    hospital_id INT,
    bloodgroup VARCHAR(5),
    organ_needed VARCHAR(50),
    urgency VARCHAR(10),
    status VARCHAR(30) DEFAULT 'waiting',
    waiting_since DATE NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY(hospital_id) REFERENCES hospitals(hospital_id),
    CONSTRAINT valid_urgency CHECK (urgency IN ('low','medium','high','critical')),
    CONSTRAINT valid_status CHECK (status IN ('waiting','matched','transplanted')),
    CONSTRAINT valid_bg CHECK (bloodgroup IN ('A+','A-','B+','B-','AB+','AB-','O+','O-'))
);

-- Donors table
CREATE TABLE donors(
    donor_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    bloodgroup VARCHAR(5),
    organ_donated VARCHAR(50),
    health_status VARCHAR(30) DEFAULT 'under_review',
    available BOOLEAN DEFAULT TRUE,
    hospital_id INT,
    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY(hospital_id) REFERENCES hospitals(hospital_id),
    CONSTRAINT valid_health CHECK (health_status IN('under_review','healthy','disqualified')),
    CONSTRAINT valid_donor_bg CHECK (bloodgroup IN ('A+','A-','B+','B-','AB+','AB-','O+','O-'))
);

-- Donor organs table (for multiple organs per donor)
CREATE TABLE donor_organs(
    organ_id INT AUTO_INCREMENT PRIMARY KEY,
    donor_id INT NOT NULL,
    organ_type VARCHAR(50) NOT NULL,
    bloodgroup VARCHAR(5) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'available',
    added_on DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_organ_status CHECK (status IN ('available','matched','donated')),
    FOREIGN KEY (donor_id) REFERENCES donors(donor_id) ON DELETE CASCADE
);

-- Organ requests table
CREATE TABLE organ_requests(
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT,
    hospital_id INT,
    organ_needed VARCHAR(50),
    urgency VARCHAR(10),
    status VARCHAR(20) DEFAULT 'pending',
    requested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
    FOREIGN KEY(hospital_id) REFERENCES hospitals(hospital_id),
    CONSTRAINT valid_request_urgency CHECK (urgency IN ('low','medium','high','critical')),
    CONSTRAINT valid_request_status CHECK(status IN('pending','matched','cancelled'))
);

-- Matches table (core transaction table)
CREATE TABLE matches(
    match_id INT AUTO_INCREMENT PRIMARY KEY,
    request_id INT,
    donor_id INT,
    organ_id INT,
    patient_id INT,
    matched_by INT,
    match_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'proposed',
    FOREIGN KEY(request_id) REFERENCES organ_requests(request_id),
    FOREIGN KEY(donor_id) REFERENCES donors(donor_id),
    FOREIGN KEY(organ_id) REFERENCES donor_organs(organ_id),
    FOREIGN KEY(patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY(matched_by) REFERENCES users(user_id),
    CONSTRAINT valid_match_status CHECK (status IN ('proposed', 'approved', 'rejected', 'completed'))
);

-- Logs table for audit
CREATE TABLE logs(
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    target_table VARCHAR(30),
    action VARCHAR(100),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

-- Insert sample admin
INSERT INTO users (name, email, password, role) VALUES 
('System Admin', 'admin@organlink.com', 'scrypt:32768:8:1$HCRgHPLVYB7Y8d6q$0945c92d1abbeac95414e04d43f847250b612b9bfab290d56c5da6e6a00b75a0b7cfb5f4102dadae7c7c78e396d8cdea6c31adaa3c51fec32cf59e7f63915e52', 'admin');

-- Sample hospital
INSERT INTO users (name, email, password, role) VALUES 
('City Hospital', 'hospital@city.com', 'scrypt:32768:8:1$HCRgHPLVYB7Y8d6q$0945c92d1abbeac95414e04d43f847250b612b9bfab290d56c5da6e6a00b75a0b7cfb5f4102dadae7c7c78e396d8cdea6c31adaa3c51fec32cf59e7f63915e52', 'hospital');

INSERT INTO hospitals (user_id, name, address, contact, approved) VALUES 
(2, 'City Hospital', '123 Main St, City', '555-0100', TRUE);

-- Note: Default password for all sample users is "password123"
-- In real use, generate proper password hashes with generate_password_hash()