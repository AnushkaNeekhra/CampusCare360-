Smart Campus - Project Development Log 
Project Overview 
Project Name:CampusCare360
Technology Stack:Python,Flask,SQLite,HTML,CSS
Purpose: To provide students with a platform to submit complaints , track their status and share feedback.
Development Progress 
Phase 1 - Project Setup and initial Development 
- Created the project structure.
- Set up the Python environment and installed Flask.
-  Developed the complaint submission feature.
- Implemented complaint tracking using ticket IDs.
- Created the admin login and dashboard.
- Implemented complaint status updates.
- Added student feedback functionality.
- Tested the complete complaint workflow.
Phase 2 – Interface and Design Improvements
- Updated the website colour palette.
- Planned improvements to website navigation.
- Worked on responsive design for mobile devices.
- Planned further improvements to the user interface.
Work Session Records
Date| Time Spent| Work Completed
07 November 2026| 6 hours| GitHub repository setup and project made and upload
  Add date| Add actual hours| Add completed task
  Add date| Add actual hours| Add completed improvement
Future Improvements
- Improve mobile responsiveness.
- Enhance the admin dashboard.
- Improve navigation and user experience.
- Add more student assistance features.
- Perform further testing and bug fixes.
Note
This log records genuine development activities and working time. It will be updated as the project progresses.
## Latest Development Update – Website Design Improvements

### Completed Work
- Improved the website colour theme with a professional blue design.
- Enhanced the navigation bar and hover effects.
- Improved button styling and animations.
- Redesigned cards, panels and form input fields.
- Added visual focus effects to form fields.
- Introduced colour-coded complaint status badges:
  - Pending – Yellow
  - In Progress – Blue
  - Resolved – Green
- Updated `static/style.css`.
- Updated `templates/track.html`.
- Tested the updated website successfully in the browser.
- Uploaded both updated files to GitHub.

### Future Work
- Improve the admin dashboard design.
- Add more user-friendly features.
- Perform final testing and documentation.
## Feature Update: Website Notification System

- Implemented a student notification system for complaint submission and status updates.
- Added admin notifications for newly submitted complaints.
- Added admin notifications when students submit feedback.
- Implemented the mark-as-read functionality for admin notifications.
- Tested all four notification scenarios successfully.
- Email notifications are not configured yet.

## Feature Update: Complaint Photo Upload

- Added an optional photo upload feature to the complaint submission form.
- Supported JPG, JPEG, and PNG image formats.
- Implemented a maximum upload size of 5 MB.
- Generated unique filenames for uploaded images.
- Added photo display in the Admin Dashboard.
- Allowed complaint submission without an image.
- Added CSS styling for uploaded complaint photos.
- Updated `.gitignore` to exclude uploaded photos.
- Successfully tested complaint submissions with and without photos.
