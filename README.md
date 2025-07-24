This repository contains a simple web-based Data Access Tracker, designed to help administrators monitor and manage access to sensitive data within an organization. It provides a centralized view of who accessed what data, when, and for what purpose.

Features
User Management: Track users who are accessing data.

Data Item Management: Define and categorize different types of data or data sources.

Access Logging: Record details of each data access event, including timestamp, user, data item, and purpose.

Search & Filter: Easily search and filter access logs by user, data item, date range, or purpose.

Reporting: Generate basic reports on data access patterns.

Admin Panel: Dedicated interface for administrators to manage users, data items, and view logs.

Trainee Panel: Interface for trainees to view their assigned courses/assessments and complete them.

Technologies Used
HTML5: For structuring the web pages.

Tailwind CSS: For responsive and utility-first styling.

JavaScript: For interactive elements, form handling, and dynamic content loading (client-side).

Firebase (Firestore & Authentication): (Planned for future integration) For persistent data storage and user authentication.

Project Structure
The project is structured with individual HTML files for different views and a shared JavaScript file for common functionalities.

index.html: (Placeholder/Login page - not explicitly provided in this set)

dashboard.html: General dashboard view.

admin_dashboard.html: Administrator's overview dashboard.

create_course.html: Form to create new courses (admin function).

create_assessment.html: Form to create new assessments (admin function).

assign_items.html: Form to assign courses/assessments to users (admin function).

view_progress.html: View user progress in courses/assessments (admin function).

trainee_assignments.html: Trainee's view of their assigned courses and assessments.

complete_assessment.html: Trainee's interface to complete an assessment.

keyboard_navigation.js: JavaScript for enhanced keyboard accessibility.

Setup and Running
Since this is primarily a front-end application with client-side JavaScript, you can run it directly in your web browser.

Clone the repository (if applicable):

git clone <repository-url>
cd data-access-tracker

(Note: If you received these files directly, you can skip this step.)

Open the HTML files:
Simply open any of the .html files (e.g., admin_dashboard.html, trainee_assignments.html) in your web browser.

For the full experience, ensure all HTML files and the keyboard_navigation.js file are in the same directory or correctly linked relative to each other.

The keyboard_navigation.js file should be linked in each HTML file before the closing </body> tag:

<script src="keyboard_navigation.js"></script>
</body>
</html>

Usage
Administrator Functions:
Admin Dashboard (admin_dashboard.html): Provides an overview of system health, user statistics, and recent system events.

Create Course (create_course.html): Fill out the form to add new courses to the system.

Create Assessment (create_assessment.html): Define new assessments with questions and details.

Assign Items (assign_items.html): Assign created courses or assessments to specific users or groups.

View Progress (view_progress.html): Filter and view the progress of users in their assigned courses and assessments.

Trainee Functions:
My Assignments (trainee_assignments.html): View a list of all assigned courses and assessments with their status and due dates.

Complete Assessment (complete_assessment.html): Access and complete specific assessments.

Keyboard Navigation:
The keyboard_navigation.js script enhances accessibility:

Sidebar:

Alt + S: Toggles the sidebar open/closed.

ArrowUp/ArrowDown: Navigate between links within the open sidebar.

Escape: Closes the sidebar.

User Dropdown:

Alt + U: Toggles the user dropdown open/closed.

Enter/Space (when avatar is focused): Opens the user dropdown.

ArrowUp/ArrowDown: Navigate between links within the open dropdown.

Escape: Closes the dropdown.

Future Enhancements (Potential)
Backend Integration: Implement a backend (e.g., Node.js, Python with Flask/Django) and a database (e.g., PostgreSQL, MongoDB, Firebase Firestore) for persistent data storage and user authentication.

User Authentication: Full user login/logout system with role-based access control.

Dynamic Content: Fetch and display data dynamically from a backend API instead of using dummy data.

Advanced Reporting: More sophisticated data visualization and reporting tools.

Notifications: Implement real-time notifications for assignments, due dates, etc.

Search Functionality: Implement actual search logic for the search bars.
