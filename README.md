Student Management

1. Online website:

How to use?

Type "https://studentmanagement-351d129b0382.herokuapp.com/" in your browser.
To test all implemented endpoints use "https://studentmanagement-351d129b0382.herokuapp.com/docs".
Website is using public database, so I've seeded it already. I've added 4 students to database and one pdf file (to student with id 39), but remember that it can change becouse website is public and everybody can edit published data.
To use implemented enpoints you have to login by using: login: "admin", password:"admin"


2. Server on local host:

How to install?

Download release of this GitHub repository, unpack it and then create docker image of it, by opening directory of repoitory using terminal and execute command: "docker build -t student-management ."

How to run instaled app?

Before running created docker image make sure that your mysql server is running.
Important: before turning on the application for the first time you have to create db in MySQL. To do so you have to log to MySQL and run command: "CREATE SCHEMA studentManagement;".
You don't have to create any tables, the app will do this automaticly.

To run aplication you have to open Terminal and type:

docker run -e DB_USERNAME=root -e DB_HOST=host.docker.internal -e MAX_PDF_SIZE_MB=5 -e DB_PASSWORD='' -e DB_PORT=3306 -e DB_NAME=StudentManagement -e SEED=1 -p 8000:8000  student-management:latest

in the above line you need to change the environment variables so that they match your data.
DB_USERNAME - your username on MySQL.
DB_HOST - by default on docker it's host.docker.internal, but if you have changed it, type your host name there.
MAX_PDF_SIZE_MB=5 - there you can choose max size of pdf file.
DB_PASSWORD - your password to MySQL.
DB_PORT - Port on which MySQL is running (By deafult it is 3306).
DB_NAME - name of database (if you created database using "CREATE SCHEMA studentManagement;" it would be StudentManagement).
SEED - 1 if you want to fill the tables of database or 0 if you dont want to do that.

You can also choose not to provide individual variables and then app will run with default values of those variables which are:
DB_USERNAME - root,
DB_HOST - host.docker.internal,
MAX_PDF_SIZE_MB=5,
DB_PASSWORD - '' (no password),
DB_PORT - 3306,
DB_NAME - StudentManagement,
SEED - 0.

How to use app?


open your browser and type localhost:8000


Implemented endpoints:

@app.get /users/me - use it to log in.

@app.get / - home page.

@app.get /students/ - use it to show all students from database.

@app.post /students/ - use it to create new student.

@app.put /students/update/{student_id} - use it to update data of student indicated by id.

@app.delete /students/del/{student_id} - use it to delete student indicated by id.

@app.post /students/{student_id}/upload-pdf/ - use it to upload pdf file to student indicated by id.

@app.get /get_pdf/{student_id}/{filename} - use it to downaload pdf file indicated by student_id and filename.

@app.delete /delete_pdf/ - use it to delete pdf file indicated by student_id and filename.


to test all of endpoint metioned above use: localhost:8000/docs


to use any endpoinmt other than root (/) you have to log in.
You can do so by running "@app.get /users/me" or by trying to use any of endpoints. To log in you have to use login:"admin" and password:"admin".

Files uploaded by using "@app.post /students/{student_id}/upload-pdf/" will be stored in folder "uploads" which is inside project folder.
Using endpoint: "@app.delete /delete_pdf/" will remove record of file from database but also will delete indicated file from uploads folder.


