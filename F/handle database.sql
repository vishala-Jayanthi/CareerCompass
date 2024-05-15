-- Create the  database named "F"
CREATE DATABASE F;


-- Switch to 'F' database; 
USE F; 


-- Create 'users' table with id, username,email, password columns. 
CREATE TABLE users (
  id INT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL,
  password VARCHAR(255) NOT NULL
); 

CREATE TABLE student_performance (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  hours_studied INT NOT NULL,
  previous_scores INT NOT NULL,
  extracurricular_activities VARCHAR(3) NOT NULL,
  sleep_hours INT NOT NULL,
  sample_question_papers_practiced INT NOT NULL,
  performance_category VARCHAR(50) NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id)
);



