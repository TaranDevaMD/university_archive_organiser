# university_archive_organiser

2 clear roles : admin role and faculty role


Core Document Processing & Automation

   Web-Based Document Upload Portal: A clean, responsive Bootstrap interface allowing  faculty to securely upload academic question papers (PDF or DOCX format) directly from their browser.

    Automated Metadata Parsing Engine: Uses Python libraries (pypdf and Regular Expressions) to automatically scan the header of uploaded documents and extract key information like Course Codes (e.g., CS101), Academic Years, and Exam Types (Midterm/Final) or renames file based on input data such as course code academic year etc asked directly to the user 

    Standardized File Renaming: Automatically converts messy or poorly named files into a strict, uniform naming convention (CourseCode_Year_ExamType.pdf) to maintain clean records.

    Cloud Integration & Smart Routing: Automatically authenticates with the one Drive API and routes newly processed files directly into their respective departmental subject folders.
    
    
    
    
Faculty Search & Retrieval

    Local Search Indexing (SQLite): Stores metadata locally as files are processed, allowing for fast queries without hitting cloud API limits.

    Instant Filtering & Keyword Search: Allows students to search by course code, keyword, or filter by year and exam type to find study materials in seconds.

    One-Click Secure Downloads: Provides direct download and view links so students can access papers instantly without dealing with folder permission hassles.


Admin role :

     sets up academic years new semesters or midfy existing one and automatic sub folders based on that ; edits existing folders ; assigns faculty to particular subjects ;       faculty can edit or upload  iles regarding the subject they are given access to by the admin ;

     further features available to faculty applies to an admin as well 




Advanced Features (For Extended Scope / Future Phases)

    Role-Based Access Control (RBAC): Separates permissions so students can view/download, while faculty can verify and upload materials.

    Duplicate Detection: Prevents clutter by using file hashing (MD5/SHA256) to block identical question papers from being uploaded twice.

    Full-Text In-Document Search: Indexes the full text of PDFs into the local database so students can search for specific topics or questions across all past papers.

    Download Analytics & Trending Papers: Highlights the most downloaded or viewed past papers on the dashboard to help students prioritize their revision.
