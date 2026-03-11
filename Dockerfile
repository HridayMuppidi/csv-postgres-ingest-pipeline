#slim translates to any 3.13 version like 3.13.7 or something
FROM python:3.13-slim

#docker creates an app directory which contains all our files when it runs our image. 
WORKDIR /app 

#copy the requirements.txt to the current folder. in our case app directory
COPY requirements.txt .

#install all the required dependencies from the requirements.txt file
RUN pip install -r requirements.txt

#copy all project files into container
COPY . .

#Run the app
CMD ["python","src/loader.py"]




