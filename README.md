# UEP System Module

This project contains several internal UEP functions combined with a user-friendly front-end interface.  
It is designed to provide an intuitive and complete user experience with the following features:

## Features

- **UEP Dialog Animations & Text Output**  
  Interactive dialog animations and dynamic text rendering.

- **Reminder Setting (Set Reminder)**  
  Schedule and manage reminders with ease.

- **Trash Bin Cleaning (Clean Trash Bin)**  
  Quickly clean up and optimize your trash can.

- **Music Control (Media Control)**  
  This feature primarily supports playing multimedia music from platforms such as Spotify and YouTube. In addition to the built-in music controls, it can also be managed through UEP, enabling functions such as play, pause, skip, and search. The system includes a caching mechanism that stores previously played tracks for faster loading, and automatically checks the cache during off-peak hours to update or remove unnecessary data.

- **World Time Query (Get World Time)**  
  Retrieve current time across different time zones.

- **OCR Recognition**  
  Extract and recognize text from images.

- **Translate_export(translate)**
  This feature supports translating PDF, DOCX, and TXT files. The text is split into multiple sentences, and each segment is translated sequentially using googletrans. A retry mechanism is implemented to prevent interruptions in case of API failures. After the translation is completed, the results are saved into a DOCX file and automatically opened for review.

